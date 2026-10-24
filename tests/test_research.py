"""Testes com dados sintéticos isolados; nenhum fixture integra a publicação."""
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'scripts' / 'build_research.py'
spec = importlib.util.spec_from_file_location('research', MODULE)
research = importlib.util.module_from_spec(spec)
spec.loader.exec_module(research)


class ResearchPipelineTest(unittest.TestCase):
    def record(self, **overrides):
        return {'id': 'synthetic-record', 'title': 'Fixture técnico', 'url': 'https://example.org/artigo',
                'source': 'Fonte sintética', 'date': '2020-03', 'stage': 'acessado_e_analisado_em_texto',
                'summary': 'Texto de teste, sem afirmações sobre pessoas reais.', **overrides}

    def test_material_dedup_does_not_become_independent_evidence(self):
        payload = research.build_payload({'a': {'records': [self.record()]},
                                          'b': {'records': [self.record(url='https://example.org/artigo?utm_source=test')]}})
        self.assertEqual(len(payload['items']), 1)
        self.assertEqual(len(payload['items'][0]['researchOrigins']), 2)
        self.assertEqual(payload['metrics']['distinctStatements'], 0)
        self.assertEqual(payload['metrics']['publishedChecks'], 0)
        self.assertIsNone(payload['items'][0]['editorialClassification'])

    def test_model_reviewer_and_audio_cannot_be_inferred(self):
        row = self.record(kind='video', human_reviewed=True, reviewer='automação', stage='published', duration_seconds=120)
        payload = research.build_payload({'a': {'records': [row]}})
        self.assertNotIn(payload['items'][0]['stage'], {'revisado', 'publicado'})
        self.assertIsNone(payload['items'][0]['review']['reviewer'])
        self.assertEqual(payload['metrics']['reviewedAudioSeconds'], 0)
        self.assertEqual(payload['metrics']['mediaCataloguedSeconds'], 120)

    def test_partial_dates_and_missing_year_are_preserved(self):
        payload = research.build_payload({'a': {'records': [self.record(), self.record(id='b', url='https://example.org/outro', date=None)]}})
        partial = next(i for i in payload['items'] if i['date'])
        self.assertEqual(partial['date'], '2020-03')
        self.assertEqual(partial['datePrecision'], 'month')
        self.assertEqual(payload['metrics']['undatedItems'], 1)
        self.assertEqual(next(r for r in payload['coverage'] if r['year'] == 2020)['found'], 1)

    def test_failed_access_never_becomes_accessed_due_to_substring(self):
        payload = research.build_payload({'a': {'records': [self.record(stage=None, access_state='found_not_accessed')]}})
        self.assertEqual(payload['items'][0]['stage'], 'encontrado')
        self.assertEqual(payload['metrics']['accessed'], 0)

    def test_legacy_link_does_not_become_a_new_material_or_review(self):
        legacy = {'records': [{'id': 'legacy-1', 'person': 'flavio', 'claim': 'Fixture de teste', 'verdict': 'Falso',
                               'sources': [{'url': 'https://example.org/artigo'}], 'reviewedAt': '2020-01-01'}]}
        payload = research.build_payload({'a': {'records': [self.record()]}}, legacy)
        self.assertEqual(payload['metrics']['newItems'], 0)
        self.assertEqual(payload['items'][0]['legacyRecordIds'], ['legacy-1'])
        self.assertEqual(payload['metrics']['reviewed'], 0)
        self.assertEqual(payload['statements'][0]['origin'], 'edição anterior')

    def test_stable_ids_and_generation_checkpoint(self):
        inputs = {'a': {'records': [self.record()]}}
        first = research.build_payload(inputs)
        second = research.build_payload(inputs, previous=first)
        self.assertEqual(first['items'][0]['id'], second['items'][0]['id'])
        self.assertEqual(first['metadata']['generatedAt'], second['metadata']['generatedAt'])
        self.assertEqual(first['metadata']['inputHash'], second['metadata']['inputHash'])

    def test_page_metadata_is_not_analyzed_transcript(self):
        payload = research.build_payload({'a': {'records': [self.record(stage=None, access_state='metadata_accessed', kind='video')]}})
        self.assertEqual(payload['items'][0]['stage'], 'acessado')
        self.assertEqual(payload['metrics']['analysed'], 0)
        self.assertIsNone(payload['items'][0]['transcript']['text'])

    def test_media_exports_only_observed_platform_identifier(self):
        row = self.record(stage=None, access_state='metadata_accessed', kind='video', platform='youtube', platform_id='abcdefghijk')
        payload = research.build_payload({'a': {'records': [row]}})
        self.assertEqual(payload['media'][0]['youtubeId'], 'abcdefghijk')
        self.assertEqual(payload['media'][0]['reviewState'], 'aguardando revisão')
        self.assertIn('não ouvido', payload['media'][0]['verificationNote'])

    def test_rebuild_preserves_actual_editorial_history(self):
        inputs = {'a': {'records': [self.record()]}}
        history = [{'id': 'synthetic-history', 'description': 'Fixture de correção técnica.'}]
        first = research.build_payload(inputs, history=history)
        second = research.build_payload(inputs, previous=first)
        self.assertEqual(second['history'], history)
        self.assertEqual(second['metadata']['generatedAt'], first['metadata']['generatedAt'])

    def test_does_not_accept_unsafe_urls(self):
        for url in ('http://example.org', 'https://user:pass@example.org/', 'javascript:alert(1)', 'https://example.org:8000/'):
            self.assertIsNone(research.canonical_url(url))


if __name__ == '__main__':
    unittest.main()
