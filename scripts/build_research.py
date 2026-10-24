#!/usr/bin/env python3
"""Normaliza lotes de pesquisa sem publicar conclusões editoriais.

Os inputs são checkpoints próprios de pesquisa, não páginas executáveis. A saída
serve ao catálogo e preserva nulos, autoria, origem e níveis reais de acesso.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import unicodedata
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'content' / 'research-input'
STAGES = ('encontrado', 'acessado', 'analisado', 'revisado', 'publicado')
FORMATS = {'documento', 'video', 'audio', 'checagem', 'reportagem', 'registro'}


def norm(text):
    return ''.join(c for c in unicodedata.normalize('NFD', str(text or '').lower())
                   if unicodedata.category(c) != 'Mn')


def stable_id(prefix, value):
    return prefix + '-' + sha256(str(value).encode()).hexdigest()[:16]


def canonical_url(value):
    try:
        u = urlsplit(str(value or '').strip())
        if u.scheme != 'https' or not u.hostname or u.username or u.password:
            return None
        if u.port and u.port != 443:
            return None
        query = [(k, v) for k, v in parse_qsl(u.query, keep_blank_values=True)
                 if not k.lower().startswith('utm_') and k.lower() not in {'fbclid', 'gclid'}]
        return urlunsplit(('https', u.netloc.lower(), u.path or '/', urlencode(query), ''))
    except ValueError:
        return None


def text(value):
    if isinstance(value, list):
        return '; '.join(text(v) for v in value if v)
    if isinstance(value, dict):
        return '; '.join(f'{k}: {text(v)}' for k, v in value.items() if v is not None)
    return str(value or '').replace('\u2014', ',')


def get_first(row, *keys):
    for key in keys:
        if row.get(key) is not None and row.get(key) != '':
            return row[key]
    return None


def date_value(value):
    if not value:
        return None
    s = str(value)
    if re.fullmatch(r'\d{4}(?:-\d{2})?(?:-\d{2})?', s):
        return s
    if re.match(r'^\d{4}-\d{2}-\d{2}T', s):
        return s[:10]
    return None


def stage_for(row):
    # Uma leitura feita pela automação não é revisão editorial humana.
    status = norm(get_first(row, 'stage', 'analysis_status', 'access_status', 'access_state', 'status'))
    if any(k in status for k in ('not_accessed', 'fetch_failed', 'found_', 'blocked')):
        return 'encontrado'
    if row.get('access_status') == 'metadata_only' or 'metadata' in status:
        return 'acessado'
    if any(k in status for k in ('analisado', 'documentary_read', 'texto_lido', 'text_read', '_analyzed')):
        return 'analisado'
    if any(k in status for k in ('accessed', 'acessado', 'catalogado', 'catalogued')):
        return 'acessado'
    # Explicit source evidence of page access, without inferring playback.
    if get_first(row, 'accessed_at', 'accessedAt', 'collected_at') or row.get('accessed') is True:
        return 'acessado'
    return 'encontrado'


def format_for(row, batch):
    f = norm(get_first(row, 'format', 'type', 'kind', 'material_type'))
    if f in FORMATS:
        return f
    if f in {'audio', 'podcast_audio'} or f.startswith('audio'):
        return 'audio'
    if f in {'video', 'podcast', 'entrevista', 'debate', 'live'} or 'video' in f:
        return 'video'
    if f in {'checagem', 'fact-check', 'factcheck'}:
        return 'checagem'
    if f in {'reportagem', 'noticia', 'notícia'}:
        return 'reportagem'
    if f in {'registro', 'registro publico', 'registro público'}:
        return 'registro'
    if any(k in f for k in ('pdf', 'document', 'proposicao', 'pronunciamento', 'votacao', 'decisao', 'taquigraf', 'transcript')):
        return 'documento'
    if batch == 'checagens':
        publisher = norm(get_first(row, 'source', 'publisher', 'institution'))
        return 'checagem' if any(k in publisher for k in ('fatos', 'lupa', 'checamos', 'comprova')) else 'reportagem'
    return 'registro'


def infer_publisher(row, url):
    explicit = get_first(row, 'publisher', 'source', 'institution', 'channel', 'canal', 'program')
    if isinstance(explicit, dict):
        explicit = get_first(explicit, 'name', 'publisher', 'title')
    if explicit:
        return text(explicit)
    host = urlsplit(url).hostname
    if host == 'noticias-stf-wp-prd.s3.sa-east-1.amazonaws.com':
        return 'Supremo Tribunal Federal'
    for suffix, label in (
        ('senado.leg.br', 'Senado Federal'), ('alerj.rj.gov.br', 'ALERJ'),
        ('stf.jus.br', 'Supremo Tribunal Federal'), ('stj.jus.br', 'Superior Tribunal de Justiça'),
        ('tse.jus.br', 'Tribunal Superior Eleitoral'), ('camara.leg.br', 'Câmara dos Deputados'),
        ('ibge.gov.br', 'IBGE'), ('bcb.gov.br', 'Banco Central'),
        ('aosfatos.org', 'Aos Fatos'), ('agencialupa.org', 'Lupa'),
        ('checamos.afp.com', 'AFP Checamos'), ('projetocomprova.com.br', 'Projeto Comprova')):
        if host == suffix or host.endswith('.' + suffix):
            return label
    return host


def source_nature(publisher, url):
    host = urlsplit(url).hostname or ''
    if host == 'noticias-stf-wp-prd.s3.sa-east-1.amazonaws.com':
        return 'órgão público, repositório de notícias e documentos'
    if host.endswith(('.gov.br', '.leg.br', '.jus.br')):
        return 'órgão público'
    if any(k in norm(publisher) for k in ('aos fatos', 'lupa', 'checamos', 'comprova', 'fato ou fake')):
        return 'checagem jornalística'
    if host in {'youtube.com', 'www.youtube.com', 'youtu.be', 'open.spotify.com', 'podcasts.apple.com'}:
        return 'canal audiovisual'
    return 'imprensa ou publicador identificado'


def source_key(publisher, url):
    host = urlsplit(url).hostname or ''
    if host == 'noticias-stf-wp-prd.s3.sa-east-1.amazonaws.com':
        return 'stf.jus.br'
    for suffix in ('senado.leg.br', 'alerj.rj.gov.br', 'stf.jus.br', 'stj.jus.br', 'tse.jus.br', 'camara.leg.br', 'bcb.gov.br', 'ibge.gov.br'):
        if host == suffix or host.endswith('.' + suffix):
            return suffix
    return host.removeprefix('www.') + '|' + norm(publisher)


def duration_seconds(row):
    value = get_first(row, 'durationSeconds', 'duration_seconds', 'duration_seconds_known', 'duration')
    if isinstance(value, (int, float)) and value >= 0:
        return float(value)
    if isinstance(value, str):
        m = re.fullmatch(r'(\d{1,2}):(\d{2})(?::(\d{2}))?', value.strip())
        if m:
            nums = list(map(int, (p for p in m.groups() if p is not None)))
            return float(sum(n * 60 ** i for i, n in enumerate(reversed(nums))))
    # Um checkpoint oficial informa sua duração em redação própria, sem campo numérico.
    m = re.search(r'duração informada de (\d+)min(\d+)s', str(row.get('summary', '')))
    if m:
        return float(int(m[1]) * 60 + int(m[2]))
    return None


def build_payload(inputs, legacy=None, feeds=None, previous=None, history=None):
    legacy = legacy or {}
    feeds = feeds or {}
    if history is None:
        history = previous.get('history', []) if previous else []
    legacy_urls = defaultdict(set)
    for collection in ('records', 'media', 'documents', 'comparisons', 'investigations'):
        for record in legacy.get(collection, []):
            for u in [record.get('url'), record.get('sourceUrl')] + [s.get('url') for s in record.get('sources', [])]:
                url = canonical_url(u)
                if url:
                    legacy_urls[url].add(record['id'])
    items_by_url, sources_by_key = {}, {}
    queries, failures, next_batch, references, raw_groups = [], [], [], [], []
    source_input_ids = {}
    for batch, payload in sorted(inputs.items()):
        if isinstance(payload, list):
            payload = {'records': payload}
        batch_stamp = get_first(payload, 'collected_at_utc', 'executed_at_utc', 'collected_at', 'generatedAt', 'collectedAt')
        raw_rows = []
        for collection in ('records', 'context_documents', 'items', 'media', 'documents', 'catalogue', 'unresolved_leads'):
            if isinstance(payload.get(collection), list):
                raw_rows.extend((collection, row) for row in payload[collection] if isinstance(row, dict))
        for collection, row in raw_rows:
            row = {**payload.get('defaults', {}), **row}
            url = canonical_url(get_first(row, 'url', 'sourceUrl', 'source_url', 'original_url'))
            if not url:
                continue
            publisher = infer_publisher(row, url)
            key = source_key(publisher, url)
            sid = stable_id('fonte', key)
            date = date_value(get_first(row, 'published_date', 'publication_date', 'date', 'publicationDate', 'publishedAt', 'recorded_date'))
            if date is None:
                date = date_value(get_first(row, 'event_date', 'recording_date'))
            topics = get_first(row, 'topics', 'themes', 'tags') or []
            if isinstance(topics, str):
                topics = [topics]
            topic = text(get_first(row, 'topic') or (topics[0] if topics else 'Atividade pública'))
            stage = stage_for(row)
            limitations = text(get_first(row, 'limitations', 'limitation', 'accessNote', 'access_note', 'use'))
            if collection == 'context_documents':
                limitations = (limitations + ' Documento de contexto; a relação com uma afirmação exige apuração específica.').strip()
            summary = text(get_first(row, 'summary', 'description', 'resumo'))
            locator = text(get_first(row, 'locator', 'localizador', 'precise_locator', 'transcript_locator')) or None
            row_id = get_first(row, 'id') or stable_id('input', url)
            item_id = stable_id('pesquisa', url)
            source_input_ids[(batch, str(row_id))] = item_id
            collected = get_first(row, 'accessed_at', 'collected_at', 'collectedAt', 'accessedAt') or batch_stamp
            item = {
                'id': item_id, 'title': text(get_first(row, 'title', 'titulo')) or 'Registro público',
                'url': url, 'publisher': publisher, 'date': date,
                'eventDate': date_value(get_first(row, 'event_date', 'recording_date', 'recorded_date')),
                'year': int(date[:4]) if date else None,
                'datePrecision': 'day' if date and len(date) == 10 else 'month' if date and len(date) == 7 else 'year' if date else 'unknown',
                'format': format_for(row, batch), 'topic': topic, 'topics': topics,
                'stage': stage, 'summary': summary, 'limitations': limitations,
                'locator': locator, 'sourceId': sid,
                'review': {'state': 'aguardando revisão editorial', 'reviewer': None, 'reviewedAt': None},
                'statementId': None, 'statementCandidateId': None,
                'transcript': {'method': text(get_first(row, 'transcript_method', 'transcription_method')) or None,
                               'state': 'transcrição oficial consultada, áudio não conferido' if 'transcript' in norm(row.get('kind')) else 'áudio não conferido',
                               'text': None, 'excerpt': get_first(row, 'short_quote'), 'startSeconds': None, 'endSeconds': None},
                'durationSeconds': duration_seconds(row), 'collectedAt': collected,
                'lastModifiedAt': collected, 'editorialClassification': None,
                'sourceConclusion': get_first(row, 'source_conclusion', 'sourceConclusion'),
                'factualQuestion': get_first(row, 'factual_question', 'factualQuestion'),
                'publicResponse': get_first(row, 'public_response', 'response'),
                'actor': get_first(row, 'speaker', 'author', 'person'),
                'literalQuote': get_first(row, 'quote', 'short_quote'),
                'platform': row.get('platform'), 'platformId': row.get('platform_id'),
                'mediaUrl': canonical_url(row.get('media_url')),
                'documentUrl': canonical_url(row.get('document_url')),
                'publicationTimeOriginal': row.get('publication_time_original'),
                'publicationTimezoneOriginal': row.get('publication_timezone_original'),
                'eventTimezoneOriginal': row.get('event_timezone_original'),
                'documentNumber': get_first(row, 'document_number', 'documentNumber'),
                'materialRole': 'contexto' if collection == 'context_documents' else 'material da apuração',
                'publicationState': 'catálogo de materiais, sem novo veredito',
                'legacyRecordIds': sorted(legacy_urls.get(url, set())),
                'researchOrigins': [{'batch': batch, 'inputId': str(row_id), 'toolReference': get_first(row, 'web_ref', 'ref')}],
                'accessMethod': text(get_first(row, 'access_method', 'method')) or text(payload.get('method')),
                'newToArchive': url not in legacy_urls,
            }
            # URL é identidade de material. Reabrir a mesma fonte não cria evidência independente.
            previous_item = items_by_url.get(url)
            if previous_item:
                previous_item['researchOrigins'].extend(item['researchOrigins'])
                previous_item['topics'] = sorted(set(previous_item['topics']) | set(topics))
                if STAGES.index(stage) > STAGES.index(previous_item['stage']):
                    for field in ('stage', 'summary', 'limitations', 'locator', 'accessMethod', 'collectedAt'):
                        previous_item[field] = item[field]
                if previous_item['durationSeconds'] is None:
                    previous_item['durationSeconds'] = item['durationSeconds']
            else:
                items_by_url[url] = item
            if key not in sources_by_key:
                parsed = urlsplit(url)
                sources_by_key[key] = {
                    'id': sid, 'name': publisher, 'url': urlunsplit((parsed.scheme, parsed.netloc, '/', '', '')),
                    'responsible': publisher, 'nature': source_nature(publisher, url),
                    'method': 'consulta pública e leitura do texto disponível',
                    'intervalMinutes': None, 'lastSuccessfulCollectionAt': None,
                    'lastConsultedAt': collected, 'accessNote': 'Acesso editorial registrado no lote; consultar as limitações de cada material.',
                    'status': 'consultada', 'sourceCount': 0, 'periods': [], 'formats': [],
                    'monitoringEnabled': False,
                }
            elif collected and (not sources_by_key[key]['lastConsultedAt'] or str(collected) > str(sources_by_key[key]['lastConsultedAt'])):
                sources_by_key[key]['lastConsultedAt'] = collected
        for value in payload.get('queries', payload.get('query_log', payload.get('research_log', []))):
            row = value if isinstance(value, dict) else {'query': str(value)}
            q = text(get_first(row, 'query', 'q', 'text'))
            if q:
                queries.append({'id': stable_id('consulta', batch + '|' + q), 'batch': batch, 'query': q,
                                'executedAt': get_first(row, 'executed_at', 'executed_date_utc') or batch_stamp,
                                'engine': row.get('engine'), 'interval': row.get('interval'),
                                'resultsState': row.get('result') or 'Ver materiais vinculados ao lote; ausência de resultado não demonstra inexistência.'})
        for row in payload.get('blocked', payload.get('access_failures', [])):
            failures.append({'batch': batch, **row} if isinstance(row, dict) else {'batch': batch, 'note': str(row)})
        for gap in payload.get('gaps', []) + payload.get('next_actions', []):
            next_batch.append({'id': stable_id('lacuna', text(gap)), 'note': text(gap), 'state': 'pendente', 'batch': batch})
        for row in payload.get('duplicate_groups', []):
            raw_groups.append((batch, row))
        for row in payload.get('references', []):
            if isinstance(row, dict):
                references.append(row)
    items = sorted(items_by_url.values(), key=lambda i: (i['date'] or '', i['id']), reverse=True)
    item_map = {i['id']: i for i in items}
    for source in sources_by_key.values():
        selected = [i for i in items if i['sourceId'] == source['id']]
        source['sourceCount'] = len(selected)
        accessed = [i for i in selected if STAGES.index(i['stage']) >= 1]
        source['accessedCount'] = len(accessed)
        source['analysedCount'] = sum(STAGES.index(i['stage']) >= 2 for i in selected)
        source['lastConsultedAt'] = max((i['collectedAt'] for i in accessed if i['collectedAt']), default=None)
        source['status'] = 'consultada' if accessed else 'localizada, acesso pendente'
        if not accessed:
            source['accessNote'] = 'Resultado localizado; o material ainda não foi acessado.'
        source['periods'] = sorted({i['year'] for i in selected if i['year'] is not None})
        source['formats'] = sorted({i['format'] for i in selected})
    # Somente notícias do coletor comprovam coleta recorrente. Consulta de pesquisa é campo separado.
    for feed in feeds.get('feeds', []):
        url = canonical_url(feed.get('url'))
        if not url:
            continue
        key = source_key(feed.get('name'), url)
        source = sources_by_key.setdefault(key, {
            'id': stable_id('fonte', key), 'name': feed.get('name'), 'url': url,
            'responsible': feed.get('name'), 'nature': source_nature(feed.get('name'), url),
            'lastConsultedAt': None, 'sourceCount': 0, 'periods': [], 'formats': [],
        })
        source.update({'method': 'RSS/Atom público', 'intervalMinutes': 60, 'monitoringEnabled': True,
                       'accessNote': feed.get('note') or 'Consultar histórico da coleta.',
                       'status': 'coleta com resultado' if feed.get('status') == 'ok' else 'falha de coleta',
                       'lastSuccessfulCollectionAt': feed.get('lastSuccessfulCheckAt') or feed.get('lastSuccessAt') or (feed.get('checkedAt') if feed.get('status') == 'ok' else None)})
    # Grupos são relações de pesquisa. Não resolvem, por si, autoria ou identidade de proposições.
    groups = []
    for batch, row in raw_groups:
        ids = [source_input_ids.get((batch, str(x))) for x in [row.get('primary_id')] + row.get('related', [])]
        ids = list(dict.fromkeys(i for i in ids if i in item_map))
        groups.append({'id': stable_id('grupo', batch + '|' + text(row.get('claim'))),
                       'type': 'candidato a repetição' if 'camisa' in norm(row.get('claim')) else 'mesmo núcleo de pesquisa',
                       'title': row.get('claim'), 'itemIds': ids, 'note': row.get('note'),
                       'state': 'aguardando revisão, sem equivalência factual automática'})
    statements = []
    for record in legacy.get('records', []):
        statements.append({'id': record['id'], 'normalizedClaim': record.get('claim'),
                           'literalQuote': None, 'person': record.get('person'),
                           'classification': record.get('verdict'), 'origin': 'edição anterior',
                           'review': {'state': 'herdada da edição anterior, sem nova revisão neste lote',
                                      'reviewer': None, 'reviewedAt': record.get('reviewedAt')},
                           'newInThisBatch': False})
    # As perguntas de pesquisa não são convertidas em falas literais nem novas checagens.
    candidates = [{'id': stable_id('proposicao-candidata', item['id']), 'mainId': None,
                   'itemId': item['id'], 'question': item['factualQuestion'],
                   'normalizedClaim': None, 'literalQuote': None, 'author': item['actor'],
                   'state': 'delimitação pendente', 'classification': None}
                  for item in items if item['factualQuestion']]
    for candidate in candidates:
        item_map[candidate['itemId']]['statementCandidateId'] = candidate['id']
    coverage = []
    for year in range(2003, 2027):
        selected = [i for i in items if i['year'] == year]
        counts = Counter(i['stage'] for i in selected)
        coverage.append({'year': year, 'found': len(selected), 'accessed': sum(STAGES.index(i['stage']) >= 1 for i in selected),
                         'analysed': sum(STAGES.index(i['stage']) >= 2 for i in selected), 'reviewed': 0, 'published': 0,
                         'stages': {s: counts[s] for s in STAGES},
                         'topics': dict(Counter(i['topic'] for i in selected)),
                         'sources': dict(Counter(i['sourceId'] for i in selected)),
                         'formats': dict(Counter(i['format'] for i in selected)),
                         'note': 'Recorte não exaustivo.' if selected else 'Lacuna de pesquisa neste lote; não demonstra inexistência de registros.'})
    media = []
    for item in items:
        if item['format'] not in {'video', 'audio'}:
            continue
        url = item['url']
        parsed = urlsplit(url)
        vid = item['platformId'] if item.get('platform') == 'youtube' else dict(parse_qsl(parsed.query)).get('v') if parsed.hostname in {'www.youtube.com', 'youtube.com'} else parsed.path.strip('/') if parsed.hostname == 'youtu.be' else None
        if vid and not re.fullmatch(r'[A-Za-z0-9_-]{11}', vid):
            vid = None
        media.append({'id': item['id'], 'title': item['title'], 'type': item['format'],
                      'provider': item['publisher'], 'publisher': item['publisher'],
                      'sourceUrl': url, 'url': url, 'date': item['date'], 'youtubeId': vid,
                      'description': item['summary'], 'people': ['flavio'], 'role': 'Material catalogado',
                      'durationSeconds': item['durationSeconds'], 'reviewState': 'aguardando revisão',
                      'verificationNote': 'Metadados catalogados. Áudio não ouvido nesta pesquisa. ' + item['limitations'],
                      'researchItemId': item['id'], 'review': item['review']})
    catalogued_seconds = sum(i['durationSeconds'] or 0 for i in items if i['format'] in {'video', 'audio'})
    metrics = {'newItems': sum(i['newToArchive'] for i in items), 'items': len(items),
               'alreadyInArchive': sum(not i['newToArchive'] for i in items),
               'accessed': sum(STAGES.index(i['stage']) >= 1 for i in items),
               'analysed': sum(STAGES.index(i['stage']) >= 2 for i in items),
               'reviewed': 0, 'publishedChecks': 0, 'distinctStatements': 0,
               'legacyStatements': len(statements), 'statementCandidates': len(candidates),
               'occurrencesConfirmed': 0, 'repetitionCandidates': len(groups),
               'sources': len(sources_by_key), 'sourcesConsulted': len({i['sourceId'] for i in items if STAGES.index(i['stage']) >= 1}),
               'video': sum(i['format'] == 'video' for i in items), 'audio': sum(i['format'] == 'audio' for i in items),
               'documents': sum(i['format'] == 'documento' for i in items),
               'mediaCataloguedSeconds': catalogued_seconds, 'reviewedAudioSeconds': 0,
               'transcribedMedia': 0, 'queryCount': len(queries), 'accessFailures': len(failures),
               'undatedItems': sum(i['year'] is None for i in items)}
    for note in ('Revisar autoria, pergunta e intervalo de cada afirmação antes de criar uma nova checagem.',
                 'Conferir no áudio original trechos decisivos; os segundos revisados neste lote são zero.',
                 'Explorar ALERJ de 2003 a 2015 por ano, mês e número de proposição.',
                 'Completar pedidos de esclarecimento como rascunhos, sem enviar mensagens.',
                 'Reabrir documentos posteriores a cada notícia judicial antes de informar situação processual atual.'):
        next_batch.append({'id': stable_id('lacuna', note), 'note': note, 'state': 'pendente', 'batch': 'consolidação'})
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    fingerprint = sha256(json.dumps({'inputs': inputs, 'history': history, 'normalizationVersion': 2}, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    generated = previous.get('metadata', {}).get('generatedAt') if previous and previous.get('metadata', {}).get('inputHash') == fingerprint else now
    result = {'schemaVersion': 1,
              'metadata': {'title': 'Catálogo de pesquisa de Flávio Bolsonaro', 'generatedAt': generated,
                           'inputHash': fingerprint, 'timezone': 'America/Campo_Grande',
                           'localDate': datetime.fromisoformat(generated.replace('Z', '+00:00')).astimezone(ZoneInfo('America/Campo_Grande')).date().isoformat(),
                           'scope': 'Materiais localizados e textos examinados; novos vereditos dependem de revisão editorial identificada.',
                           'rights': 'Resumos próprios, citações curtas e links. Não se republicam íntegras de terceiros.',
                           'audioReviewLimitation': 'Nenhum segundo de áudio foi conferido neste lote.',
                           'classificationPolicy': 'Conclusões de terceiros são atribuídas à fonte e não viram classificação própria.'},
              'items': items, 'sources': sorted(sources_by_key.values(), key=lambda s: s['name']), 'media': media,
              'events': [{'id': stable_id('evento', i['id']), 'itemId': i['id'], 'title': i['title'],
                          'date': i['eventDate'], 'datePrecision': 'unknown' if not i['eventDate'] else i['datePrecision'],
                          'context': i['summary'], 'state': 'identificação de evento pendente' if not i['eventDate'] else 'data informada pela fonte'} for i in items],
              'statements': statements, 'propositions': candidates, 'occurrences': [],
              'evidence': [{'id': stable_id('evidencia', i['id']), 'itemId': i['id'], 'sourceId': i['sourceId'],
                            'url': i['url'], 'locator': i['locator'], 'role': i['materialRole'],
                            'supports': [], 'weakens': [], 'state': 'vínculo com proposição ainda não julgado'} for i in items],
              'reviews': [], 'history': history, 'coverage': coverage, 'metrics': metrics,
              'queries': queries, 'accessFailures': failures, 'repetitionGroups': groups,
              'nextBatch': list({i['id']: i for i in next_batch}.values()), 'references': references,
              'publicationGate': {'sensitiveConclusionRequires': ['evidência externa conferida', 'revisor identificado', 'justificativa e limites', 'histórico persistido'],
                                  'automaticPublicationAllowed': False, 'pendingClassifications': True}}
    validate(result)
    return result


def validate(payload):
    ids = [i['id'] for i in payload['items']]
    urls = [i['url'] for i in payload['items']]
    assert len(ids) == len(set(ids)), 'IDs duplicados'
    assert len(urls) == len(set(urls)), 'URLs duplicadas'
    source_ids = {s['id'] for s in payload['sources']}
    for item in payload['items']:
        assert item['sourceId'] in source_ids
        assert item['format'] in FORMATS and item['stage'] in STAGES
        assert item['review']['reviewer'] is None
        assert item['editorialClassification'] is None
        assert item['stage'] not in {'revisado', 'publicado'}, 'Revisão humana não pode ser inferida'
        assert canonical_url(item['url']) == item['url']
    assert payload['metrics']['reviewedAudioSeconds'] == 0
    assert payload['metrics']['publishedChecks'] == 0


def write_outputs(payload):
    full = json.dumps(payload, ensure_ascii=False, indent=2) + '\n'
    for path in (ROOT / 'content/research.json', ROOT / 'dist/data/research.json'):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(full, encoding='utf-8')
    (ROOT / 'dist/data/research.js').write_text('window.ARQUIVO_RESEARCH = ' + json.dumps(payload, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + ';\n', encoding='utf-8')
    metrics = payload['metrics']
    lines = ['# Cobertura da pesquisa', '', f"Gerado em {payload['metadata']['generatedAt']} (UTC). Fuso de apresentação: America/Campo_Grande.", '',
             f"{metrics['items']} URLs únicas no lote; {metrics['newItems']} ainda não vinculadas à edição anterior. {metrics['accessed']} materiais acessados e {metrics['analysed']} com texto analisado.", '',
             'Links não representam afirmações distintas, confirmações independentes nem falsidades. A matriz descreve somente os materiais deste lote, pela data disponível da publicação ou do documento. Registros sem data ficam fora das linhas anuais.', '',
             f"{metrics['video']} vídeos e {metrics['audio']} áudios catalogados. Duração conhecida total: {metrics['mediaCataloguedSeconds'] / 3600:.2f} h. Áudio efetivamente revisado: 0 h. Não se deduz tempo revisado a partir da duração dos arquivos.", '',
             'Nenhuma nova classificação sensível foi publicada. As 71 afirmações da edição anterior são preservadas separadamente e não foram revalidadas por este lote.', '',
             '| Ano | Encontrados | Acessados | Texto analisado | Revisados | Checagens publicadas |', '| --- | ---: | ---: | ---: | ---: | ---: |']
    for row in payload['coverage']:
        lines.append(f"| {row['year']} | {row['found']} | {row['accessed']} | {row['analysed']} | 0 | 0 |")
    lines += ['', f"Materiais sem data: {metrics['undatedItems']}. Ausência de registros em um ano significa lacuna deste lote, não prova de inexistência.", '', '## Próximo lote', '']
    lines += ['- ' + gap['note'] for gap in payload['nextBatch']]
    lines += ['', '## Limitações de acesso', '']
    for failure in payload['accessFailures']:
        lines.append('- ' + text(failure))
    (ROOT / 'documentacao/COBERTURA.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--import-dir', type=Path)
    args = parser.parse_args()
    INPUT.mkdir(parents=True, exist_ok=True)
    if args.import_dir:
        for name in ('oficiais.json', 'checagens.json', 'audiovisual.json'):
            source = args.import_dir / name
            if source.exists():
                shutil.copyfile(source, INPUT / name)
        for name in ('oficiais.md', 'checagens.md', 'referencias.md'):
            source = args.import_dir / name
            if source.exists():
                shutil.copyfile(source, INPUT / name)
    inputs = {p.stem: json.loads(p.read_text(encoding='utf-8')) for p in sorted(INPUT.glob('*.json'))}
    legacy = json.loads((ROOT / 'content/acervo.editorial.json').read_text(encoding='utf-8'))
    news_path = ROOT / 'dist/data/news.json'
    feeds = json.loads(news_path.read_text(encoding='utf-8')) if news_path.exists() else {}
    previous_path = ROOT / 'content/research.json'
    previous = json.loads(previous_path.read_text(encoding='utf-8')) if previous_path.exists() else None
    history_path = ROOT / 'content/research-history.json'
    history = json.loads(history_path.read_text(encoding='utf-8')) if history_path.exists() else None
    if isinstance(history, dict):
        history = history.get('history', [])
    if history is not None and not isinstance(history, list):
        raise ValueError('Histórico precisa ser um array ou objeto com history array.')
    payload = build_payload(inputs, legacy, feeds, previous, history)
    write_outputs(payload)
    print(json.dumps(payload['metrics'], ensure_ascii=False))


if __name__ == '__main__':
    main()
