"""Contratos da apresentação e dos formatos; fixtures não entram no catálogo."""
import importlib.util
import json
from pathlib import Path
import re
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_research_portal', ROOT/'scripts/build_research.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

class PortalContractTest(unittest.TestCase):
    def test_explicit_documentary_format_is_preserved(self):
        for fmt in build.FORMATS:
            self.assertEqual(build.format_for({'format':fmt}, 'extra-batch'), fmt)

    def test_new_styles_and_script_load_once(self):
        html=(ROOT/'dist/index.html').read_text()
        for file in ('assets/portal.js','assets/portal.css'):
            self.assertEqual(html.count(file), 1)
        self.assertIn('id="portalSearch"', html)
        self.assertIn('aria-label="Atalhos no celular"', html)

    def test_all_portal_destinations_remain_in_html(self):
        html=(ROOT/'dist/index.html').read_text()
        for id in ('inicio','pesquisa','acervo','midiateca','comparacoes','apuracoes','documentos','noticias','fontes','cobertura','correcoes','metodologia'):
            self.assertIn('id="'+id+'"', html)
            self.assertIn('href="#'+id+'"', html)
        ids=re.findall(r'\bid="([^"]+)"',html)
        self.assertEqual(len(ids),len(set(ids)))

    def test_sensitive_approval_gate_was_not_relaxed(self):
        data=json.loads((ROOT/'content/acervo.editorial.json').read_text())
        self.assertEqual(data['metadata']['approvedReviewerIds'], [])
        self.assertEqual(len(data['records']), 71)
        app=(ROOT/'dist/assets/app.js').read_text()
        self.assertIn("item.review?.state==='approved'",app)
        self.assertIn('approvedReviewerIds||[]',app)

    def test_input_records_remain_pending(self):
        data=json.loads((ROOT/'content/research.json').read_text())
        for i in data['items']:
            self.assertIsNone(i['editorialClassification'])
            self.assertIsNone(i['review']['reviewer'])
        self.assertEqual(data['metrics']['reviewedAudioSeconds'],0)

    def test_chrome_sem_link_do_github_e_cta_local(self):
        html=(ROOT/'dist/index.html').read_text()
        self.assertNotIn('aria-label="Código e histórico no GitHub"',html)
        self.assertNotIn('class="sidebar-repository"',html)
        self.assertNotIn('>GitHub</a>',html)
        self.assertIn('id="portalSearchJump"',html)
        self.assertIn('href="#metodologia" id="downloadPdf"',html)

    def test_link_documental_prioriza_origem_externa(self):
        js=(ROOT/'dist/assets/app.js').read_text()
        self.assertIn('if (/^(?:assets|documentos)\\//.test(local) && published) return published;',js)
        self.assertIn("const routePane=pane=>",js)
        self.assertIn("received=true;",js)
