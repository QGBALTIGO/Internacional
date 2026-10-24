#!/usr/bin/env python3
"""Build the Portuguese documentary dossier from the website's canonical data.

Usage:
  python build_pdf.py --data ../dist/data/acervo.json
  python build_pdf.py --data PATH --output PATH

Without --data, content/acervo.editorial.json is used. The released PDF is built
from the same canonical JSON as the website. No factual classifications are
inferred by this script. Paragraphs, references, indexes and contextual records
are measured and continued across pages without discarding editorial text.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from reportlab.lib.colors import HexColor, Color, white
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" if (ROOT / "dist").is_dir() else ROOT
DEFAULT_OUTPUT = DIST / "documentos" / "dossie-documental.pdf"
SITE = "https://arquivo-bolsonaro-fatos.copperkoala32.chatgpt.site"
W, H = 595.276, 841.89
M = 50
CW = W - 2 * M
PAPER = HexColor("#f5f3ed")
GREEN = HexColor("#1d302a")
ORANGE = HexColor("#bd432c")
MUTED = HexColor("#61665e")
LINE = HexColor("#d6d8cf")
SOFT = HexColor("#e8e9df")
AMBER = HexColor("#8c5b18")
PEOPLE = {"jair": "Jair Bolsonaro", "flavio": "Flávio Bolsonaro"}
BOTTOM = 77


def clean_text(value):
    """Keep prose readable in embedded fonts and use ordinary ASCII hyphens."""
    text = str(value or "")
    text = re.sub(r"[\u2010-\u2015\u2212]", "-", text)
    text = text.replace("\u00a0", " ").replace("\ufe0f", "")
    return re.sub(r"[\U0001f300-\U0001faff]", "", text)


def esc(value):
    return html.escape(clean_text(value), quote=True)


def short_date(value):
    if not value:
        return ""
    value = str(value)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return "/".join(reversed(value.split("-")))
    return value


def collection(value):
    """Accept flat lists, id-keyed dictionaries or media type dictionaries."""
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        result = []
        for key, item in value.items():
            if isinstance(item, list):
                result.extend(item)
            elif isinstance(item, dict):
                result.append({"id": key, **item})
        return result
    return []


def load_data(path):
    path = Path(path) if path else ROOT / "content" / "acervo.editorial.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("records"), list):
        raise ValueError("O JSON final deve conter uma lista em records.")
    return data


def register_fonts():
    root = Path("/usr/share/fonts/truetype/dejavu")
    for name, filename in [
        ("DV-Sans", "DejaVuSans.ttf"),
        ("DV-Sans-Bold", "DejaVuSans-Bold.ttf"),
        ("DV-Serif", "DejaVuSerif.ttf"),
        ("DV-Serif-Bold", "DejaVuSerif-Bold.ttf"),
    ]:
        pdfmetrics.registerFont(TTFont(name, str(root / filename)))
    pdfmetrics.registerFontFamily("DV-Sans", normal="DV-Sans", bold="DV-Sans-Bold")
    pdfmetrics.registerFontFamily("DV-Serif", normal="DV-Serif", bold="DV-Serif-Bold")


class Dossier:
    def __init__(self, data, output):
        self.data = data
        self.records = data["records"]
        self.media = collection(data.get("media"))
        self.documents = collection(data.get("documents"))
        self.images = collection(data.get("images"))
        self.comparisons = collection(data.get("comparisons"))
        self.investigations = collection(data.get("investigations"))
        self.all_assets = {a.get("id"): a for a in self.media + self.documents + self.images}
        self.meta = data.get("metadata", {})
        self.revision = short_date(self.meta.get("reviewedAt") or self.meta.get("revisionDate") or self.meta.get("updatedAt") or "2026-10-23")
        self.edition = str(self.meta.get("edition") or "02").zfill(2)
        self.site_url = self.meta.get("siteUrl") or SITE
        self.page = 0
        self.sections = []
        self.link_count = 0
        self.flow_section = "Acervo documental"
        self.flow_title = ""
        self.current_record = None
        self.record_pages = {}
        output.parent.mkdir(parents=True, exist_ok=True)
        self.c = canvas.Canvas(str(output), pagesize=(W, H), pageCompression=1)
        self.c.setTitle("Arquivo Bolsonaro | Declarações e documentos")
        self.c.setAuthor("Arquivo Bolsonaro | Curadoria documental")
        self.c.setSubject("Declarações verificadas, contexto, fontes e materiais públicos. Curadoria não exaustiva.")
        self.c.setKeywords("checagem, fontes, Jair Bolsonaro, Flávio Bolsonaro, documentação")
        self.c.setCreator("Arquivo Bolsonaro | ReportLab")

    def paragraph(self, text, width=CW, size=10.5, leading=16, color=GREEN, font="DV-Sans", raw=False):
        style = ParagraphStyle(
            "p", fontName=font, fontSize=size, leading=leading,
            textColor=color, alignment=TA_LEFT, spaceAfter=0,
            splitLongWords=True, allowWidows=0, allowOrphans=0,
        )
        para = Paragraph(clean_text(text) if raw else esc(text), style)
        para.wrap(width, H)
        return para

    def measure(self, text, width=CW, size=10.5, leading=16, color=GREEN, font="DV-Sans", raw=False):
        return self.paragraph(text, width, size, leading, color, font, raw).wrap(width, H)[1]

    def continuation(self):
        section, title = self.flow_section, self.flow_title
        y = self.page_start(section, continued=True)
        self.small("CONTINUAÇÃO", M, y, ORANGE, 7.5)
        y -= 18
        if title:
            y = self.p(title, M, y, CW, 17, 22, GREEN, "DV-Serif") - 13
        self.rule(y)
        return y - 20

    def ensure(self, y, required=90):
        if y - required < BOTTOM:
            return self.continuation()
        return y

    def p(self, text, x, y, width=CW, size=10.5, leading=16, color=GREEN, font="DV-Sans", raw=False):
        """Draw a paragraph, splitting only when it exceeds one page's frame."""
        para = self.paragraph(text, width, size, leading, color, font, raw)
        _, height = para.wrap(width, H)
        if y - height >= BOTTOM or self.page == 1:
            para.drawOn(self.c, x, y-height)
            return y-height
        # A paragraph that fits a fresh frame stays together. Very long prose
        # uses ReportLab's line-aware split; the remainder is never truncated.
        fresh_space = H - 165 - BOTTOM
        if height <= fresh_space:
            y = self.continuation()
            if y - height >= BOTTOM:
                para.drawOn(self.c, x, y-height)
                return y-height
        pending = [para]
        while pending:
            para = pending.pop(0)
            _, height = para.wrap(width, H)
            available = y - BOTTOM
            if height <= available:
                para.drawOn(self.c, x, y-height)
                y -= height
                continue
            parts = para.split(width, available)
            if not parts:
                y = self.continuation()
                pending.insert(0, para)
                continue
            first, rest = parts[0], parts[1:]
            _, used = first.wrap(width, H)
            first.drawOn(self.c, x, y-used)
            y -= used
            if rest:
                y = self.continuation()
                pending = rest + pending
        return y

    def small(self, text, x, y, color=MUTED, size=8):
        self.c.setFont("DV-Sans", size)
        self.c.setFillColor(color)
        self.c.drawString(x, y, clean_text(text))

    def rule(self, y, x=M, width=CW, color=LINE):
        self.c.setStrokeColor(color)
        self.c.setLineWidth(.6)
        self.c.line(x, y, x+width, y)

    def label(self, text, y, x=M, color=ORANGE):
        y = self.ensure(y, 65)
        self.small(text.upper(), x, y, color, 8)
        return y-14

    def labeled_text(self, title, body, y, size=10, leading=15.5, color=GREEN, label_color=ORANGE, font="DV-Sans", after=18):
        required=self.measure(body,CW,size,leading,color,font)+14+after
        y=self.ensure(y,min(required,H-290))
        y=self.label(title,y,color=label_color)
        return self.p(body,M,y,CW,size,leading,color,font)-after

    def page_start(self, section, bookmark=None, outline=None, cover=False, continued=False):
        if self.page:
            self.c.showPage()
        self.page += 1
        if not continued:
            self.flow_section = section
            self.flow_title = ""
        self.c.setFillColor(PAPER)
        self.c.rect(0, 0, W, H, fill=1, stroke=0)
        if bookmark:
            self.c.bookmarkPage(bookmark)
        if outline and bookmark:
            self.c.addOutlineEntry(outline, bookmark, level=0, closed=False)
        if not cover:
            self.small("ARQUIVO BOLSONARO", M, H-36, GREEN, 8)
            self.c.setFont("DV-Sans", 7.5)
            self.c.setFillColor(MUTED)
            self.c.drawRightString(W-M, H-36, clean_text(section.upper()))
            self.rule(H-48)
            self.rule(42)
            self.small(f"EDIÇÃO {self.edition}  /  REVISÃO {self.revision}", M, 27, MUTED, 7)
            self.c.setFont("DV-Sans", 8)
            self.c.drawRightString(W-M, 27, f"{self.page:02d}")
        self.sections.append({"page": self.page, "section": section, "bookmark": bookmark, "continued": continued})
        if self.current_record:
            self.record_pages.setdefault(self.current_record, []).append(self.page)
        return H-77

    def external_link(self, title, url, x, y, width=CW, size=9, leading=13, color=GREEN):
        if not str(url).startswith(("https://", "http://")):
            return self.p(title, x, y, width, size, leading, color)
        self.link_count += 1
        return self.p(f'<link href="{esc(url)}" color="{color.hexval()}">{esc(title)}</link>', x, y, width, size, leading, color, raw=True)

    def asset_path(self, item, fallback=None):
        for key in ("localPath", "path", "src", "thumbnailPath", "thumbnail"):
            value = item.get(key) if isinstance(item, dict) else None
            if value and not str(value).startswith(("https://", "http://")):
                p = Path(value)
                for candidate in (p, DIST / str(p).lstrip("/"), ROOT / str(p).lstrip("/")):
                    if candidate.is_file():
                        return candidate
        if fallback and Path(fallback).exists():
            return Path(fallback)
        return None

    def clipped_image(self, path, x, y, width, height):
        if Path(path).suffix.lower() in (".jpg", ".jpeg"):
            # Preserve the original JPEG stream instead of expanding it into
            # a much larger lossless RGB stream inside the PDF.
            img = ImageReader(str(path))
        else:
            with Image.open(path) as source_image:
                img = ImageReader(source_image.convert("RGB"))
        iw, ih = img.getSize()
        scale = max(width/iw, height/ih)
        dw, dh = iw*scale, ih*scale
        self.c.saveState()
        clip = self.c.beginPath()
        clip.rect(x, y, width, height)
        self.c.clipPath(clip, stroke=0, fill=0)
        self.c.drawImage(img, x+(width-dw)/2, y+(height-dh)/2, dw, dh, mask="auto")
        self.c.restoreState()

    def cover(self):
        self.page_start("Capa", "capa", "Capa", True)
        self.c.setFillColor(GREEN)
        self.c.rect(0, H-104, W, 104, fill=1, stroke=0)
        self.small("ARQUIVO / MEMÓRIA PÚBLICA", M, H-50, PAPER, 8.5)
        self.c.setFillColor(ORANGE)
        self.c.rect(W-M-60, H-76, 60, 32, fill=1, stroke=0)
        self.small(f"ED. {self.edition}", W-M-49, H-64, white, 8.5)
        self.p("Arquivo\nBolsonaro".replace("\n", "<br/>"), M, H-136, CW, 46, 51, GREEN, "DV-Serif-Bold", raw=True)
        self.p("Declarações e documentos.", M, H-256, CW, 24, 31, ORANGE, "DV-Serif")
        self.p("Um acervo documental de declarações de Jair e Flávio Bolsonaro, com contexto, verificações e caminhos para a evidência original.", M, H-308, CW-8, 11.5, 18, GREEN)
        y = H-389
        self.rule(y)
        n_primary = len({s.get("url") for r in self.records for s in r.get("sources",[]) if s.get("type")=="primary"})
        counts = Counter(r.get("person") for r in self.records)
        stats = [(f"{len(self.records):02d}", "FICHAS DOCUMENTAIS"), (str(len({s.get('url') for r in self.records for s in r.get('sources',[])})), "FONTES REFERENCIADAS"), (f"{counts.get('jair', 0)} + {counts.get('flavio', 0)}", "JAIR + FLÁVIO")]
        for i,(number,label) in enumerate(stats):
            x = M+i*(CW/3)
            self.p(number, x, y-16, CW/3-12, 25, 29, GREEN, "DV-Serif")
            self.small(label, x, y-61, MUTED, 6.8)
        image_y, image_h = 110, 246
        gap = 12
        image_w = (CW-gap)/2
        for i,key in enumerate(("jair", "flavio")):
            im = next((x for x in self.images if x.get("person")==key), {})
            path = self.asset_path(im)
            if not path:
                path = next((p for p in (DIST / "assets" / f"{key}.webp", DIST / "assets" / f"{key}.jpg", Path(f"/tmp/bolsonaro_media/{key}-bolsonaro.jpg")) if p.is_file()), None)
            x = M+i*(image_w+gap)
            if path:
                self.clipped_image(path,x,image_y,image_w,image_h)
            self.c.setFillColor(GREEN)
            self.c.rect(x,image_y,image_w,27,fill=1,stroke=0)
            self.small(PEOPLE[key],x+11,image_y+9,PAPER,8.5)
        self.p("Curadoria não exaustiva. Classificações tratam do conteúdo verificável das afirmações, sem presumir intenção. Fotografias de identificação; créditos e condições de uso no fim.", M, 91, CW, 7.5, 11, MUTED)
        self.small(f"REVISÃO DOCUMENTAL  /  {self.revision}", M, 27, GREEN, 7.5)

    def methodology(self):
        y = self.page_start("Metodologia", "metodologia", "Metodologia")
        self.flow_title = "Como os registros entram no arquivo"
        y = self.label("Como ler este acervo", y)
        y = self.p("Critério antes\nda classificação.".replace("\n","<br/>"), M, y-5, CW, 27, 34, GREEN, "DV-Serif", raw=True)-22
        paragraphs = [
            ("Escopo e seleção", "Esta edição reúne uma seleção de declarações atribuídas nominalmente a Jair ou Flávio Bolsonaro e documentadas por fontes públicas. Não pretende enumerar todas as falas incorretas, medir a frequência de falsidades nem representar uma amostra estatística do discurso de qualquer pessoa."),
            ("O que cada ficha registra", "A formulação da alegação é uma paráfrase editorial, não uma transcrição literal. A ficha informa autoria, data ou intervalo conhecido, tema, contexto e fontes. Compartilhar conteúdo não equivale a produzi-lo; essa distinção deve ser preservada. Datas de declarações podem diferir das datas de publicação das checagens."),
            ("Falso", "A afirmação verificável é contrariada pelas evidências apresentadas nas fontes citadas."),
            ("Enganoso", "A apresentação omite contexto, mistura medidas ou usa um elemento verdadeiro de modo a sustentar conclusão inadequada."),
            ("Sem comprovação", "A acusação não foi sustentada por evidência verificável nas fontes consultadas. Ausência de comprovação não autoriza inventar prova negativa ou afirmar impossibilidade absoluta."),
            ("Limites e atualização", "As classificações se referem ao conteúdo e ao contexto documentados. Não demonstram, por si só, intenção de enganar. Reconhecimentos de erro e retificações identificados integram as fichas. Relatórios parlamentares, depoimentos e decisões judiciais devem ser lidos segundo sua natureza; nenhum deles substitui a verificação específica de uma afirmação."),
            ("Comparações e apurações", "Comparações apresentam falas sobre o mesmo tema com suas datas. Uma mudança de posição pode ser legítima; a análise precisa explicitar se há correção, incompatibilidade ou evolução do entendimento. A seção de apurações distingue reportagens, documentos, alegações, respostas e decisões. A abertura de investigação não equivale a condenação."),
            ("Uso dos materiais", "Fotografias identificam as pessoas. Reportagens e vídeos institucionais podem oferecer contexto, enquanto documentos e dados sustentam pontos específicos. Entrevistas completas não recebem classificação automática. O papel de cada material é indicado. Links externos dependem da disponibilidade dos respectivos provedores."),
        ]
        for title,body in paragraphs:
            y = self.ensure(y, self.measure(title, size=10.3, leading=15, font="DV-Sans-Bold") + self.measure(body, size=9.3, leading=14) + 17)
            y=self.p(title,M,y,CW,10.3,15,GREEN,"DV-Sans-Bold")-4
            y=self.p(body,M,y,CW,9.3,14,MUTED)-13
        self.rule(y+4)

    def overview(self):
        y = self.page_start("Guia de leitura", "guia", "Guia de leitura")
        self.flow_title = "Nesta edição"
        y = self.label(f"Edição {self.edition}", y)
        y = self.p("Declarações\ne documentos".replace("\n", "<br/>"), M, y-5, CW, 29, 36, GREEN, "DV-Serif", raw=True)-19
        y = self.p("O índice de cada pessoa leva às fichas. Comparações, apurações e materiais de apoio têm seções próprias. Os títulos abaixo também são navegáveis.", M, y, CW, 10, 16, MUTED)-24
        counts = Counter(r.get("person") for r in self.records)
        entries = [
            ("indice-jair", "Declarações de Jair Bolsonaro", f"{counts.get('jair',0)} fichas com autoria, contexto e referências."),
            ("indice-flavio", "Declarações de Flávio Bolsonaro", f"{counts.get('flavio',0)} fichas com autoria, contexto e referências."),
        ]
        if self.comparisons:
            entries.append(("comparacoes", "Entre falas", f"{len(self.comparisons)} comparações datadas, com análise e fontes."))
        if self.investigations:
            entries.append(("apuracoes", "Apurações e documentos", f"{len(self.investigations)} episódio(s) com cronologia, procedência e respostas."))
        entries += [
            ("documentos", "Documentos de referência", f"{len(self.documents)} relatórios, decisões e outros documentos para consulta."),
            ("creditos", "Imagens, vídeos e áudios", f"{len(self.media)} registros multimídia, além das imagens de identificação."),
            ("notas", "Notas editoriais e edição digital", "Data da revisão, alcance do documento e endereço do projeto."),
        ]
        for number,(target,title,description) in enumerate(entries,1):
            y = self.ensure(y, 70)
            oldy = y
            self.small(f"{number:02d}", M, y-11, ORANGE, 9)
            y = self.p(title, M+30, y, CW-30, 12, 17, GREEN, "DV-Sans-Bold")-5
            y = self.p(description, M+30, y, CW-30, 9, 14, MUTED)-15
            self.c.linkRect("", target, (M+28,y+8,W-M,oldy+3), relative=0, thickness=0)
            self.rule(y+6)

    def contents(self, key):
        items = [r for r in self.records if r.get("person")==key]
        y=self.page_start("Índice de fichas",f"indice-{key}",f"Índice: {PEOPLE[key]}")
        self.flow_title = f"Índice: {PEOPLE[key]}"
        y=self.label("Índice navegável",y)
        y=self.p(PEOPLE[key],M,y-5,CW,27,34,GREEN,"DV-Serif")-12
        y=self.p(f"{len(items)} registros. Selecione um título para abrir a ficha.",M,y,CW,9,14,MUTED)-20
        for r in items:
            num=self.records.index(r)+1
            date_topic = f"{r.get('dateLabel') or short_date(r.get('statementDate')) or r.get('year','')}  /  {r.get('topic','')}"
            required = self.measure(r.get("title", ""), CW-90, 10, 14, font="DV-Sans-Bold") + self.measure(date_topic, CW-30, 7.3, 11) + 20
            y = self.ensure(y, required)
            self.small(f"{num:02d}",M,y-11,ORANGE,9)
            oldy=y
            y=self.p(r.get("title", ""),M+30,y,CW-90,10,14,GREEN,"DV-Sans-Bold")
            self.c.linkRect("",r["id"],(M+28,y-2,W-M,oldy+3),relative=0,thickness=0)
            y=self.p(date_topic,M+30,y-4,CW-30,7.3,11,MUTED)-12
            self.rule(y+4)
        y = self.ensure(y, 42)
        self.p("As datas correspondem às declarações ou ao período conhecido, não necessariamente à publicação das fontes.",M,y-13,CW,7.5,11,MUTED)

    def source_row(self, source, index, y):
        label = {"primary":"FONTE PRIMÁRIA", "factcheck":"CHECAGEM", "reporting":"REPORTAGEM"}.get(source.get("type"), "REGISTRO / REFERÊNCIA")
        publisher = source.get("publisher") or source.get("name") or "Fonte"
        d = short_date(source.get("date"))
        metadata = f"{publisher}  /  {label}"+(f"  /  {d}" if d else "")
        title = source.get("title") or source.get("url") or "Fonte"
        required = self.measure(metadata, CW-27, 7.1, 10.5) + self.measure(title, CW-27, 9, 13) + 26
        y = self.ensure(y, required)
        self.small(f"{index:02d}",M,y-10,ORANGE,8)
        x=M+27
        y=self.p(metadata,x,y,CW-27,7.1,10.5,MUTED)
        y=self.external_link(title,source.get("url"),x,y-3,CW-27,9,13)
        host=urlparse(source.get("url","")).netloc
        y=self.p(host+"  ·  abrir fonte",x,y-3,CW-27,7,10,MUTED)-10
        return y

    def note_box(self, title, body, y, source_url=None):
        """Render an editorial qualification without silently omitting it."""
        text_h=self.measure(body,CW-26,8.6,13)
        box_h=text_h+37+(15 if source_url else 0)
        if box_h > H-300:
            y=self.label(title,y,color=GREEN)
            y=self.p(body,M,y,CW,8.6,13,GREEN)-10
            if source_url:
                y=self.external_link("Consultar o registro",source_url,M,y,CW,7.2,10.5,GREEN)-15
            return y
        y=self.ensure(y,box_h+15)
        self.c.setFillColor(SOFT)
        self.c.rect(M,y-box_h,CW,box_h,fill=1,stroke=0)
        self.c.setFillColor(GREEN)
        self.c.rect(M,y-box_h,2.5,box_h,fill=1,stroke=0)
        self.small(title.upper(),M+13,y-14,GREEN,7.2)
        yy=self.p(body,M+13,y-23,CW-26,8.6,13,GREEN)
        if source_url:
            self.external_link("Consultar o registro",source_url,M+13,yy-5,CW-26,7.2,10.5,GREEN)
        return y-box_h-15

    def record(self, item, index):
        person=PEOPLE.get(item.get("person"),item.get("person", ""))
        self.current_record = item["id"]
        y=self.page_start(f"Ficha {index+1:02d} / {person}",item["id"])
        self.flow_title = item.get("title", "")
        self.c.addOutlineEntry(f"{index+1:02d}. {item.get('title','')}",item["id"],level=0,closed=False)
        y=self.label(f"Ficha {index+1:02d}  /  {person}",y)
        y=self.p(item.get("title",""),M,y-8,CW,24,30,GREEN,"DV-Serif-Bold")-16
        verdict=item.get("verdict", "")
        color=ORANGE if verdict=="Falso" else AMBER if verdict=="Enganoso" else MUTED
        pillw=pdfmetrics.stringWidth(verdict,"DV-Sans-Bold",8.5)+24
        self.c.setFillColor(color)
        self.c.roundRect(M,y-22,pillw,24,3,fill=1,stroke=0)
        self.c.setFillColor(white)
        self.c.setFont("DV-Sans-Bold",8.5)
        self.c.drawString(M+12,y-14,verdict)
        datelabel=item.get("dateLabel") or short_date(item.get("statementDate")) or str(item.get("year", ""))
        self.p(f"{datelabel}  /  {item.get('topic','')}",M+pillw+13,y-4,CW-pillw-13,8.2,13,MUTED)
        y-=47
        y=self.labeled_text("A alegação · paráfrase",item.get("claim",""),y,11.3,17,font="DV-Serif",after=20)
        y=self.labeled_text("O que as fontes mostram",item.get("summary",""),y,10.1,15.5)
        if item.get("context"):
            y=self.labeled_text("Contexto e limites",item["context"],y,9.4,14.5,MUTED,MUTED,after=15)
        correction=item.get("correction")
        if isinstance(correction,dict) and correction.get("text"):
            title="Reconhecimento posterior"
            if correction.get("date"):
                title+=" · "+short_date(correction["date"])
            y=self.note_box(title,correction["text"],y,correction.get("sourceUrl"))
        elif isinstance(correction,str) and correction:
            y=self.note_box("Reconhecimento posterior",correction,y)
        for field,title in (("classificationNote","Sobre a classificação"),("caveat","Ressalva"),("editorialNote","Nota editorial")):
            if isinstance(item.get(field),str) and item[field]:
                y=self.note_box(title,item[field],y)
        y=self.ensure(y,115)
        self.rule(y+2)
        y=self.label("Referências clicáveis",y-17)
        for num,source in enumerate(item.get("sources",[]),1):
            y=self.source_row(source,num,y)
        materials=item.get("media") or item.get("relatedMedia") or []
        for item0 in materials:
            if isinstance(item0,str):
                item0=self.all_assets.get(item0,{})
            if isinstance(item0,dict) and item0.get("url"):
                y=self.ensure(y,65)
                self.small("MATERIAL ASSOCIADO",M,y-3,MUTED,7)
                y=self.external_link(item0.get("title","Material associado"),item0["url"],M,y-12,CW,8,12)-4
                if item0.get("role"):
                    y=self.p(f"Papel do material: {item0['role']}",M,y,CW,7.2,10.5,MUTED)
                y-=12
        self.small(f"ID: {item['id']}",M,63,MUTED,6.4)
        self.c.setFont("DV-Sans",7)
        self.c.setFillColor(GREEN)
        self.c.drawRightString(W-M,63,"Voltar ao índice")
        key=item.get("person","jair")
        self.c.linkRect("",f"indice-{key}",(W-M-84,58,W-M,73),relative=0,thickness=0)
        self.current_record = None

    def comparisons_section(self):
        if not self.comparisons:
            return
        for number, item in enumerate(self.comparisons, 1):
            bookmark = item.get("id") or f"comparacao-{number}"
            y=self.page_start("Entre falas",bookmark, f"Comparação {number:02d}: {item.get('title','')}")
            if number == 1:
                self.c.bookmarkPage("comparacoes")
            self.flow_title = item.get("title", "Comparação de declarações")
            y=self.label(f"Comparação {number:02d}  /  {item.get('category','Registros datados')}",y)
            y=self.p(self.flow_title,M,y-7,CW,25,31,GREEN,"DV-Serif-Bold")-18
            for field, caption in (("first","Primeiro registro"),("second","Segundo registro")):
                entry=item.get(field) or {}
                if not isinstance(entry,dict):
                    continue
                when=entry.get("dateLabel") or short_date(entry.get("date"))
                y=self.labeled_text(caption+("  /  "+when if when else ""),entry.get("summary") or entry.get("text") or entry.get("claim") or "",y,12,18,font="DV-Serif",after=9)
                if entry.get("sourceUrl"):
                    y=self.external_link("Consultar a fonte deste registro",entry["sourceUrl"],M,y,CW,8,12,ORANGE)-17
            for field, caption in (("analysis","Análise da comparação"),("context","Contexto e limites")):
                if item.get(field):
                    y=self.labeled_text(caption,item[field],y,label_color=MUTED)
            if item.get("sources"):
                y=self.ensure(y,115)
                y=self.label("Referências clicáveis",y)
                for i,source in enumerate(item["sources"],1):
                    y=self.source_row(source,i,y)
            y=self.ensure(y,35)
            self.p("Categoria própria de comparação. O contraste entre registros não atribui automaticamente falsidade a todas as falas nem comprova intenção.",M,y-5,CW,8,12,MUTED)

    def investigations_section(self):
        if not self.investigations:
            return
        for number,item in enumerate(self.investigations,1):
            bookmark=item.get("id") or f"apuracao-{number}"
            y=self.page_start("Apurações e documentos",bookmark,f"Apuração: {item.get('title','')}")
            if number == 1:
                self.c.bookmarkPage("apuracoes")
            self.flow_title=item.get("title","Documentação de um episódio")
            y=self.label(f"Episódio {number:02d}  /  documentação de contexto",y)
            y=self.p(self.flow_title,M,y-7,CW,26,32,GREEN,"DV-Serif-Bold")-19
            if item.get("status"):
                y=self.note_box("Situação na revisão",item["status"],y)
            for field,caption in (("summary","O que está documentado"),("context","Contexto"),("response","Resposta dos envolvidos"),("limitations","Limites da documentação")):
                if item.get(field):
                    y=self.labeled_text(caption,item[field],y,label_color=ORANGE if field=="summary" else MUTED)
            provenance=item.get("provenance") or []
            if provenance:
                y=self.ensure(y,130)
                y=self.label("Procedência dos materiais",y)
                for entry in provenance:
                    y=self.ensure(y,100)
                    y=self.p(entry.get("material") or "Material",M,y,CW,10.3,15,GREEN,"DV-Sans-Bold")-5
                    if entry.get("publisher"):
                        y=self.p(entry["publisher"],M,y,CW,8,12,MUTED)-5
                    y=self.p(entry.get("description") or "",M,y,CW,9.3,14.5,MUTED)-7
                    if entry.get("sourceUrl"):
                        y=self.external_link("Abrir a publicação ou o documento",entry["sourceUrl"],M,y,CW,8,12,ORANGE)-17
            timeline=item.get("timeline") or []
            if timeline:
                y=self.ensure(y,145)
                y=self.label("Cronologia documentada",y)
                for entry in timeline:
                    date_label=entry.get("dateLabel") or short_date(entry.get("date"))
                    title=entry.get("title") or "Registro"
                    body=entry.get("text") or entry.get("summary") or ""
                    required=self.measure(title,CW,10.3,15,font="DV-Sans-Bold")+self.measure(body,CW,9.3,14.5)+61
                    y=self.ensure(y,required)
                    self.small(date_label,M,y-8,ORANGE,8)
                    y=self.p(title,M,y-21,CW,10.3,15,GREEN,"DV-Sans-Bold")-6
                    y=self.p(body,M,y,CW,9.3,14.5,MUTED)-7
                    if entry.get("sourceUrl"):
                        y=self.external_link("Consultar fonte do acontecimento",entry["sourceUrl"],M,y,CW,8,12,ORANGE)-18
                    self.rule(y+6)
            if item.get("sources"):
                y=self.ensure(y,115)
                y=self.label("Referências clicáveis",y)
                for i,source in enumerate(item["sources"],1):
                    y=self.source_row(source,i,y)

    def resource_item(self,item,y,index):
        title=item.get("title") or item.get("name") or "Material público"
        publisher=item.get("credit") or item.get("publisher") or "Instituição identificada na fonte"
        detail=item.get("dateLabel") or short_date(item.get("date"))
        if item.get("pages"):
            detail+=f"  /  {item['pages']} páginas"
        duration=item.get("durationLabel")
        if not duration and isinstance(item.get("durationSeconds"),(int,float)):
            seconds=round(item["durationSeconds"])
            duration=f"{seconds//3600:02d}:{seconds%3600//60:02d}:{seconds%60:02d}" if seconds>=3600 else f"{seconds//60:02d}:{seconds%60:02d}"
        if duration:
            detail+=f"  /  {duration}"
        metadata=publisher+("  /  "+detail if detail else "")
        description=item.get("description") or item.get("notes") or ""
        role=item.get("role")
        required=self.measure(f"{index:02d}  {title}",CW,11,16,font="DV-Sans-Bold")+self.measure(metadata,CW,8,12)+45
        if description:
            required+=self.measure(description,CW,8.5,13)+5
        if role:
            required+=self.measure(f"Papel no acervo: {role}",CW,7.5,11)+5
        if item.get("license"):
            required+=self.measure(f"Condição de uso: {item['license']}",CW,7.3,11)+4
        required+=16*sum(bool(item.get(k)) for k in ("sourceUrl","url","licenseUrl","transcriptUrl"))
        y=self.ensure(y,min(required,H-230))
        y=self.p(f"{index:02d}  {title}",M,y,CW,11,16,GREEN,"DV-Sans-Bold")-5
        y=self.p(metadata,M,y,CW,8,12,MUTED)-5
        if role:
            y=self.p(f"Papel no acervo: {role}",M,y,CW,7.5,11,GREEN)-5
        if description:
            y=self.p(description,M,y,CW,8.5,13,MUTED)-5
        if item.get("license"):
            y=self.p(f"Condição de uso: {item['license']}",M,y,CW,7.3,11,MUTED)-4
        url=item.get("sourceUrl") or item.get("url")
        if url:
            y=self.external_link("Abrir fonte e metadados",url,M,y,CW,8.2,12,ORANGE)-4
        if item.get("url") and item["url"]!=url:
            y=self.external_link("Abrir o registro original",item["url"],M,y,CW,8.2,12,ORANGE)-4
        if item.get("transcriptUrl"):
            y=self.external_link("Consultar transcrição publicada pela fonte",item["transcriptUrl"],M,y,CW,7.3,11,MUTED)-4
        elif item.get("transcriptAvailable") is False and item.get("type")=="audio":
            y=self.p("A fonte oferece resumo. Transcrição integral não identificada nesta revisão.",M,y,CW,7.3,11,MUTED)-4
        if item.get("licenseUrl"):
            y=self.external_link("Consultar condições de uso",item["licenseUrl"],M,y,CW,7.3,11,MUTED)-4
        self.rule(y-6)
        return y-24

    def resources(self):
        y=self.page_start("Documentação de apoio","documentos","Documentos de referência")
        self.flow_title="Documentos de referência"
        y=self.label("Acervo de apoio",y)
        y=self.p("Documentos\nde referência".replace("\n","<br/>"),M,y-4,CW,26,32,GREEN,"DV-Serif",raw=True)-12
        y=self.p("Documentos institucionais para consulta aprofundada. Sua natureza e seu alcance são distintos; a presença no acervo não equivale a uma conclusão sobre todas as falas.",M,y,CW,9,14,MUTED)-19
        for i,item in enumerate(self.documents,1):
            y=self.resource_item(item,y,i)

        asset_items=self.images+self.media
        y=self.page_start("Créditos multimídia","creditos","Créditos multimídia")
        self.flow_title="Imagens, vídeos e áudios"
        y=self.label("Autoria e procedência",y)
        y=self.p("Imagens, vídeos\ne áudios".replace("\n","<br/>"),M,y-4,CW,26,32,GREEN,"DV-Serif",raw=True)-12
        y=self.p("Os materiais mantêm suas autorias originais. O uso neste acervo não implica apoio dos autores ou das instituições às escolhas editoriais. Consulte cada fonte para o contexto integral.",M,y,CW,9,14,MUTED)-21
        for i,item in enumerate(asset_items,1):
            y=self.resource_item(item,y,i)

        y=self.page_start("Notas editoriais","notas","Notas e edição digital")
        self.flow_title="Notas editoriais e edição digital"
        y=self.label(f"Edição {self.edition}",y)
        y=self.p("Um acervo aberto\nà verificação.".replace("\n","<br/>"),M,y-5,CW,27,34,GREEN,"DV-Serif",raw=True)-24
        y=self.p("Este documento foi organizado para tornar possível conferir cada registro, localizar a fonte e reconhecer os limites da conclusão. O leitor pode discordar de uma classificação e examinar a evidência que a sustenta.",M,y,CW,11,17,GREEN)-22
        y=self.p("As fontes originais têm precedência sobre a síntese editorial. Páginas podem mudar, ser corrigidas ou deixar de existir. Registros e materiais foram reunidos na revisão indicada; o documento não implica monitoramento contínuo nem verificação de todos os eventos posteriores.",M,y,CW,10.5,16,MUTED)-22
        y=self.p("Correções devem preservar a formulação anterior, explicar a alteração e indicar a nova evidência. A retirada de uma postagem não prova, isoladamente, falsidade; o reconhecimento explícito de erro deve permanecer associado ao registro.",M,y,CW,10.5,16,MUTED)-22
        self.rule(y)
        y=self.label("Edição digital · endereço do projeto",y-23)
        y=self.external_link(self.site_url,self.site_url,M,y,CW,9,14,GREEN)-10
        y=self.p("Este endereço identifica a edição digital do projeto. A disponibilidade dos registros e dos conteúdos externos depende dos respectivos publicadores. O acompanhamento de notícias pode receber novas publicações entre as revisões deste PDF.",M,y,CW,9,14,MUTED)-24
        y=self.label("Identificação desta edição",y)
        investigation_label="apuração" if len(self.investigations)==1 else "apurações"
        y=self.p(f"Arquivo Bolsonaro | Declarações e documentos\nEdição {self.edition} · revisão documental em {self.revision}\n{len(self.records)} fichas, {len(self.comparisons)} comparações, {len(self.investigations)} {investigation_label} e {len(self.media)} registros multimídia.\nCuradoria não exaustiva.".replace("\n","<br/>"),M,y,CW,10,16,GREEN,raw=True)

    def build(self):
        ids=[r.get("id") for r in self.records]
        if len(ids)!=len(set(ids)) or any(not x for x in ids):
            raise ValueError("Os registros precisam de ids únicos e não vazios.")
        for r in self.records:
            if not r.get("sources"):
                raise ValueError(f"Registro sem fonte: {r['id']}")
        self.cover()
        self.methodology()
        self.overview()
        for key in ("jair", "flavio"):
            self.contents(key)
        for index,item in enumerate(self.records):
            self.record(item,index)
        self.comparisons_section()
        self.investigations_section()
        self.resources()
        self.c.save()
        return {"pages":self.page,"records":len(self.records),"comparisons":len(self.comparisons),"investigations":len(self.investigations),"media":len(self.media),"documents":len(self.documents),"externalLinks":self.link_count,"sections":self.sections,"recordPages":self.record_pages}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data",type=Path,help="JSON canônico do site, incluindo records, media, comparisons e investigations")
    parser.add_argument("--output",type=Path,default=DEFAULT_OUTPUT)
    args=parser.parse_args()
    register_fonts()
    dossier=Dossier(load_data(args.data),args.output)
    result=dossier.build()
    result["output"]=str(args.output)
    result["dataSource"]=str(args.data) if args.data else str(ROOT/"content"/"acervo.editorial.json")
    result["bytes"]=args.output.stat().st_size
    qa_dir=ROOT/"qa"/"pdf"
    qa_dir.mkdir(parents=True,exist_ok=True)
    (qa_dir/"manifest.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ("sections","recordPages")},ensure_ascii=False))


if __name__=="__main__":
    main()
