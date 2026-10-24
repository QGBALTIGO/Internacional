"""Fixtures sintéticas, isoladas em diretórios temporários; nunca vão ao acervo."""
import importlib.util
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.request import Request

spec=importlib.util.spec_from_file_location('monitor',Path(__file__).resolve().parents[1]/'scripts/update_news.py')
monitor=importlib.util.module_from_spec(spec);spec.loader.exec_module(monitor)

class MonitorPersistence(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,10,24,3,tzinfo=timezone.utc)
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'state.json'
        self.config={'intervalMinutes':60,'sources':[{'id':'a','name':'A','url':'https://www12.senado.leg.br/rss','enabled':True},{'id':'b','name':'B','url':'https://www.tse.jus.br/rss','enabled':True}]}
        self.item={'id':'news-test','title':'Flávio Bolsonaro','url':'https://www12.senado.leg.br/item?utm_source=test','publishedAt':'2026-10-23T00:00:00Z','collectedAt':monitor.stamp(self.now),'sourceId':'a','editorialState':'coletado'}
        self.previous={'items':[],'metadata':{}}
    def fetch(self,source,now):
        return [{**self.item,'sourceId':source['id']}],{'id':source['id'],'name':source['name'],'url':source['url'],'status':'ok','checkedAt':monitor.stamp(now),'itemCount':1,'matchedCount':1}
    def test_restart_and_duplicate_sources_preserve_one_record(self):
        state=monitor.load_state(self.path)
        first,report=monitor.collect(self.config,self.previous,state,self.path,self.now,fetcher=self.fetch)
        self.assertEqual(len(state['items']),1)
        self.assertEqual(report['newMaterials'],1)
        row=next(iter(state['items'].values()))
        self.assertEqual(row['sourceIds'],['a','b'])
        self.assertNotIn('verdict',row)
        restarted=monitor.load_state(self.path)
        after,report2=monitor.collect(self.config,first,restarted,self.path,self.now+timedelta(minutes=1),fetcher=lambda *_:self.fail('Not due'))
        self.assertEqual(report2['attemptedSources'],0)
        self.assertEqual(after['metadata']['lastSuccessfulCheckAt'],first['metadata']['lastSuccessfulCheckAt'])
        _,report3=monitor.collect(self.config,after,monitor.load_state(self.path),self.path,self.now+timedelta(hours=1),fetcher=self.fetch)
        self.assertEqual(report3['newMaterials'],0)
        self.assertEqual(len(monitor.load_state(self.path)['items']),1)
    def test_failure_isolated_and_last_success_retained(self):
        state=monitor.load_state(self.path)
        first,_=monitor.collect(self.config,self.previous,state,self.path,self.now,fetcher=self.fetch)
        def fail_one(source,now):
            if source['id']=='a': raise RuntimeError('synthetic')
            return self.fetch(source,now)
        second,report=monitor.collect(self.config,first,state,self.path,self.now+timedelta(hours=1),fetcher=fail_one)
        self.assertEqual(report['successfulSources'],1)
        job=state['sources']['a']
        self.assertEqual(job['state'],'retry')
        self.assertEqual(job['lastSuccessfulCheckAt'],monitor.stamp(self.now))
        self.assertEqual(job['nextAttemptAt'],monitor.stamp(self.now+timedelta(hours=1,minutes=15)))
        self.assertEqual(len(second['items']),1)
    def test_running_job_resumes_even_with_future_due_time(self):
        state=monitor.load_state(self.path)
        state['sources']['a']={'state':'running','nextAttemptAt':monitor.stamp(self.now+timedelta(hours=24))}
        _,report=monitor.collect(self.config,self.previous,state,self.path,self.now,fetcher=self.fetch)
        self.assertEqual(report['attemptedSources'],2)
        self.assertEqual(state['sources']['a']['state'],'waiting')
    def test_public_window_does_not_delete_historical_ledger(self):
        state=monitor.load_state(self.path)
        monitor.record_items(state,[{**self.item,'publishedAt':'2025-01-01T00:00:00Z'}],self.now)
        self.assertEqual(monitor.merge_items(list(state['items'].values()),[],self.now),[])
        self.assertEqual(len(state['items']),1)
    def test_exponential_backoff_and_quota_retry_after(self):
        job={'lastSuccessfulCheckAt':'2026-10-23T00:00:00Z'}
        status={'status':'error','errorType':'HTTPError','retryAfterMinutes':90}
        monitor.complete_job(job,status,self.now)
        self.assertEqual(job['nextAttemptAt'],monitor.stamp(self.now+timedelta(minutes=90)))
        for _ in range(8): monitor.complete_job(job,{'status':'error'},self.now)
        self.assertEqual(job['nextAttemptAt'],monitor.stamp(self.now+timedelta(minutes=480)))
    def test_rdf_namespace_and_guid_only(self):
        raw='<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://purl.org/rss/1.0/" xmlns:dc="http://purl.org/dc/elements/1.1/"><item><title>Flávio Bolsonaro</title><link>https://www.tse.jus.br/item</link><dc:date>2026-10-23T13:00:00-03:00</dc:date></item></rdf:RDF>'.encode()
        items,_=monitor.parse_feed(raw,{'id':'a','name':'A'},self.now)
        self.assertEqual(items[0]['publishedAt'],'2026-10-23T16:00:00Z')
        raw='<rss><channel><item><title>Flávio Bolsonaro</title><guid>https://www12.senado.leg.br/item</guid><pubDate>Fri, 23 Oct 2026 12:00:00 GMT</pubDate></item></channel></rss>'.encode()
        self.assertEqual(len(monitor.parse_feed(raw,{'id':'a','name':'A'},self.now)[0]),1)
    def test_flavio_focus_does_not_silently_attribute_jair(self):
        self.assertFalse(monitor.relevant('Jair Bolsonaro responde','',focus='flavio'))
        self.assertTrue(monitor.relevant('Jair Bolsonaro responde','entrevista com Flávio Bolsonaro',focus='flavio'))
    def test_private_network_and_redirect_destination_rejected(self):
        for value in ['https://127.0.0.1/','https://169.254.169.254/','https://[::1]/','https://localhost/','https://host.internal/']:
            self.assertIsNone(monitor.canonical_url(value))
        for value in ['https://example.com/feed','https://www12.senado.leg.br:8443/rss','https://127.0.0.1/rss']:
            with self.assertRaises(ValueError): monitor.validate_fetch_url(value,resolve=False)
        with patch.object(monitor.socket,'getaddrinfo',return_value=[(2,1,6,'',('10.0.0.1',443))]):
            with self.assertRaises(ValueError): monitor.validate_fetch_url('https://www12.senado.leg.br/rss')
        with self.assertRaises(ValueError): monitor.SafeRedirect().redirect_request(Request('https://www.tse.jus.br/rss'),None,302,'Found',{},'https://127.0.0.1/secret')
    def test_environment_flag_without_run_evidence_does_not_verify_schedule(self):
        with patch.dict(monitor.os.environ,{'GITHUB_ACTIONS':'true','GITHUB_RUN_ID':'','GITHUB_REPOSITORY':''},clear=True):
            evidence=monitor.execution_evidence(self.now)
        self.assertIsNone(evidence['url'])
        self.assertNotIn('scheduleVerified',evidence)

if __name__=='__main__': unittest.main()
