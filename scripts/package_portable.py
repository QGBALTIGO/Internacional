#!/usr/bin/env python3
"""Empacota uma cópia portátil, sem identidade de hospedagem nem metadados Git."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist' if (ROOT / 'dist').is_dir() else ROOT
DEST = DIST / 'documentos' / 'arquivo-bolsonaro.zip'


def main():
    payload = {}
    for path in sorted(DIST.rglob('*')):
        if not path.is_file() or path == DEST or path.name.startswith('qa-'):
            continue
        if any(part.startswith('.') or part == '__pycache__' for part in path.relative_to(DIST).parts):
            continue
        payload[path.relative_to(DIST).as_posix()] = path.read_bytes()
    payload['index.html'] = payload['index.html'].decode('utf-8').replace('<html lang="pt-BR">','<html lang="pt-BR" data-portable="true">',1).encode('utf-8')
    for rel in ['README.md','requirements.txt','content','scripts','documentacao','tests']:
        base=ROOT / rel
        files=[base] if base.is_file() else sorted(base.rglob('*'))
        for path in files:
            if path.is_file() and '__pycache__' not in path.parts:
                payload[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    manifest = {name:{'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()} for name,blob in sorted(payload.items())}
    payload['documentacao/ARQUIVOS-SHA256.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    DEST.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(DEST,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,blob in sorted(payload.items()):
            archive.writestr('arquivo-bolsonaro/'+name,blob)
    with zipfile.ZipFile(DEST) as archive:
        assert archive.testzip() is None
        assert 'arquivo-bolsonaro/index.html' in archive.namelist()
        assert not any('/.git/' in name or '/.openai/' in name for name in archive.namelist())
    print(json.dumps({'archive':str(DEST),'bytes':DEST.stat().st_size,'files':len(payload)},ensure_ascii=False))


if __name__=='__main__':
    main()
