#!/usr/bin/env python3
"""Integra lotes editoriais explicitamente revisados. Não busca nem classifica fatos."""
import argparse
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]

def clean(value):
    if isinstance(value,str):return value.replace('\u2014',' / ').replace('\u2013',' a ')
    if isinstance(value,list):return [clean(x) for x in value]
    if isinstance(value,dict):return {k:clean(v) for k,v in value.items() if k not in {'localPath','transcriptLocalPath','evidencePath','evidenceDirectory'}}
    return value

def merge_by_id(old,new):
    items={x['id']:x for x in old}
    for item in new:items[item['id']]=item
    return list(items.values())

def main():
    p=argparse.ArgumentParser();p.add_argument('--jair',type=Path,required=True);p.add_argument('--flavio',type=Path,required=True);p.add_argument('--media',type=Path,required=True);a=p.parse_args()
    path=ROOT/'content/acervo.editorial.json';data=json.loads(path.read_text())
    j=json.loads(a.jair.read_text());f=json.loads(a.flavio.read_text());m=json.loads(a.media.read_text())
    for batch in [j,f]:
        data['records']=merge_by_id(data['records'],batch.get('records',[]))
        for key in ['comparisons','investigations','documents']:
            data[key]=merge_by_id(data.get(key,[]),batch.get(key,[]))
    media=[]
    for item in m['media']:
        item={**item,'id':item['id'].lower()}
        item['people']=['jair' if 'Jair' in name else 'flavio' for name in item.get('persons',[]) if 'Jair' in name or 'Flávio' in name]
        item['creditShort']=item.get('publisher',item.get('credit','Publicador'))
        item['hasTranscript']=bool(item.get('transcriptAvailable'))
        if item.get('durationSeconds'):
            duration=int(item['durationSeconds']);item['durationLabel']=f'{duration//60}min{duration%60:02d}s'
        if item['type']=='audio':item['src']=item['url']
        media.append(item)
    data['media']=merge_by_id(data['media'],media)
    for old in data['media']:
        if 'people' not in old:old['people']=[]
    ids={i['id'] for i in data['records']}
    for r in data['records']:
        r.setdefault('relatedMedia',[]);r.setdefault('reviewedAt',r.get('verifiedAt','2026-10-24'))
        r.setdefault('datePrecision','day' if r.get('statementDate') else 'month')
        r.setdefault('sortDate',r.get('statementDate') or str(r['year']))
        for item in media:
            direct=r['id'] in item.get('caseIds',[])
            interview=item.get('date')==r.get('statementDate') and r['person'] in item['people'] and re.search(r'entrevista|debate|podcast|roda viva',item.get('role','')+' '+item.get('title',''),re.I)
            if (direct or interview) and item['id'] not in r['relatedMedia']:r['relatedMedia'].append(item['id'])
    for doc in data['documents']:
        doc.setdefault('sourceUrl',doc['url']);doc.setdefault('credit',doc.get('publisher','Documento público'))
        if doc.get('pageCount'):doc.setdefault('pages',doc['pageCount'])
    by_url={n['url']:n for n in data.get('news',[])}
    for n in m.get('news',[])+f.get('news',[])+j.get('noticias',[]):
        if not n.get('url'):continue
        n={**n,'publishedAt':n.get('publishedAt') or n.get('date'),'kind':n.get('kind','news')}
        by_url[n['url']]=n
    data['news']=list(by_url.values())
    data['metadata'].update(title='Arquivo Bolsonaro | Declarações e documentos',edition='02',version='2.0.0',reviewedAt='2026-10-24',scope='Acervo selecionado, com checagens, comparações de falas, apurações e acompanhamento periódico de fontes públicas.',repository='https://github.com/QGBALTIGO/Internacional')
    data['spotlights']=['flavio-viagens-sete-bilhoes-2026','jair-vacinas-compras-2020','flavio-pf-filme-lula-2026']
    path.write_text(json.dumps(clean(data),ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:len(data.get(k,[])) for k in ['records','media','comparisons','investigations','documents','news']}))

if __name__=='__main__':main()
