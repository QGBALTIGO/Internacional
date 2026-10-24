/* Arquivo Bolsonaro: interface estática, filtros locais e dados públicos versionados. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const norm = value => String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const name = person => person === 'jair' ? 'Jair Bolsonaro' : person === 'flavio' ? 'Flávio Bolsonaro' : 'Jair e Flávio Bolsonaro';
  const paths = {
    'arrow-up-right':'M6 18 18 6M6 6h12v12', 'arrow-right':'M4 12h16m-6-6 6 6-6 6', 'arrow-up':'M12 20V4m-6 6 6-6 6 6',
    search:'m16 16 5 5M18 10.5a7.5 7.5 0 1 1-15 0 7.5 7.5 0 0 1 15 0Z',
    bookmark:'M6 3h12v18l-6-4-6 4V3Z', close:'m6 6 12 12M6 18 18 6', plus:'M12 5v14M5 12h14',
    play:'m9 5 11 7-11 7V5Z', headphones:'M4 13v-1a8 8 0 0 1 16 0v1M4 12H2v8h5v-8H4Zm16 0h2v8h-5v-8h3Z',
    file:'M5 3h10l4 4v14H5V3Zm10 0v5h4M8 12h8M8 16h6', menu:'M4 6h16M4 12h16M4 18h16',
    moon:'M20.7 13a9 9 0 0 1-9.7-9.7A9 9 0 1 0 20.7 13Z', sun:'M12 3V1m0 22v-2M3 12H1m22 0h-2M5 5 3.5 3.5m17 17L19 19M5 19l-1.5 1.5m17-17L19 5M17 12a5 5 0 1 1-10 0 5 5 0 0 1 10 0Z',
    code:'m8 6-6 6 6 6m8-12 6 6-6 6m-3-15-2 18', grid:'M3 3h6v6H3V3Zm12 0h6v6h-6V3ZM3 15h6v6H3v-6Zm12 0h6v6h-6v-6Z',
    timeline:'M5 2v20M9 6h12M9 18h12M7 6a2 2 0 1 1-4 0 2 2 0 0 1 4 0Zm0 12a2 2 0 1 1-4 0 2 2 0 0 1 4 0Z',
    'chevron-down':'m6 9 6 6 6-6', download:'M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5',
    refresh:'M20 10a8 8 0 0 0-14-5L3 8m0-5v5h5M4 14a8 8 0 0 0 14 5l3-3m0 5v-5h-5',
    check:'m5 12 4 4L19 6', info:'M12 11v6m0-10v.01M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z',
    clock:'M12 6v6l4 2M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z',
    link:'m10 13 4-4M9 16l-2 2a4 4 0 0 1-6-6l4-4a4 4 0 0 1 6 0m4 0 2-2a4 4 0 0 1 6 6l-4 4a4 4 0 0 1-6 0',
    print:'M6 9V3h12v6M6 17H3V9h18v8h-3M6 14h12v7H6v-7Z', swap:'M4 7h16m-4-4 4 4-4 4M20 17H4m4-4-4 4 4 4'
  };
  const icon = key => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${paths[key] || paths.file}"/></svg>`;
  function hydrateIcons(root = document) { root.querySelectorAll('[data-icon]').forEach(el => { el.innerHTML = icon(el.dataset.icon); }); }
  function safeUrl(value, local = false) {
    const text = String(value ?? '');
    if (local && /^(assets|documentos|data)\/[a-zA-Z0-9_./-]+$/.test(text) && !text.includes('..')) return text;
    try { const u = new URL(text); return u.protocol === 'https:' && !u.username && !u.password ? u.href : ''; } catch { return ''; }
  }
  function external(url, text, className = '') { const href = safeUrl(url); return href ? `<a class="${esc(className)}" href="${esc(href)}" target="_blank" rel="noopener noreferrer">${esc(text)} ${icon('arrow-up-right')}</a>` : `<span>${esc(text)}</span>`; }
  function dateLabel(value, options = {}) {
    if (!value) return 'Data não informada';
    if (/^\d{4}$/.test(value)) return value;
    if (/^\d{4}-\d{2}$/.test(value)) return new Intl.DateTimeFormat('pt-BR', {month:'short',year:'numeric',timeZone:'UTC'}).format(new Date(value+'-01T12:00:00Z'));
    const d = new Date(/^\d{4}-\d{2}-\d{2}$/.test(value) ? value+'T12:00:00Z' : value);
    return Number.isNaN(d.getTime()) ? String(value) : new Intl.DateTimeFormat('pt-BR', {day:'numeric',month:'short',year:'numeric',timeZone:'UTC',...options}).format(d);
  }
  const timeLabel = value => value ? dateLabel(value, {day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit',timeZone:'America/Campo_Grande'}) : 'Nenhuma coleta registrada';
  function readStorage(key, fallback) { try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback; } catch { return fallback; } }
  function writeStorage(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* A navegação continua sem armazenamento. */ } }
  const base = window.ACERVO || {metadata:{},records:[],media:[],documents:[],images:[]};
  let data = structuredClone(base), news = window.ARQUIVO_NEWS || {metadata:{},items:[],feeds:[]};
  let recordMap = new Map(), mediaMap = new Map(), searchIndex = new Map(), currentCase = null, closingForHash = false;
  const state = {person:'all',query:'',topic:'all',verdict:'all',year:'all',sort:'newest',view:'grid',limit:12,savedOnly:false,saved:new Set(readStorage('arquivo-saved',[])),mediaType:'all',mediaQuery:'',mediaPerson:'all',mediaRole:'all',mediaLimit:9,comparisonLimit:4,newsQuery:'',newsLimit:12};
  let refreshInFlight = false, toastTimer;
  const badgeClass = v => v === 'Falso' ? 'false' : v === 'Enganoso' ? 'misleading' : v === 'Sem comprovação' ? 'unproven' : 'context';
  const badge = v => `<span class="badge ${badgeClass(v)}">${icon(v==='Falso'?'close':v==='Sem comprovação'?'info':'file')}${esc(v)}</span>`;
  const normalizedSources = list => (Array.isArray(list) ? list : []).filter(s => s && s.title && s.publisher && safeUrl(s.url));
  function validRecord(r) { return r && /^[a-z0-9-]+$/.test(r.id||'') && ['jair','flavio'].includes(r.person) && ['Falso','Enganoso','Sem comprovação'].includes(r.verdict) && ['title','claim','summary','context'].every(k=>typeof r[k]==='string'&&r[k].length>0) && normalizedSources(r.sources).length > 0; }
  function mergeUpdates(patch) {
    if (!patch || patch.schemaVersion !== 1) return false;
    for (const key of ['records','media','documents','comparisons','investigations']) {
      const map = new Map((data[key] || []).map(r=>[r.id,r]));
      for (const item of (patch[key] || [])) {
        if (!item || !/^[a-z0-9-]+$/.test(item.id || '')) continue;
        if (key==='records' && !validRecord(item)) continue;
        if (key!=='records' && !item.title) continue;
        map.set(item.id,item);
      }
      data[key] = [...map.values()];
    }
    if (patch.updatedAt && new Date(patch.updatedAt)>new Date(data.metadata.reviewedAt||0)) data.metadata.reviewedAt=patch.updatedAt;
    return true;
  }
  function rebuild() {
    recordMap = new Map(data.records.filter(validRecord).map(r=>[r.id,r])); data.records = [...recordMap.values()];
    mediaMap = new Map((data.media||[]).map(m=>[m.id,m]));
    searchIndex = new Map(data.records.map(r=>[r.id,norm([r.title,r.claim,r.summary,r.context,r.topic,name(r.person),...(r.tags||[]),...r.sources.map(s=>s.publisher)].join(' '))]));
    const topics=[...new Set(data.records.map(r=>r.topic))].sort((a,b)=>a.localeCompare(b,'pt-BR'));
    const years=[...new Set(data.records.map(r=>r.year).filter(Boolean))].sort((a,b)=>b-a);
    $('topicFilter').innerHTML='<option value="all">Todos os assuntos</option>'+topics.map(t=>`<option>${esc(t)}</option>`).join(''); $('topicFilter').value=state.topic;
    $('yearFilter').innerHTML='<option value="all">Todos os anos</option>'+years.map(y=>`<option value="${y}">${y}</option>`).join(''); $('yearFilter').value=state.year;
    const sources=new Set([...data.records,...(data.comparisons||[]),...(data.investigations||[])].flatMap(r=>(r.sources||[]).map(s=>s.url)));
    $('statCases').textContent=data.records.length; $('statMedia').textContent=data.media.length; $('statSources').textContent=sources.size;
    $('countAll').textContent=data.records.length; $('countJair').textContent=data.records.filter(r=>r.person==='jair').length; $('countFlavio').textContent=data.records.filter(r=>r.person==='flavio').length;
    $('editionNumber').textContent=data.metadata.edition||'02'; $('editorialDate').textContent=dateLabel(data.metadata.reviewedAt);
    renderSpotlights(); renderCases(); renderMedia(); renderComparisons(); renderInvestigations(); renderDocuments();
  }
  function toast(message) { clearTimeout(toastTimer);$('toast').textContent=message;$('toast').classList.add('visible');toastTimer=setTimeout(()=>$('toast').classList.remove('visible'),3500); }
  function filteredRecords() {
    const tokens=norm(state.query).split(/\s+/).filter(Boolean);
    return data.records.filter(r=>(state.person==='all'||r.person===state.person)&&(state.topic==='all'||r.topic===state.topic)&&(state.verdict==='all'||r.verdict===state.verdict)&&(state.year==='all'||String(r.year)===state.year)&&(!state.savedOnly||state.saved.has(r.id))&&tokens.every(t=>searchIndex.get(r.id).includes(t))).sort((a,b)=>state.sort==='sources'?b.sources.length-a.sources.length:state.sort==='oldest'?String(a.sortDate||a.statementDate||a.year).localeCompare(String(b.sortDate||b.statementDate||b.year)):String(b.sortDate||b.statementDate||b.year).localeCompare(String(a.sortDate||a.statementDate||a.year)));
  }
  function caseCard(r) { return `<article class="case-card" aria-labelledby="title-${esc(r.id)}"><div class="card-top">${badge(r.verdict)}<button class="save-button ${state.saved.has(r.id)?'saved':''}" data-action="save" data-id="${esc(r.id)}" aria-pressed="${state.saved.has(r.id)}" aria-label="Salvar registro: ${esc(r.title)}">${icon('bookmark')}</button></div><div class="card-meta"><strong>${name(r.person)}</strong><span>${esc(r.dateLabel||dateLabel(r.statementDate))}</span></div><h3 id="title-${esc(r.id)}"><button data-action="case" data-id="${esc(r.id)}">${esc(r.title)}</button></h3><p class="card-claim">${esc(r.claim)}</p><div class="card-topic">${icon('file')}<span>${esc(r.topic)}</span>${r.correction?`<span class="correction-mark">Correção registrada</span>`:''}${r.relatedMedia?.length?`${icon('play')}<span>Material vinculado</span>`:''}</div><div class="card-footer"><span>${r.sources.length} ${r.sources.length===1?'fonte':'fontes'}</span><button data-action="case" data-id="${esc(r.id)}" aria-label="Abrir ficha: ${esc(r.title)}">Ler a ficha ${icon('arrow-up-right')}</button></div></article>`; }
  function renderCases() {
    const records=filteredRecords(),shown=records.slice(0,state.limit);let lastYear;
    $('caseGrid').className='case-grid'+(state.view==='timeline'?' timeline':'');
    $('caseGrid').innerHTML=shown.map(r=>{let heading='';if(state.view==='timeline'&&r.year!==lastYear){lastYear=r.year;heading=`<h3 class="timeline-year">${esc(r.year)}</h3>`;}return heading+caseCard(r);}).join('');
    $('resultsStatus').innerHTML=`<strong>${records.length}</strong> ${records.length===1?'registro encontrado':'registros encontrados'}`;
    $('shownCount').textContent=`Exibindo ${shown.length} de ${records.length}`;$('emptyState').hidden=records.length>0;$('loadMore').hidden=shown.length>=records.length;
    $('clearFilters').hidden=state.person==='all'&&!state.query&&state.topic==='all'&&state.verdict==='all'&&state.year==='all'&&!state.savedOnly;
    document.querySelectorAll('[data-person]').forEach(el=>{const active=state.person===el.dataset.person;el.classList.toggle('active',active);el.setAttribute('aria-pressed',active);});
    $('savedFilter').setAttribute('aria-pressed',state.savedOnly);$('savedCount').textContent=[...state.saved].filter(id=>recordMap.has(id)).length;
    ['grid','timeline'].forEach(view=>{const el=$(view+'View');el.classList.toggle('active',state.view===view);el.setAttribute('aria-pressed',state.view===view);});
  }
  function resetFilters() {Object.assign(state,{person:'all',query:'',topic:'all',verdict:'all',year:'all',limit:12,savedOnly:false});$('searchInput').value='';['topicFilter','verdictFilter','yearFilter'].forEach(id=>$(id).value='all');renderCases();}
  function toggleSave(id) {if(state.saved.has(id))state.saved.delete(id);else state.saved.add(id);writeStorage('arquivo-saved',[...state.saved]);renderCases();if(currentCase===id&&$('caseDialog').open)renderCaseDialog(recordMap.get(id));}
  function renderSpotlights() {
    const selected=(data.spotlights||['flavio-smartmatic-2026','jair-tcu-mortes','jair-origem-pix']).map(id=>recordMap.get(id)).filter(Boolean);
    for(const r of filteredRecords()){if(selected.length>=3)break;if(!selected.find(i=>i.id===r.id))selected.push(r);}
    $('spotlightGrid').innerHTML=selected.slice(0,3).map(r=>`<article class="spotlight-card"><span class="small-label">${name(r.person)} / ${esc(r.topic)}</span><h3><button data-action="case" data-id="${esc(r.id)}">${esc(r.title)}</button></h3><span aria-hidden="true">${icon('arrow-up-right')}</span></article>`).join('');
  }
  function sourceList(sources) {return `<ol class="source-list">${normalizedSources(sources).map(s=>`<li><div>${external(s.url,s.title)}<small>${esc(s.publisher)}${s.date?' / '+esc(dateLabel(s.date)):''}</small><span class="source-type">${s.type==='primary'?'Documento ou registro original':s.type==='factcheck'?'Checagem publicada':'Apuração jornalística'}</span></div></li>`).join('')}</ol>`;}
  function relatedMedia(ids) {const items=(ids||[]).map(id=>mediaMap.get(id)).filter(Boolean);return items.length?`<section class="detail-section"><h3>Materiais relacionados</h3><div class="related-media">${items.map(m=>`<button data-action="media" data-id="${esc(m.id)}">${icon(m.type==='audio'?'headphones':'play')}${esc(m.title)}</button>`).join('')}</div></section>`:'';}
  function renderCaseDialog(r) {
    if(!r)return;$('dialogLabel').textContent=`FICHA / ${r.id}`;
    $('dialogContent').innerHTML=`<div class="dialog-body"><div class="dialog-badges">${badge(r.verdict)}<span>${esc(r.topic)}</span></div><h2 id="caseTitle">${esc(r.title)}</h2><div class="detail-author"><img src="assets/${r.person}.webp" alt="" width="42" height="42"><div><strong>${name(r.person)}</strong><small>${esc(r.dateLabel||dateLabel(r.statementDate))}${r.datePrecision&&r.datePrecision!=='day'?' / data aproximada':''}</small></div></div><div class="statement-box"><span class="small-label">A DECLARAÇÃO</span><p>${esc(r.claim)}</p><small>Síntese da afirmação. A formulação original está nas fontes.</small></div><section class="detail-section"><h3>O que a documentação mostra</h3><p class="evidence">${esc(r.summary)}</p>${r.editorialNote?`<p class="muted-detail">${esc(r.editorialNote)}</p>`:''}</section>${r.correction?`<section class="correction-box"><h3>Correção posterior / ${esc(dateLabel(r.correction.date))}</h3><p>${esc(r.correction.text)}</p>${external(r.correction.sourceUrl,'Consultar a correção')}</section>`:''}<section class="detail-section"><h3>Contexto</h3><p>${esc(r.context)}</p>${r.classificationNote?`<p class="muted-detail">${esc(r.classificationNote)}</p>`:''}</section><section class="detail-section"><h3>Fontes da ficha</h3>${sourceList(r.sources)}</section>${r.media?.length?`<section class="detail-section"><h3>Gravações e outros registros</h3><ol class="source-list">${r.media.filter(m=>safeUrl(m.url)).map(m=>`<li><div>${external(m.url,m.title)}<small>${esc(m.publisher||m.role||'Registro vinculado')}${m.access?' / '+esc(m.access):''}</small></div></li>`).join('')}</ol></section>`:''}${relatedMedia(r.relatedMedia)}<div class="detail-actions"><button data-action="save" data-id="${esc(r.id)}" class="${state.saved.has(r.id)?'saved':''}" aria-pressed="${state.saved.has(r.id)}">${icon('bookmark')}${state.saved.has(r.id)?'Salvo':'Salvar'}</button><button data-action="copy" data-id="${esc(r.id)}">${icon('link')}Copiar link</button><button data-action="download-case" data-id="${esc(r.id)}">${icon('download')}Baixar ficha</button><button data-action="print">${icon('print')}Imprimir</button></div><p class="detail-footnote">Revisão: ${esc(dateLabel(r.reviewedAt||data.metadata.reviewedAt))}. A classificação considera as fontes indicadas. Os favoritos ficam neste navegador.</p></div>`;
  }
  function updateBodyLock(){document.body.classList.toggle('modal-open',!!document.querySelector('dialog[open]'));}
  function openDialog(id) { const d=$(id);if(!d.open)d.showModal();updateBodyLock(); }
  function openCase(id,fromHash=false) {const r=recordMap.get(id);if(!r){toast('Ficha não encontrada.');return;}currentCase=id;renderCaseDialog(r);openDialog('caseDialog');$('caseDialog').scrollTop=0;if(!fromHash)history.pushState(null,'',`#ficha=${encodeURIComponent(id)}`);}
  function syncHash() {const hash=location.hash;if(hash.startsWith('#ficha=')){try{openCase(decodeURIComponent(hash.slice(7)),true);}catch{return;}}else if($('caseDialog').open){closingForHash=true;$('caseDialog').close();closingForHash=false;}}
  function mediaCategory(m) {if(m.category)return m.category;const t=norm(m.role+' '+m.title);return /entrevista|debate|roda viva|flow|podcast/.test(t)?'entrevista':/declaracao|discurso|pronunciamento|fala original/.test(t)?'declaracao':'contexto';}
  function mediaPeople(m) {return Array.isArray(m.people)?m.people:Array.isArray(m.persons)?m.persons:m.person?[m.person]:[];}
  function mediaCard(m) {
    const credit=m.creditShort||m.publisher||m.credit||'Publicador';
    const common=`<div class="media-card-body"><div class="media-meta"><span>${esc(credit)}</span><span>${esc(m.dateLabel||dateLabel(m.date))}</span></div><h3>${esc(m.title)}</h3><p>${esc(m.description||'')}</p>`;
    if(m.type==='audio')return `<article class="media-card audio-card" id="midia-${esc(m.id)}"><div class="audio-heading">${icon('headphones')}<div class="waveform" aria-hidden="true">${Array.from({length:40},(_,i)=>`<i style="height:${6+(i*7%25)}px"></i>`).join('')}</div><span>ÁUDIO ORIGINAL</span></div>${common}<audio class="audio-player" controls preload="none" src="${esc(safeUrl(m.src||m.url,true))}" aria-label="Ouvir ${esc(m.title)}"></audio><div class="media-meta"><span>${esc(m.role||'Reportagem')}</span><span>${esc(m.durationLabel||'')}</span></div>${external(m.sourceUrl||m.url,m.hasTranscript?'Fonte e transcrição':'Publicação de origem','media-source')}</div></article>`;
    const thumb=safeUrl(m.thumbnail,true)||(m.youtubeId&&/^[\w-]{11}$/.test(m.youtubeId)?`https://i.ytimg.com/vi/${m.youtubeId}/hqdefault.jpg`:'');
    return `<article class="media-card" id="midia-${esc(m.id)}"><button class="video-cover" data-action="media" data-id="${esc(m.id)}" aria-label="Abrir vídeo: ${esc(m.title)}"><span class="video-typographic"><small>REGISTRO EM VÍDEO</small><strong>${esc(credit)}</strong></span>${thumb?`<img src="${esc(thumb)}" alt="" loading="lazy" decoding="async" width="480" height="270" referrerpolicy="no-referrer">`:''}<span class="video-label">${esc(m.role||'Vídeo')}</span><span class="play-round">${icon('play')}</span><span class="video-time">${esc(m.durationLabel||'VÍDEO')}</span></button>${common}${external(m.sourceUrl||m.url,'Publicação de origem','media-source')}</div></article>`;
  }
  function renderMedia() {
    const q=norm(state.mediaQuery);const items=data.media.filter(m=>(state.mediaType==='all'||m.type===state.mediaType)&&(state.mediaPerson==='all'||mediaPeople(m).includes(state.mediaPerson))&&(state.mediaRole==='all'||mediaCategory(m)===state.mediaRole)&&(!q||norm([m.title,m.description,m.credit,m.creditShort,...(m.tags||[])].join(' ')).includes(q))).sort((a,b)=>String(b.date||'').localeCompare(String(a.date||'')));
    $('mediaGrid').innerHTML=items.slice(0,state.mediaLimit).map(mediaCard).join('')||'<div class="empty-state"><h3>Nenhum material com esses filtros.</h3></div>';
    $('mediaCount').textContent=`${items.length} ${items.length===1?'material':'materiais'}`;$('loadMoreMedia').hidden=state.mediaLimit>=items.length;
    document.querySelectorAll('[data-media-type]').forEach(el=>{const active=state.mediaType===el.dataset.mediaType;el.classList.toggle('active',active);el.setAttribute('aria-pressed',active);});
  }
  function pausePlayers(except=null) {document.querySelectorAll('audio,video').forEach(p=>{if(p!==except)p.pause();});}
  function openMedia(id) {
    const m=mediaMap.get(id);if(!m)return;pausePlayers();let player='';
    if(m.type==='audio')player=`<div class="media-audio-wrap"><audio controls preload="metadata" src="${esc(safeUrl(m.src||m.url,true))}" aria-label="${esc(m.title)}"></audio></div>`;
    else if(m.youtubeId&&/^[\w-]{11}$/.test(m.youtubeId))player=`<div class="media-player-wrap"><iframe src="https://www.youtube-nocookie.com/embed/${m.youtubeId}?rel=0${Number.isInteger(m.startSeconds)?'&start='+m.startSeconds:''}" title="${esc(m.title)}" allow="encrypted-media; picture-in-picture; fullscreen" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe></div>`;
    else if(safeUrl(m.src,true))player=`<div class="media-player-wrap"><video controls playsinline preload="metadata" poster="${esc(safeUrl(m.thumbnail,true))}" src="${esc(safeUrl(m.src,true))}" aria-label="${esc(m.title)}"></video></div>`;
    else player='<div class="media-audio-wrap">Este registro está disponível na página do publicador.</div>';
    $('mediaDialogContent').innerHTML=`${player}<div class="media-dialog-description"><span class="small-label">${esc(m.role||'Registro')} / ${esc(m.dateLabel||dateLabel(m.date))}</span><h2 id="mediaDialogTitle">${esc(m.title)}</h2><p>${esc(m.description||'')}</p><p>${esc(m.credit||m.publisher||'')}. ${esc(m.license||'Direitos do publicador. Reprodução no player original.')}</p>${m.verificationNote?`<p>${esc(m.verificationNote)}</p>`:''}<div class="media-links">${external(m.sourceUrl||m.url,'Abrir publicação original')}${m.youtubeId?external(`https://www.youtube.com/watch?v=${m.youtubeId}`,'Assistir no YouTube'):''}</div></div>`;openDialog('mediaDialog');
  }
  function renderComparisons() {
    const items=data.comparisons||[];$('comparacoes').hidden=!items.length;
    $('comparisonGrid').innerHTML=items.slice(0,state.comparisonLimit).map(c=>`<article class="comparison-card"><span class="badge context">${esc(c.category||'Comparação de registros')}</span><h3>${esc(c.title)}</h3><div class="comparison-pair">${[c.first,c.second].map(s=>`<div class="comparison-item"><time>${icon('clock')}${esc(s.dateLabel||dateLabel(s.date))}</time><p>${esc(s.summary)}</p></div>`).join('')}</div><div class="comparison-footer"><span>${name(c.person)}</span><button data-action="comparison" data-id="${esc(c.id)}">Contexto e fontes ${icon('arrow-up-right')}</button></div></article>`).join('');$('loadMoreComparisons').hidden=state.comparisonLimit>=items.length;
  }
  function renderInvestigations() {
    const items=data.investigations||[];$('apuracoes').hidden=!items.length;
    $('investigationGrid').innerHTML=items.map((i,index)=>`<article class="investigation-card"><span class="episode-number">${String(index+1).padStart(2,'0')}</span><span class="badge context">${esc((i.status||'Documentação do episódio').split(';')[0])}</span><h3>${esc(i.title)}</h3><p>${esc(i.summary)}</p><button data-action="investigation" data-id="${esc(i.id)}">Abrir documentação ${icon('arrow-up-right')}</button></article>`).join('');
  }
  function openContext(type,id) {
    const item=(data[type==='comparison'?'comparisons':'investigations']||[]).find(i=>i.id===id);if(!item)return;
    let sections='';
    if(type==='comparison')sections=`<div class="context-timeline">${[item.first,item.second].map((s,i)=>`<article><time>${esc(s.dateLabel||dateLabel(s.date))}</time><h3>${i===0?'Primeiro registro':'Registro posterior'}</h3><p>${esc(s.summary)}</p>${external(s.sourceUrl,'Consultar o registro')}</article>`).join('')}</div><section class="detail-section"><h3>Como comparar os registros</h3><p class="evidence">${esc(item.analysis)}</p><p>${esc(item.context||'')}</p></section>`;
    else sections=`<section class="detail-section"><p class="evidence">${esc(item.summary)}</p><p>${esc(item.context||'')}</p></section>${item.provenance?.length?`<section class="detail-section"><h3>Mensagens, áudios e documentos publicados</h3><ol class="source-list">${item.provenance.map(p=>`<li><div><strong>${esc(p.material)}</strong><p>${esc(p.description)}</p>${external(p.sourceUrl,'Abrir material em '+p.publisher)}</div></li>`).join('')}</ol></section>`:''}${item.timeline?.length?`<div class="context-timeline">${item.timeline.map(t=>`<article><time>${esc(t.dateLabel||dateLabel(t.date))}</time><h3>${esc(t.title)}</h3><p>${esc(t.text)}</p>${external(t.sourceUrl,'Consultar a fonte')}</article>`).join('')}</div>`:''}${item.response?`<section class="detail-section"><h3>Resposta dos envolvidos</h3><p>${esc(item.response)}</p></section>`:''}${item.limitations?`<section class="correction-box"><h3>O que permanece em apuração</h3><p>${esc(item.limitations)}</p></section>`:''}`;
    $('contextContent').innerHTML=`<div class="dialog-body"><div class="dialog-badges"><span class="badge context">${esc(item.category||item.status||'Contexto')}</span><span>${name(item.person)}</span></div><h2 id="contextTitle">${esc(item.title)}</h2>${sections}<section class="detail-section"><h3>Fontes e documentos</h3>${sourceList(item.sources)}</section>${relatedMedia(item.relatedMedia)}<p class="detail-footnote">Revisão: ${esc(dateLabel(item.reviewedAt||data.metadata.reviewedAt))}. Sínteses dos registros citados, com contexto e respostas disponíveis.</p></div>`;openDialog('contextDialog');$('contextDialog').scrollTop=0;
  }
  function renderNews() {
    const seeds=data.news||[];const unique=new Map([...seeds,...(news.items||[])].filter(n=>n.title&&safeUrl(n.url)).map(n=>[n.url,n]));
    const items=[...unique.values()].filter(n=>!state.newsQuery||norm(n.title+' '+n.publisher).includes(norm(state.newsQuery))).sort((a,b)=>(new Date(b.publishedAt||b.date||0).getTime()||0)-(new Date(a.publishedAt||a.date||0).getTime()||0));
    $('newsList').innerHTML=items.slice(0,state.newsLimit).map(n=>{const raw=n.publishedAt||n.date;const date=raw?new Date(/^\d{4}-\d{2}-\d{2}$/.test(raw)?raw+'T12:00:00Z':raw):null;const ok=date&&!Number.isNaN(date.getTime());return `<article class="news-item"><div class="news-date"><strong>${ok?new Intl.DateTimeFormat('pt-BR',{day:'numeric',timeZone:'America/Sao_Paulo'}).format(date):'s/d'}</strong>${ok?new Intl.DateTimeFormat('pt-BR',{month:'short',year:'2-digit',timeZone:'America/Sao_Paulo'}).format(date):''}</div><div><h3><a href="${esc(safeUrl(n.url))}" target="_blank" rel="noopener noreferrer">${esc(n.title)}</a></h3><div class="news-publisher"><span>${esc(n.publisher||'Publicação externa')}</span><span>${esc(n.kind==='factcheck'?'Checagem publicada':'Publicação externa')}</span></div></div><a href="${esc(safeUrl(n.url))}" target="_blank" rel="noopener noreferrer" aria-label="Abrir notícia: ${esc(n.title)}">${icon('arrow-up-right')}</a></article>`;}).join('')||'<p class="news-empty">Nenhuma publicação com esse termo. Os registros do acervo continuam disponíveis acima.</p>';
    $('loadMoreNews').hidden=state.newsLimit>=items.length;renderStatus();
  }
  function renderStatus() {
    const m=news.metadata||{},feeds=news.feeds||[],ok=feeds.filter(f=>f.status==='ok').length;
    $('lastAttempt').textContent=timeLabel(m.lastAttemptAt);$('lastSuccess').textContent=timeLabel(m.lastSuccessfulCheckAt);$('feedHealth').textContent=feeds.length?`${ok} de ${feeds.length}`:'Nenhuma coleta registrada';
    $('monitorTitle').textContent=m.scheduleVerified?'Coleta a cada hora':'Consulta das fontes';
    const last=m.lastSuccessfulCheckAt?new Date(m.lastSuccessfulCheckAt):null;const stale=!last||Number.isNaN(last.getTime())||(Date.now()-last.getTime()>4*60*60*1000);
    $('statusDot').classList.toggle('stale',stale);$('freshnessLabel').textContent=last?(stale?'Coleta precisa de atualização':'Fontes consultadas'):'Acervo disponível';
    $('freshnessDetail').textContent=last?timeLabel(m.lastSuccessfulCheckAt):`Revisão em ${dateLabel(data.metadata.reviewedAt)}`;
    $('feedStatusList').innerHTML=feeds.map(f=>`<div class="feed-status"><div>${esc(f.name)}<small>${esc(f.note||'')}</small></div><span class="${f.status==='ok'?'success':'failure'}">${f.status==='ok'?`${f.itemCount||0} itens`:'Falha de acesso'}</span></div>`).join('')||'<p>A situação das fontes será exibida após a coleta.</p>';
  }
  function renderDocuments() {
    $('documentList').innerHTML=(data.documents||[]).map(d=>`<article class="document-item"><div class="document-icon">${icon('file')}PDF</div><div class="document-info"><h3><a href="${esc(safeUrl(d.src||d.url,true))}" target="_blank" rel="noopener noreferrer">${esc(d.title)}</a></h3><p>${esc(d.description||'')}</p><div class="document-detail"><span>${esc(d.dateLabel||dateLabel(d.date))}</span>${d.pages?`<span>${d.pages} páginas</span>`:''}<span>${esc(d.bytesLabel||'')}</span></div><div class="document-links"><a href="${esc(safeUrl(d.src||d.url,true))}" target="_blank" rel="noopener noreferrer">Abrir documento ${icon('arrow-up-right')}</a>${external(d.sourceUrl||d.url,'Origem do documento')}</div></div></article>`).join('');
  }
  function openCredits() {
    const publishers=new Map(),seen=new Set();for(const r of [...data.records,...(data.comparisons||[]),...(data.investigations||[])])for(const s of normalizedSources(r.sources)){if(!seen.has(s.url)){seen.add(s.url);publishers.set(s.publisher,(publishers.get(s.publisher)||0)+1);}}
    $('creditsContent').innerHTML=`<h2 id="creditsTitle">Fontes e créditos</h2><p>${data.records.length} checagens e ${seen.size} referências únicas nas fichas, comparações e apurações. Uma referência pode aparecer em mais de um registro.</p><div class="publisher-list">${[...publishers].sort((a,b)=>b[1]-a[1]).map(([p,n])=>`<div>${esc(p)}<span>${n} ${n===1?'referência':'referências'}</span></div>`).join('')}</div><h3>Fotografias</h3><ul class="credits-list">${(data.images||[]).map(i=>`<li>${external(i.sourceUrl,i.title)}. ${esc(i.credit)}. ${external(i.licenseUrl,i.license||'Licença')}. ${esc(i.notes||'')}</li>`).join('')}</ul><p>Retratos institucionais para identificar os autores. O enquadramento e os tons de cinza são aplicados na apresentação. Eles não representam os episódios narrados.</p><h3>Vídeos, áudios e documentos</h3><ul class="credits-list">${data.media.map(m=>`<li>${external(m.sourceUrl||m.url,m.title)}. ${esc(m.credit||m.publisher||'')}. ${esc(m.license||'Direitos do publicador.')}</li>`).join('')}</ul><h3>Projeto</h3><p>Fonte Manrope sob Open Font License 1.1. Ícones vetoriais em SVG. Pesquisas e filtros são processados no navegador. Favoritos e preferência de tema ficam no armazenamento local. Mídias externas são fornecidas pelos respectivos publicadores.</p>${external('https://github.com/QGBALTIGO/Internacional','Código, documentação e histórico')}`;openDialog('creditsDialog');
  }
  function download(filename,content,type) {const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  function exportCSV() {const cell=v=>{let s=String(v??'');if(/^[=+\-@\t\r]/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"';};const rows=[['id','pessoa','data','tema','classificacao','titulo','declaracao','evidencia','contexto','fontes'],...data.records.map(r=>[r.id,name(r.person),r.statementDate||r.dateLabel,r.topic,r.verdict,r.title,r.claim,r.summary,r.context,r.sources.map(s=>s.publisher+': '+s.url).join('\n')])];download('arquivo-bolsonaro.csv','\ufeff'+rows.map(r=>r.map(cell).join(';')).join('\r\n'),'text/csv;charset=utf-8');}
  function downloadCase(id) {const r=recordMap.get(id);if(!r)return;download(r.id+'.txt',`${r.title}\n${name(r.person)} | ${r.dateLabel} | ${r.verdict}\n\nDECLARAÇÃO\n${r.claim}\n\nEVIDÊNCIA\n${r.summary}\n\nCONTEXTO\n${r.context}\n${r.correction?'\nCORREÇÃO POSTERIOR\n'+r.correction.text+'\n'+r.correction.sourceUrl+'\n':''}\nFONTES\n${r.sources.map(s=>s.publisher+' | '+s.title+'\n'+s.url).join('\n\n')}\n\nRevisão: ${r.reviewedAt||data.metadata.reviewedAt}\n`,'text/plain;charset=utf-8');}
  async function copyCase(id) {try{await navigator.clipboard.writeText(location.href.split('#')[0]+'#ficha='+encodeURIComponent(id));toast('Link da ficha copiado.');}catch{toast('O navegador bloqueou a cópia. O endereço da ficha está na barra de navegação.');}}
  function setTheme(theme) {document.documentElement.dataset.theme=theme;$('themeToggle').innerHTML=icon(theme==='dark'?'sun':'moon');$('themeToggle').setAttribute('aria-label',theme==='dark'?'Ativar tema claro':'Ativar tema escuro');writeStorage('arquivo-theme',theme);}
  async function fetchJSON(url) {const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),10000);try{const response=await fetch(url,{signal:controller.signal,credentials:'omit',referrerPolicy:'no-referrer',cache:'no-cache'});if(!response.ok)throw new Error('Dados indisponíveis');const raw=await response.text();if(raw.length>3000000)throw new Error('Arquivo acima do limite');return JSON.parse(raw);}finally{clearTimeout(timeout);}}
  async function refreshRemote(manual=false) {
    if(refreshInFlight||location.protocol==='file:'){if(manual)toast('Esta cópia usa os dados incluídos no download.');return;}
    refreshInFlight=true;$('refreshNews').disabled=true;
    const remote='https://raw.githubusercontent.com/QGBALTIGO/Internacional/main/dist/data/';
    const results=await Promise.allSettled([fetchJSON(remote+'news.json'),fetchJSON(remote+'editorial-updates.json')]);
    let received=false;
    if(results[0].status==='fulfilled'&&Array.isArray(results[0].value.items)&&results[0].value.schemaVersion===1){const candidate=results[0].value;if(new Date(candidate.metadata?.lastAttemptAt||0)>=new Date(news.metadata?.lastAttemptAt||0)){news=candidate;writeStorage('arquivo-news-cache',news);}received=true;}
    if(results[1].status==='fulfilled'&&results[1].value.schemaVersion===1){if(mergeUpdates(results[1].value)){rebuild();writeStorage('arquivo-updates-cache',results[1].value);}received=true;}
    renderNews();refreshInFlight=false;$('refreshNews').disabled=false;if(manual)toast(received?'Última versão disponível carregada.':'Não foi possível atualizar agora. Os dados já carregados continuam disponíveis.');
  }
  document.addEventListener('click',event=>{
    const el=event.target.closest('button,a');if(!el)return;
    if(el.dataset.close){$(el.dataset.close).close();return;}
    const {action,id}=el.dataset;
    if(action==='case')openCase(id);else if(action==='save')toggleSave(id);else if(action==='media')openMedia(id);else if(action==='comparison'||action==='investigation')openContext(action,id);else if(action==='credits')openCredits();else if(action==='copy')copyCase(id);else if(action==='download-case')downloadCase(id);else if(action==='print')window.print();
    if(el.dataset.person){state.person=el.dataset.person;state.limit=12;renderCases();}
    if(el.dataset.mediaType){pausePlayers();state.mediaType=el.dataset.mediaType;state.mediaLimit=9;renderMedia();}
    if(el.closest('#mobileMenu')){$('mobileMenu').hidden=true;$('menuToggle').setAttribute('aria-expanded','false');}
  });
  let searchTimer;$('searchInput').addEventListener('input',e=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>{state.query=e.target.value;state.limit=12;renderCases();},120);});
  for(const [id,key] of [['topicFilter','topic'],['verdictFilter','verdict'],['yearFilter','year'],['sortSelect','sort']])$(id).addEventListener('change',e=>{state[key]=e.target.value;state.limit=12;renderCases();});
  $('savedFilter').addEventListener('click',()=>{state.savedOnly=!state.savedOnly;state.limit=12;renderCases();});$('clearFilters').addEventListener('click',resetFilters);$('resetEmpty').addEventListener('click',resetFilters);
  $('gridView').addEventListener('click',()=>{state.view='grid';renderCases();});$('timelineView').addEventListener('click',()=>{state.view='timeline';renderCases();});$('loadMore').addEventListener('click',()=>{state.limit+=12;renderCases();});
  $('mediaSearch').addEventListener('input',e=>{state.mediaQuery=e.target.value;state.mediaLimit=9;renderMedia();});for(const [id,key] of [['mediaPerson','mediaPerson'],['mediaRole','mediaRole']])$(id).addEventListener('change',e=>{pausePlayers();state[key]=e.target.value;state.mediaLimit=9;renderMedia();});
  $('loadMoreMedia').addEventListener('click',()=>{state.mediaLimit+=9;renderMedia();});$('loadMoreComparisons').addEventListener('click',()=>{state.comparisonLimit+=4;renderComparisons();});
  $('newsSearch').addEventListener('input',e=>{state.newsQuery=e.target.value;state.newsLimit=12;renderNews();});$('loadMoreNews').addEventListener('click',()=>{state.newsLimit+=12;renderNews();});$('refreshNews').addEventListener('click',()=>refreshRemote(true));
  $('exportJson').addEventListener('click',()=>download('arquivo-bolsonaro.json',JSON.stringify(data,null,2),'application/json'));$('exportCsv').addEventListener('click',exportCSV);
  $('themeToggle').addEventListener('click',()=>setTheme(document.documentElement.dataset.theme==='dark'?'light':'dark'));
  $('menuToggle').addEventListener('click',()=>{const opened=$('mobileMenu').hidden;$('mobileMenu').hidden=!opened;$('menuToggle').setAttribute('aria-expanded',opened);});
  document.addEventListener('keydown',e=>{if(e.key==='/'&&!e.ctrlKey&&!e.metaKey&&!document.querySelector('dialog[open]')&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)){e.preventDefault();$('searchInput').focus();$('acervo').scrollIntoView();}if(e.key==='Escape'){$('mobileMenu').hidden=true;$('menuToggle').setAttribute('aria-expanded','false');}});
  document.addEventListener('error',e=>{if(e.target.tagName==='IMG'&&e.target.closest('.video-cover')){e.target.hidden=true;e.target.closest('.video-cover').classList.add('thumbnail-missing');}},true);
  document.addEventListener('play',e=>{if(e.target.matches('audio,video'))pausePlayers(e.target);},true);
  document.querySelectorAll('dialog').forEach(d=>{d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();}});d.addEventListener('close',()=>{if(d.id==='mediaDialog'){$('mediaDialogContent').querySelectorAll('audio,video').forEach(p=>p.pause());$('mediaDialogContent').innerHTML='';}if(d.id==='caseDialog'){currentCase=null;if(!closingForHash&&location.hash.startsWith('#ficha='))history.replaceState(null,'','#acervo');}updateBodyLock();});});
  window.addEventListener('hashchange',syncHash);window.addEventListener('popstate',syncHash);
  let scrollQueued=false;window.addEventListener('scroll',()=>{if(!scrollQueued){scrollQueued=true;requestAnimationFrame(()=>{const h=document.documentElement.scrollHeight-innerHeight;$('readingProgress').style.width=(h>0?Math.min(100,scrollY/h*100):0)+'%';scrollQueued=false;});}},{passive:true});
  hydrateIcons();setTheme(readStorage('arquivo-theme',matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light'));
  const cachedNews=readStorage('arquivo-news-cache',null);if(cachedNews?.schemaVersion===1&&new Date(cachedNews.metadata?.lastAttemptAt||0)>new Date(news.metadata?.lastAttemptAt||0))news=cachedNews;
  mergeUpdates(window.ARQUIVO_UPDATES);const cachedUpdates=readStorage('arquivo-updates-cache',null);if(cachedUpdates?.schemaVersion===1&&new Date(cachedUpdates.updatedAt||0)>new Date(window.ARQUIVO_UPDATES?.updatedAt||0))mergeUpdates(cachedUpdates);
  rebuild();renderNews();syncHash();
  if('IntersectionObserver' in window){const navObserver=new IntersectionObserver(entries=>{for(const entry of entries)if(entry.isIntersecting)document.querySelectorAll('.desktop-nav a').forEach(a=>a.classList.toggle('active',a.hash==='#'+entry.target.id));},{rootMargin:'-15% 0px -65% 0px'});['acervo','midiateca','comparacoes','noticias','documentos'].forEach(id=>navObserver.observe($(id)));}
  refreshRemote();setInterval(()=>{if(document.visibilityState==='visible')refreshRemote();},20*60*1000);
})();
