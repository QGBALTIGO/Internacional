#!/usr/bin/env python3
"""Valida o conteúdo editorial e gera os dados usados pela página e as exportações."""
import csv
import io
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist' if (ROOT / 'dist').is_dir() else ROOT
SOURCE = ROOT / 'content' / 'acervo.editorial.json'


def main():
    data = json.loads(SOURCE.read_text(encoding='utf-8'))
    records = data['records']
    assert records, 'O acervo não pode estar vazio.'
    ids = [r['id'] for r in records]
    assert len(ids) == len(set(ids)), 'Há identificadores de fichas duplicados.'
    media_ids = {m['id'] for m in data['media']}
    assert len(media_ids) == len(data['media']), 'Há identificadores de mídia duplicados.'
    for record in records:
        assert re.fullmatch(r'[a-z0-9-]+', record['id']), record['id']
        assert record['person'] in {'jair', 'flavio'}, record['id']
        assert record['verdict'] in {'Confirmado','Falso','Enganoso','Sem comprovação','Sem comprovação suficiente','Inconclusivo','Contradição documentada','Mudança de posição','Opinião, previsão ou promessa'}, record['id']
        assert record['sources'], f"Sem fonte: {record['id']}"
        for key in ('title', 'claim', 'summary', 'context', 'dateLabel', 'topic'):
            assert isinstance(record[key], str) and record[key].strip(), f'{record["id"]}: {key}'
        if record['statementDate']:
            assert date.fromisoformat(record['statementDate']).year == record['year'], record['id']
        assert set(record.get('relatedMedia', [])) <= media_ids, record['id']
        for source in record['sources']:
            parsed = urlparse(source['url'])
            assert parsed.scheme == 'https' and parsed.hostname, source['url']
            assert source['publisher'] and source['title'], record['id']
    for collection in ('comparisons', 'investigations'):
        for item in data.get(collection, []):
            assert item['id'] and item['title'] and item['sources'], item
            assert item['person'] in {'jair', 'flavio'}, item['id']
            if collection == 'comparisons':
                assert item['first']['summary'] and item['second']['summary'], item['id']
                assert item['first']['sourceUrl'] and item['second']['sourceUrl'], item['id']
    for item in data['media'] + data['documents'] + data['images']:
        for key in ('src', 'thumbnail'):
            if not item.get(key):
                continue
            if item[key].startswith('https://'):
                assert urlparse(item[key]).hostname, item['id']
                continue
            path = (DIST / item[key]).resolve()
            assert path.is_relative_to(DIST.resolve()), f'Caminho fora do projeto: {path}'
            assert path.is_file() and path.stat().st_size > 0, f'Arquivo ausente: {path}'
            if path.suffix == '.pdf':
                assert path.read_bytes().startswith(b'%PDF-'), f'PDF inválido: {path}'
    out = DIST / 'data'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'acervo.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    compact = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    (out / 'acervo.js').write_text('window.ACERVO = ' + compact + ';\n', encoding='utf-8')
    table = io.StringIO(newline='')
    writer = csv.writer(table, delimiter=';', quoting=csv.QUOTE_ALL)
    writer.writerow(['id','pessoa','data','ano','tema','classificacao','titulo','declaracao_parafrase','evidencia','contexto','fontes'])
    def cell(value):
        value = str(value or '')
        return "'" + value if value.startswith(('=', '+', '-', '@', '\t', '\r')) else value
    for r in records:
        row = [r['id'], 'Jair Bolsonaro' if r['person']=='jair' else 'Flávio Bolsonaro', r['statementDate'] or r['dateLabel'], r['year'], r['topic'], r['verdict'], r['title'], r['claim'], r['summary'], r['context'], '\n'.join(f"{s['publisher']}: {s['url']}" for s in r['sources'])]
        writer.writerow([cell(v) for v in row])
    (out / 'acervo.csv').write_text('\ufeff' + table.getvalue(), encoding='utf-8', newline='')
    patch_source = ROOT / 'content' / 'editorial-updates.json'
    if patch_source.exists():
        patch = json.loads(patch_source.read_text(encoding='utf-8'))
        (out / 'editorial-updates.json').write_text(json.dumps(patch, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        (out / 'editorial-updates.js').write_text('window.ARQUIVO_UPDATES = ' + json.dumps(patch, ensure_ascii=False, separators=(',', ':')).replace('</','<\\/') + ';\n', encoding='utf-8')
    result = {'records':len(records),'people':dict(Counter(r['person'] for r in records)),'verdicts':dict(Counter(r['verdict'] for r in records)),'uniqueSources':len({s['url'] for r in records for s in r['sources']}),'media':len(data['media']),'documents':len(data['documents']),'comparisons':len(data.get('comparisons',[])),'investigations':len(data.get('investigations',[]))}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()

