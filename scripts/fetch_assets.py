#!/usr/bin/env python3
"""Baixa os anexos públicos do manifesto e confere seu SHA-256 antes de gravar."""
import hashlib
import json
from pathlib import Path
import sys
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 30 * 1024 * 1024


def main():
    manifest = json.loads((ROOT / 'content/assets.json').read_text())
    failures = []
    for asset in manifest['assets']:
        path = (ROOT / asset['path']).resolve()
        if not path.is_relative_to(ROOT / 'dist'):
            raise ValueError('Caminho fora do diretório público')
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == asset['sha256']:
            print('Disponível:', asset['path'])
            continue
        url = urllib.parse.urlsplit(asset['url'])
        if url.scheme != 'https' or url.username or url.password:
            raise ValueError('Endereço inválido no manifesto')
        try:
            request = urllib.request.Request(asset['url'], headers={'User-Agent': 'ArquivoBolsonaro/2.0 (arquivo documental)'})
            with urllib.request.urlopen(request, timeout=45) as response:
                if urllib.parse.urlsplit(response.url).scheme != 'https':
                    raise ValueError('Redirecionamento para endereço sem HTTPS')
                content = response.read(LIMIT + 1)
            if len(content) > LIMIT:
                raise ValueError('Arquivo acima do limite de 30 MB')
            if hashlib.sha256(content).hexdigest() != asset['sha256']:
                raise ValueError('SHA-256 diferente do arquivo conferido; revisar a origem antes de substituir')
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(path.suffix + '.tmp')
            temporary.write_bytes(content)
            temporary.replace(path)
            print('Conferido:', asset['path'])
        except Exception as exc:
            failures.append(asset['path'])
            print('Falha:', asset['path'], str(exc), file=sys.stderr)
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
