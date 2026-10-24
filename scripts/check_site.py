#!/usr/bin/env python3
"""Confere estrutura, referências locais e separação editorial sem abrir navegador."""
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
class Inspect(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.urls=[];self.headings=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id'):self.ids.append(a['id'])
        for k in ('src','href'):
            if a.get(k):self.urls.append(a[k])
        if tag=='h1':self.headings+=1

def main():
    s=(DIST/'index.html').read_text();p=Inspect();p.feed(s)
    assert len(p.ids)==len(set(p.ids)),'IDs repetidos'
    assert p.headings==1,'Hierarquia de título principal'
    assert '—' not in s,'Travessão na interface'
    for u in p.urls:
        v=urlsplit(u)
        if v.scheme:assert v.scheme=='https',u;continue
        if u.startswith('#'):
            if '=' not in u:assert u[1:] in p.ids,u
        elif v.path:
            path=(DIST/v.path).resolve();assert path.is_relative_to(DIST.resolve()) and path.is_file(),u
    r=json.loads((ROOT/'content/research.json').read_text())
    assert r['metrics']['reviewedAudioSeconds']==0
    assert r['metrics']['publishedChecks']==0
    assert all(i['review']['reviewer'] is None and i.get('editorialClassification') is None for i in r['items'])
    assert (DIST/'data/research.json').read_bytes()==(ROOT/'content/research.json').read_bytes()
    # Os IDs de fala permanecem no acervo original; arquivos de pesquisa não os substituem.
    d=json.loads((ROOT/'content/acervo.editorial.json').read_text());assert len(d['records'])==71
    assert len({x['id'] for x in d['records']})==71
    assert d['metadata']['approvedReviewerIds']==[]
    print(json.dumps({'htmlIds':len(p.ids),'localAndAnchorLinksChecked':len(p.urls),'materials':len(r['items']),'legacyRecords':len(d['records']),'newSensitiveChecks':0},ensure_ascii=False))
if __name__=='__main__':main()
