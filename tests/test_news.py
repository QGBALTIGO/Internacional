"""Casos de integridade da coleta: HTML, datas, atribuição, falhas e duplicação."""
import importlib.util
from datetime import datetime,timezone
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('collector',Path(__file__).resolve().parents[1]/'scripts/update_news.py')
collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)

class FeedIntegrity(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,10,24,tzinfo=timezone.utc)
        self.source={'id':'test','name':'Fonte de teste','url':'https://example.com/rss','kind':'news'}
    def test_rss_metadata_only_and_tracking_removed(self):
        raw=b'<rss><channel><item><title>Jair Bolsonaro em entrevista</title><link>https://example.com/item?utm_source=x&amp;id=2</link><pubDate>Fri, 23 Oct 2026 12:00:00 GMT</pubDate><description>&lt;b&gt;Texto integral privado ao feed&lt;/b&gt;</description></item></channel></rss>'
        items,total=collector.parse_feed(raw,self.source,self.now)
        self.assertEqual(total,1);self.assertEqual(items[0]['url'],'https://example.com/item?id=2')
        self.assertNotIn('description',items[0]);self.assertNotIn('verdict',items[0])
    def test_atom_and_explicit_attribution(self):
        raw='<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Flávio Bolsonaro no Senado</title><link href="https://example.com/flavio"/><published>2026-10-23T10:00:00-03:00</published><summary>Discurso</summary></entry></feed>'.encode()
        items,_=collector.parse_feed(raw,self.source,self.now)
        self.assertEqual(items[0]['people'],['flavio'])
        self.assertEqual(items[0]['publishedAt'],'2026-10-23T13:00:00Z')
    def test_no_automatic_family_attribution(self):
        self.assertFalse(collector.relevant('Eduardo Bolsonaro em viagem',''))
        self.assertTrue(collector.relevant('Eduardo e Jair Bolsonaro em viagem',''))
    def test_entity_payload_rejected(self):
        with self.assertRaises(ValueError):collector.parse_feed(b'<!DOCTYPE foo [<!ENTITY x "abc">]><rss/>',self.source,self.now)
    def test_only_https_and_no_credentials(self):
        for url in ['javascript:alert(1)','https://user:password@example.com','http://example.com']:
            self.assertIsNone(collector.canonical_url(url))
    def test_prior_items_survive_failed_collection(self):
        old={'id':'x','url':'https://example.com/a','title':'Registro anterior','publishedAt':'2026-10-20T00:00:00Z'}
        self.assertEqual(collector.merge_items([old],[],self.now),[old])
        self.assertEqual(len(collector.merge_items([old],[{**old,'title':'Título corrigido'}],self.now)),1)

if __name__=='__main__':unittest.main()
