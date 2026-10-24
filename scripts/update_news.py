#!/usr/bin/env python3
"""Consulta RSS/Atom públicos e publica somente títulos, datas, veículos e links.

Nenhuma notícia recebe classificação automática de falsidade. Sem chave de API.
Falhas de uma fonte preservam os itens anteriores e ficam registradas no painel.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import tempfile
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 3_000_000
MAX_ITEMS = 500
TIMEOUT = 18
HEADERS = {'User-Agent':'ArquivoBolsonaro/2.0 (+https://github.com/QGBALTIGO/Internacional)', 'Accept':'application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9'}

class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]
    def handle_data(self, data):
        self.parts.append(data)

def plain(value):
    parser=PlainText(); parser.feed(unescape(str(value or '')))
    return re.sub(r'\s+', ' ', ' '.join(parser.parts)).strip()

def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.lower()) if unicodedata.category(c)!='Mn')

def canonical_url(value):
    try:
        p=urlsplit(str(value).strip())
        if p.scheme!='https' or not p.hostname or p.username or p.password:
            return None
        query=[(k,v) for k,v in parse_qsl(p.query,keep_blank_values=True) if not k.lower().startswith('utm_') and k.lower() not in {'fbclid','gclid','mc_cid','mc_eid'}]
        return urlunsplit((p.scheme,p.netloc,p.path,urlencode(query),''))
    except ValueError:
        return None

def parse_date(value):
    if not value: return None
    try:
        dt=datetime.fromisoformat(str(value).strip().replace('Z','+00:00'))
    except ValueError:
        try: dt=parsedate_to_datetime(str(value))
        except (TypeError,ValueError,OverflowError): return None
    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def text_child(node, names):
    for child in node:
        if child.tag.split('}')[-1].lower() in names:
            text=''.join(child.itertext())
            if text.strip(): return text.strip()
    return ''

def relevant(title, description):
    text=normalize(title+' '+description)
    if 'jair bolsonaro' in text or 'flavio bolsonaro' in text or 'tropa do flavio' in text:
        return True
    # Titulação abreviada só entra quando não aponta exclusivamente a outro familiar.
    return 'bolsonaro' in normalize(title) and not re.search(r'\b(eduardo|carlos|michelle|renan)\b',normalize(title))

def parse_feed(raw, source, now):
    if len(raw)>MAX_BYTES: raise ValueError('Feed acima do limite de tamanho')
    if re.search(br'<!\s*(DOCTYPE|ENTITY)',raw,re.I): raise ValueError('Declaração XML não permitida')
    root=ET.fromstring(raw)
    nodes=[n for n in root.iter() if n.tag.split('}')[-1] in {'item','entry'}]
    if not nodes: raise ValueError('RSS/Atom sem itens legíveis')
    selected=[]
    for entry in nodes[:300]:
        title=plain(text_child(entry,{'title'}))
        desc=plain(text_child(entry,{'description','summary','content','encoded'}))
        if not title or not relevant(title,desc): continue
        raw_url=text_child(entry,{'link'})
        for child in entry:
            if child.tag.split('}')[-1]=='link' and child.get('href') and child.get('rel','alternate')=='alternate':
                raw_url=child.get('href');break
        url=canonical_url(raw_url)
        published=parse_date(text_child(entry,{'pubdate','published','date','updated'}))
        if not url or not published or published>now+timedelta(hours=6): continue
        if published<now-timedelta(days=180): continue
        people=[]
        for word,key in [('jair','jair'),('flavio','flavio')]:
            if word in normalize(title+' '+desc):people.append(key)
        title=' '.join(title.split()[:25])
        selected.append({'id':'news-'+sha256(url.encode()).hexdigest()[:16],'title':title,'url':url,'publisher':source['name'],'publishedAt':published.isoformat().replace('+00:00','Z'),'people':people,'kind':'factcheck' if source.get('kind')=='factcheck' else 'news','sourceId':source['id'],'collectedAt':now.isoformat().replace('+00:00','Z')})
    return selected,len(nodes)

def fetch_source(source,now):
    if not canonical_url(source['url']):raise ValueError('URL de fonte inválida')
    status={'id':source['id'],'name':source['name'],'url':source['url'],'checkedAt':now.isoformat().replace('+00:00','Z'),'status':'error','itemCount':0,'matchedCount':0}
    try:
        with urlopen(Request(source['url'],headers=HEADERS),timeout=TIMEOUT) as response:
            if urlsplit(response.url).scheme!='https':raise ValueError('Redirecionamento sem HTTPS')
            raw=response.read(MAX_BYTES+1)
        items,total=parse_feed(raw,source,now)
        status.update(status='ok',itemCount=total,matchedCount=len(items),note=f'{len(items)} publicações relacionadas nesta consulta')
        return items,status
    except (HTTPError,URLError,TimeoutError,ET.ParseError,ValueError,OSError) as error:
        # Não incluir URL de redirecionamento, cabeçalhos ou detalhes potencialmente sensíveis.
        status['note']=f'Coleta indisponível ({type(error).__name__}); itens anteriores preservados'
        return [],status

def merge_items(previous,new,now):
    items={}
    for item in previous+new:
        url=canonical_url(item.get('url'));dt=parse_date(item.get('publishedAt'))
        if not url or not dt or dt<now-timedelta(days=180):continue
        item={**item,'url':url};items[url]=item
    return sorted(items.values(),key=lambda i:i['publishedAt'],reverse=True)[:MAX_ITEMS]

def atomic_write(path,content):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,delete=False) as f:
        f.write(content);tmp=f.name
    os.replace(tmp,path)

def write_payload(path,payload):
    atomic_write(path,json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    compact=json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
    atomic_write(path.with_suffix('.js'),'window.ARQUIVO_NEWS = '+compact+';\n')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sources',type=Path,default=ROOT/'content/sources.json');parser.add_argument('--output',type=Path,default=ROOT/'dist/data/news.json');args=parser.parse_args()
    config=json.loads(args.sources.read_text());sources=[s for s in config['sources'] if s.get('enabled')]
    now=datetime.now(timezone.utc);stamp=now.isoformat().replace('+00:00','Z')
    previous=json.loads(args.output.read_text()) if args.output.exists() else {'items':[],'metadata':{}}
    found=[];statuses=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(fetch_source,s,now):s for s in sources}
        for future in as_completed(futures):
            items,status=future.result();found.extend(items);statuses.append(status)
    statuses.sort(key=lambda s:s['name']);successes=sum(s['status']=='ok' for s in statuses)
    payload={'schemaVersion':1,'metadata':{'lastAttemptAt':stamp,'lastSuccessfulCheckAt':stamp if successes else previous.get('metadata',{}).get('lastSuccessfulCheckAt'),'intervalMinutes':60,'scheduleVerified':os.environ.get('GITHUB_ACTIONS')=='true' or previous.get('metadata',{}).get('scheduleVerified',False),'publicationPolicy':'Títulos, datas e links. Nenhuma classificação automática de falsidade.','successfulSources':successes,'totalSources':len(sources)},'items':merge_items(previous.get('items',[]),found,now),'feeds':statuses}
    write_payload(args.output,payload)
    print(json.dumps({'items':len(payload['items']),'successfulSources':successes,'totalSources':len(sources),'lastAttemptAt':stamp},ensure_ascii=False))
    # Uma falha completa deve aparecer também como falha da execução, após salvar o diagnóstico.
    if not successes:raise SystemExit(2)

if __name__=='__main__':main()
