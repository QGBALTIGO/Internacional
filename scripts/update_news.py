#!/usr/bin/env python3
"""Coleta RSS/Atom com fila persistente; nunca atribui conclusões editoriais."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
import ipaddress
import json
import os
from pathlib import Path
import re
import socket
import tempfile
import threading
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 3_000_000
MAX_ITEMS = 500
TIMEOUT = 18
ALLOWED_FETCH_HOSTS = frozenset({
    'www.aosfatos.org', 'aosfatos.org', 'www.agencialupa.org', 'agencialupa.org',
    'lupa.uol.com.br', 'www12.senado.leg.br', 'www.tse.jus.br',
    'agenciabrasil.ebc.com.br', 'checamos.afp.com',
})
HEADERS = {'User-Agent':'ArquivoBolsonaro/3.0 (+https://github.com/QGBALTIGO/Internacional)', 'Accept':'application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9'}
_DOMAIN_LOCKS = {}
_DOMAIN_LOCKS_GUARD = threading.Lock()

class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]
    def handle_data(self, data): self.parts.append(data)

def plain(value):
    parser=PlainText(); parser.feed(unescape(str(value or '')))
    return re.sub(r'\s+', ' ', ' '.join(parser.parts)).strip()

def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.lower()) if unicodedata.category(c)!='Mn')

def canonical_url(value):
    try:
        p=urlsplit(str(value).strip()); host=(p.hostname or '').lower().rstrip('.')
        if p.scheme!='https' or not host or p.username or p.password or p.port not in (None,443): return None
        if host in {'localhost','localhost.localdomain'} or host.endswith(('.local','.internal','.localhost')): return None
        try:
            if not ipaddress.ip_address(host).is_global: return None
        except ValueError: pass
        query=[(k,v) for k,v in parse_qsl(p.query,keep_blank_values=True) if not k.lower().startswith('utm_') and k.lower() not in {'fbclid','gclid','mc_cid','mc_eid'}]
        netloc=('['+host+']') if ':' in host else host
        return urlunsplit(('https',netloc,p.path or '/',urlencode(query),''))
    except ValueError: return None

def validate_fetch_url(value, resolve=True):
    """Só os hosts públicos auditados no código podem ser consultados pelo worker."""
    url=canonical_url(value)
    if not url or urlsplit(url).hostname not in ALLOWED_FETCH_HOSTS: raise ValueError('Destino de coleta não autorizado')
    if resolve:
        addresses=socket.getaddrinfo(urlsplit(url).hostname,443,type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses): raise ValueError('Destino de rede não público')
    return url

class SafeRedirect(HTTPRedirectHandler):
    max_redirections=4
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_fetch_url(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def parse_date(value):
    if not value: return None
    try: dt=datetime.fromisoformat(str(value).strip().replace('Z','+00:00'))
    except ValueError:
        try: dt=parsedate_to_datetime(str(value))
        except (TypeError,ValueError,OverflowError): return None
    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def stamp(now): return now.astimezone(timezone.utc).isoformat().replace('+00:00','Z')

def text_child(node, names):
    for child in node:
        if child.tag.split('}')[-1].lower() in names:
            text=''.join(child.itertext())
            if text.strip(): return text.strip()
    return ''

def relevant(title, description, focus='all'):
    text=normalize(title+' '+description)
    if focus=='flavio': return 'flavio bolsonaro' in text or 'tropa do flavio' in text
    if 'jair bolsonaro' in text or 'flavio bolsonaro' in text or 'tropa do flavio' in text: return True
    return 'bolsonaro' in normalize(title) and not re.search(r'\b(eduardo|carlos|michelle|renan)\b',normalize(title))

def parse_feed(raw, source, now):
    if len(raw)>MAX_BYTES: raise ValueError('Feed acima do limite de tamanho')
    if re.search(br'<!\s*(DOCTYPE|ENTITY)',raw,re.I): raise ValueError('Declaração XML não permitida')
    root=ET.fromstring(raw)
    nodes=[n for n in root.iter() if n.tag.split('}')[-1].lower() in {'item','entry'}]
    if not nodes: raise ValueError('RSS/Atom sem itens legíveis')
    selected=[]
    for entry in nodes[:300]:
        title=plain(text_child(entry,{'title'})); desc=plain(text_child(entry,{'description','summary','content','encoded'}))
        if not title or not relevant(title,desc,source.get('focus','all')): continue
        raw_url=text_child(entry,{'link'})
        for child in entry:
            if child.tag.split('}')[-1]=='link' and child.get('href') and child.get('rel','alternate')=='alternate': raw_url=child.get('href'); break
        if not raw_url:
            for child in entry:
                if child.tag.split('}')[-1]=='guid' and child.get('isPermaLink','true').lower()!='false': raw_url=''.join(child.itertext()); break
        url=canonical_url(raw_url); published=parse_date(text_child(entry,{'pubdate','published','date','updated'}))
        if not url or not published or published>now+timedelta(hours=6) or published<now-timedelta(days=180): continue
        people=[key for word,key in [('jair','jair'),('flavio','flavio')] if word in normalize(title+' '+desc)]
        selected.append({'id':'news-'+sha256(url.encode()).hexdigest()[:16],'title':' '.join(title.split()[:25]),'url':url,'publisher':source['name'],'publishedAt':stamp(published),'people':people,'kind':'factcheck' if source.get('kind')=='factcheck' else 'news','sourceId':source['id'],'collectedAt':stamp(now),'editorialState':'coletado','contentAccess':'metadados do feed; artigo não examinado'})
    return selected,len(nodes)

def fetch_source(source,now):
    status={'id':source['id'],'name':source['name'],'url':source['url'],'checkedAt':stamp(now),'status':'error','itemCount':0,'matchedCount':0}
    try:
        url=validate_fetch_url(source['url'])
        host=urlsplit(url).hostname
        with _DOMAIN_LOCKS_GUARD: lock=_DOMAIN_LOCKS.setdefault(host,threading.Lock())
        # Uma requisição por host de cada vez; nenhum polling por visitante.
        with lock:
            with build_opener(SafeRedirect()).open(Request(url,headers=HEADERS),timeout=TIMEOUT) as response:
                validate_fetch_url(response.url)
                raw=response.read(MAX_BYTES+1)
        items,total=parse_feed(raw,source,now)
        status.update(status='ok',itemCount=total,matchedCount=len(items),note=f'{len(items)} publicações relacionadas nesta consulta')
        return items,status
    except (HTTPError,URLError,TimeoutError,ET.ParseError,ValueError,OSError) as error:
        status['note']=f'Coleta indisponível ({type(error).__name__}); itens anteriores preservados'
        status['errorType']=type(error).__name__
        if isinstance(error,HTTPError):
            status['httpStatus']=error.code
            retry=(error.headers or {}).get('Retry-After','')
            if retry.isdigit(): status['retryAfterMinutes']=min(1440,max(1,(int(retry)+59)//60))
            elif parse_date(retry): status['retryAfterMinutes']=min(1440,max(1,int((parse_date(retry)-now).total_seconds()/60)))
        return [],status

def merge_items(previous,new,now):
    items={}
    for item in previous+new:
        url=canonical_url(item.get('url')); dt=parse_date(item.get('publishedAt'))
        if not url or not dt or dt<now-timedelta(days=180): continue
        prior=items.get(url,{})
        item={**item,'url':url}
        if prior.get('collectedAt'): item['collectedAt']=prior['collectedAt']
        items[url]=item
    return sorted(items.values(),key=lambda i:i['publishedAt'],reverse=True)[:MAX_ITEMS]

def atomic_write(path,content):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,delete=False) as f:
        f.write(content); tmp=f.name
    os.replace(tmp,path)

def write_payload(path,payload):
    atomic_write(path,json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    compact=json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
    atomic_write(path.with_suffix('.js'),'window.ARQUIVO_NEWS = '+compact+';\n')

def load_state(path):
    if not path.exists(): return {'schemaVersion':1,'sources':{},'items':{},'runs':[],'daily':{}}
    state=json.loads(path.read_text(encoding='utf-8'))
    if state.get('schemaVersion')!=1: raise ValueError('Versão de checkpoint incompatível')
    for key in ('sources','items','daily'): state.setdefault(key,{})
    state.setdefault('runs',[])
    return state

def save_state(path,state): atomic_write(path,json.dumps(state,ensure_ascii=False,indent=2)+'\n')

def is_due(job,now,force=False):
    due=parse_date(job.get('nextAttemptAt'))
    return force or job.get('state')=='running' or not due or due<=now

def record_items(state,items,now):
    added=0
    for item in items:
        url=canonical_url(item['url'])
        if not url: continue
        key=sha256(url.encode()).hexdigest()
        prior=state['items'].get(key)
        source_ids=sorted(set((prior or {}).get('sourceIds',[])+[item['sourceId']]))
        state['items'][key]={**(prior or {}),**item,'url':url,'collectedAt':(prior or {}).get('collectedAt') or item['collectedAt'],'firstCollectedAt':(prior or {}).get('firstCollectedAt') or item['collectedAt'],'lastSeenAt':max((prior or {}).get('lastSeenAt',''),stamp(now)),'sourceIds':source_ids}
        added+=prior is None
    return added

def complete_job(job,status,now,interval=60):
    previous_success=job.get('lastSuccessfulCheckAt')
    job.update(status); job['lastAttemptAt']=stamp(now)
    if status['status']=='ok':
        job.update(state='waiting',consecutiveFailures=0,lastSuccessfulCheckAt=stamp(now),lastError=None)
        delay=interval
    else:
        failures=job.get('consecutiveFailures',0)+1
        delay=min(480,15*2**min(failures-1,5))
        delay=max(delay,status.get('retryAfterMinutes',0))
        job.update(state='retry',consecutiveFailures=failures,lastSuccessfulCheckAt=previous_success,lastError={'at':stamp(now),'type':status.get('errorType','WorkerError')})
    job['nextAttemptAt']=stamp(now+timedelta(minutes=delay))
    return job

def execution_evidence(now):
    run_id=os.environ.get('GITHUB_RUN_ID',''); repo=os.environ.get('GITHUB_REPOSITORY',''); event=os.environ.get('GITHUB_EVENT_NAME','')
    if repo=='QGBALTIGO/Internacional' and re.fullmatch(r'\d+',run_id):
        return {'provider':'GitHub Actions','id':run_id,'url':f'https://github.com/{repo}/actions/runs/{run_id}','event':event,'attempt':os.environ.get('GITHUB_RUN_ATTEMPT'),'startedAt':stamp(now),'note':'Registro de execução iniciado pelo worker; conferir conclusão no provedor.'}
    return {'provider':'execução local','id':None,'url':None,'startedAt':stamp(now)}

def collect(config,previous,state,state_path,now,force=False,fetcher=fetch_source):
    sources=[{**s,'focus':s.get('focus',config.get('focus','flavio'))} for s in config['sources'] if s.get('enabled')]
    if len({s['id'] for s in sources})!=len(sources): raise ValueError('IDs de fontes duplicados')
    old_feeds={f['id']:f for f in previous.get('feeds',[])}
    # Migração inicial dos metadados anteriores, antes dos novos resultados.
    for item in previous.get('items',[]):
        if item.get('sourceId') and item.get('collectedAt'): record_items(state,[item],parse_date(item.get('collectedAt')) or now)
    for s in sources:
        if s['id'] not in state['sources']:
            old=old_feeds.get(s['id'],{})
            state['sources'][s['id']]={**old,'state':'waiting','lastSuccessfulCheckAt':old.get('checkedAt') if old.get('status')=='ok' else None}
    due=[s for s in sources if is_due(state['sources'][s['id']],now,force)]
    for s in due: state['sources'][s['id']].update(state='running',startedAt=stamp(now))
    # Checkpoint anterior à rede: um processo interrompido retoma jobs running.
    save_state(state_path,state)
    found=[]; successes=0; new_count=0; errors=0
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(fetcher,s,now):s for s in due}
        for future in as_completed(futures):
            s=futures[future]
            try: items,status=future.result()
            except Exception as error:
                items=[];status={'id':s['id'],'name':s['name'],'url':s['url'],'checkedAt':stamp(now),'status':'error','itemCount':0,'matchedCount':0,'errorType':type(error).__name__,'note':'Falha isolada do worker; itens anteriores preservados'}
            found.extend(items); successes+=status['status']=='ok'; errors+=status['status']!='ok'
            new_count+=record_items(state,items,now)
            complete_job(state['sources'][s['id']],status,now,int(s.get('intervalMinutes',config.get('intervalMinutes',60))))
            # Ledger e conclusão do job são gravados juntos após cada resultado.
            save_state(state_path,state)
    evidence=execution_evidence(now)
    report={'at':stamp(now),'attemptedSources':len(due),'successfulSources':successes,'failedSources':errors,'newMaterials':new_count,'execution':evidence}
    state['runs']=(state['runs']+[report])[-120:]
    day=now.date().isoformat(); daily=state['daily'].setdefault(day,{'newMaterials':0,'successfulCollections':0,'failedCollections':0,'editorialReviews':0,'corrections':0})
    daily['newMaterials']+=new_count;daily['successfulCollections']+=successes;daily['failedCollections']+=errors
    state['updatedAt']=stamp(now); save_state(state_path,state)
    feeds=[]
    for s in sources:
        job=state['sources'][s['id']]
        feeds.append({k:job.get(k) for k in ('checkedAt','status','itemCount','matchedCount','note','lastAttemptAt','lastSuccessfulCheckAt','lastError','nextAttemptAt','consecutiveFailures','state') if job.get(k) is not None}|{'id':s['id'],'name':s['name'],'url':s['url']})
    feeds.sort(key=lambda f:f['name'])
    old_meta=previous.get('metadata',{})
    payload={'schemaVersion':1,'metadata':{'lastAttemptAt':stamp(now) if due else old_meta.get('lastAttemptAt'),'lastSuccessfulCheckAt':stamp(now) if successes else old_meta.get('lastSuccessfulCheckAt'),'intervalMinutes':config.get('intervalMinutes',60),'scheduleVerified':False,'execution':evidence,'publicationPolicy':'Metadados de descoberta. Nenhuma classificação automática de falsidade.','successfulSources':sum(f.get('status')=='ok' for f in feeds),'totalSources':len(sources),'attemptedSourcesThisRun':len(due),'successfulSourcesThisRun':successes,'focus':'flavio','persistentCatalogItems':len(state['items']),'pendingEditorialReview':sum(i.get('editorialState','coletado')=='coletado' for i in state['items'].values()),'queue':{'waiting':sum(j.get('state')=='waiting' for j in state['sources'].values()),'retry':sum(j.get('state')=='retry' for j in state['sources'].values())},'dailyBalance':{'dateUTC':day,**daily}},'items':merge_items(previous.get('items',[]),found,now),'feeds':feeds}
    return payload,report

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sources',type=Path,default=ROOT/'content/sources.json');parser.add_argument('--output',type=Path,default=ROOT/'dist/data/news.json');parser.add_argument('--state',type=Path,default=ROOT/'.monitor/state.json');parser.add_argument('--force',action='store_true',help='Consultar fontes agora, preservando o checkpoint e as URLs anteriores');args=parser.parse_args()
    config=json.loads(args.sources.read_text()); previous=json.loads(args.output.read_text()) if args.output.exists() else {'items':[],'metadata':{}}
    state=load_state(args.state)
    payload,report=collect(config,previous,state,args.state,datetime.now(timezone.utc),args.force)
    write_payload(args.output,payload); print(json.dumps(report,ensure_ascii=False))
    if report['attemptedSources'] and not report['successfulSources']: raise SystemExit(2)

if __name__=='__main__':main()
