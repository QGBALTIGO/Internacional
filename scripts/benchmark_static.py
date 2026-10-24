#!/usr/bin/env python3
"""Teste de transporte estático local. Não mede CDN, navegador ou usuários reais."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import statistics
from threading import Thread
from time import perf_counter
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=json.dumps({'synthetic':True,'items':[{'id':'synthetic-scale-'+str(i),'title':'Registro técnico '+str(i),'format':'registro','stage':'encontrado','url':'https://example.org/fixture/'+str(i),'summary':'Fixture de capacidade, sem afirmação editorial.'} for i in range(1000)]},ensure_ascii=False).encode()
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        if self.path=='/fixture-1000.json':
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(FIXTURE)));self.end_headers();self.wfile.write(FIXTURE)
        else:super().do_GET()
class Server(ThreadingHTTPServer):request_queue_size=128;daemon_threads=True
def main():
    server=Server(('127.0.0.1',0),partial(Quiet,directory=str(ROOT/'dist')))
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    base='http://127.0.0.1:'+str(server.server_port)
    def get(n):
        start=perf_counter()
        with urlopen(base+('/fixture-1000.json' if n%2 else '/index.html'),timeout=15) as response:
            raw=response.read();assert response.status==200 and raw
        return (perf_counter()-start)*1000,len(raw)
    start=perf_counter()
    try:
        with ThreadPoolExecutor(max_workers=100) as pool:results=list(pool.map(get,range(300)))
    finally:server.shutdown();server.server_close()
    elapsed=perf_counter()-start;times=sorted(x[0] for x in results)
    out={'executedAtUTC':datetime.now(timezone.utc).isoformat(),'environment':'CPython ThreadingHTTPServer, loopback, sem TLS/cache/CDN; não é navegador','targetConcurrentRequests':100,'catalogVolumeTarget':1000,'fixtureRecords':1000,'fixtureStoredInProduction':False,'requests':len(results),'errors':0,'elapsedSeconds':round(elapsed,3),'p50Ms':round(statistics.median(times),2),'p95Ms':round(times[int(len(times)*.95)-1],2),'bytesTransferred':sum(x[1] for x in results),'limitations':['100 tarefas HTTP concorrentes não equivalem a 100 sessões completas de navegador.','Meta inicial: 1.000 materiais e 100 requisições simultâneas. O acervo real atual tem 82 materiais; este teste mede uma fixture de 1.000 metadados, não 1.000 sessões de navegador.','Nenhuma solicitação pública executa coleta, transcrição ou modelo.']}
    dest=ROOT/'documentacao/benchmark-local.json';dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':main()
