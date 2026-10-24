/* Navegação e descoberta do acervo. Não cria conteúdo nem altera estados editoriais. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  if (!$('portalRecent')) return;
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const norm = s => String(s ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const safe = s => {try {const u=new URL(String(s));return u.protocol==='https:'&&!u.username&&!u.password?u.href:'';}catch{return '';}};
  const paths={folder:'M3 5h6l2 3h10v12H3V5Z',file:'M5 3h9l5 5v13H5ZM14 3v5h5M8 12h8M8 16h6',play:'m9 5 11 7-11 7V5Z',arrow:'M4 12h16m-6-6 6 6-6 6',quote:'M4 5h7v8H8l-3 6H3l3-6H4ZM14 5h7v8h-3l-3 6h-2l3-6h-2Z',check:'M9 3h6l2 3h3v15H4V6h3l2-3ZM8 13l3 3 5-6',headphones:'M4 13v-1a8 8 0 0 1 16 0v1M4 12H2v8h5v-8H4Zm16 0h2v8h-5v-8h3Z'};
  const icon=k=>`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${paths[k]||paths.file}"/></svg>`;
  const formats={documento:'Documento',video:'Vídeo',audio:'Áudio',checagem:'Checagem do veículo',reportagem:'Reportagem',registro:'Registro público'};
  const titles={inicio:'Visão geral',pesquisa:'Catálogo documental',acervo:'Falas e checagens',midiateca:'Vídeos e áudios',comparacoes:'Entre falas',apuracoes:'Frente Vorcaro',documentos:'Documentos e arquivos',noticias:'Notícias',fontes:'Mapa de fontes',cobertura:'Cobertura da pesquisa',correcoes:'Histórico e correções',metodologia:'Critérios editoriais'};
  const paneNodes=[...document.querySelectorAll('[data-portal-pane]')];
  let current='inicio',searchLimit=12,report=window.ARQUIVO_RESEARCH||{items:[],sources:[],media:[]};
  const legacy=window.ACERVO||{records:[],media:[]};
  let items=[],media=[],searchItems=[];
  function date(s){
    if(!s)return 'Data não informada';
    if(/^\d{4}$/.test(s))return s;
    if(/^\d{4}-\d{2}$/.test(s))return new Intl.DateTimeFormat('pt-BR',{month:'short',year:'numeric',timeZone:'UTC'}).format(new Date(s+'-01T12:00:00Z'));
    const d=new Date(/^\d{4}-\d{2}-\d{2}$/.test(s)?s+'T12:00:00Z':s);
    return Number.isNaN(d.getTime())?'Data não informada':new Intl.DateTimeFormat('pt-BR',{day:'2-digit',month:'short',year:'numeric',timeZone:'UTC'}).format(d);
  }
  function openPane(id,scroll=false){
    if(id==='explorar')id='inicio';
    if(!titles[id])return;
    current=id;
    paneNodes.forEach(el=>el.classList.toggle('portal-pane-inactive',el.dataset.portalPane!==id));
    document.body.classList.toggle('portal-inner-page',id!=='inicio');
    $('portalPageName').textContent=titles[id];
    document.querySelectorAll('.portal-nav-link').forEach(el=>{if(el.hash==='#'+id)el.setAttribute('aria-current','page');else el.removeAttribute('aria-current');});
    if(scroll)window.scrollTo({top:0,behavior:'auto'});
  }
  function fromHash(scroll=false){
    const h=location.hash.slice(1);
    const dialogPane=h.startsWith('registro=')?'pesquisa':h.startsWith('ficha=')?'acervo':h.startsWith('midia=')?'midiateca':h.startsWith('comparacao=')?'comparacoes':h.startsWith('apuracao=')?'apuracoes':null;
    if(titles[h]||h==='explorar')openPane(h,scroll);
    else if(dialogPane)openPane(dialogPane,scroll);
    else if(!h)openPane('inicio',scroll);
  }
  const researchAttr=i=>`data-research-id="${esc(i.id)}"`;
  function card(i){
    const attrs=i._kind==='case'?`data-action="case" data-id="${esc(i.id)}"`:i._kind==='media'?`data-action="media" data-id="${esc(i.id)}"`:researchAttr(i);
    const label=i._kind==='case'?'Ficha da edição anterior':i._kind==='media'?'Registro audiovisual':formats[i.format]||'Material documental';
    const status=i._kind==='case'?(i.verdict+' / edição anterior'):i._kind==='media'?'Ver contexto':'Revisão pendente';
    const ico=i.format==='audio'?'headphones':i.format==='video'||i._kind==='media'?'play':i._kind==='case'?'check':'file';
    const pub=i.publisher||i.creditShort||i.sources?.[0]?.publisher||'Fonte identificada';
    const summary=i.summary||i.description||i.claim||'Abra o registro para consultar a procedência.';
    return `<article class="portal-record"><div class="portal-record-top"><span class="portal-record-type">${icon(ico)}${esc(label)}</span><span class="portal-record-status">${esc(status)}</span></div><h3><button ${attrs}>${esc(i.title)}</button></h3><p>${esc(summary)}</p><div class="portal-record-bottom"><span title="${esc(pub)}">${esc(pub)} · ${esc(date(i.date||i.statementDate))}</span><button ${attrs} aria-label="Abrir registro: ${esc(i.title)}">Abrir ${icon('arrow')}</button></div></article>`;
  }
  function rebuild(){
    items=(report.items||[]).filter(i=>/^[a-z0-9-]+$/.test(i.id||'')&&i.title&&safe(i.url));
    const seen=new Set();media=[];
    for(const m of [...(legacy.media||[]),...(report.media||[])]){
      const keys=[m.sourceUrl,m.url,m.youtubeId].filter(Boolean);
      if(!m.id||!m.title||keys.some(k=>seen.has(k)))continue;
      media.push(m);keys.forEach(k=>seen.add(k));
    }
    // Search distinct records. Documentary source links are not counted as separate verdicts.
    searchItems=[...items.map(i=>({...i,_kind:'research'})),...(legacy.records||[]).map(i=>({...i,_kind:'case',_person:i.person==='jair'?'Jair Bolsonaro':'Flávio Bolsonaro'})),...media.filter(m=>!items.some(i=>i.id===m.id||i.url===m.sourceUrl||i.url===m.url)).map(i=>({...i,_kind:'media'}))].map(i=>({...i,_search:norm([i.title,i.summary,i.description,i.claim,i.topic,i.publisher,i._person,...(i.topics||[]),...(i.tags||[]),i.factualQuestion,i.locator].filter(Boolean).join(' '))}));
    const metrics=[[items.length,'materiais','no catálogo'],[items.filter(i=>i.format==='documento').length,'documentos','catalogados'],[media.length,'vídeos e áudios','acervo completo'],[(report.sources||[]).length,'fontes','mapeadas']];
    $('portalMetrics').innerHTML=metrics.map(([n,a,b])=>`<div class="portal-metric"><strong>${n}</strong><span><b>${esc(a)}</b>${esc(b)}</span></div>`).join('');
    const parliamentary=items.filter(i=>i.publisher==='Senado Federal').length;
    const comparisons=(legacy.comparisons||[]).filter(i=>i.person==='flavio').length;
    $('portalCollections').innerHTML=[
      ['acervo','check','Falas e checagens',`${(legacy.records||[]).filter(r=>r.person==='flavio').length} fichas de Flávio`,null],
      ['midiateca','play','Vídeos e áudios','Entrevistas e publicações originais',null],
      ['pesquisa','folder','Atividade parlamentar',`${parliamentary} registros do Senado`,'parlamento'],
      ['apuracoes','quote','Frente Vorcaro','Documentos, cronologia e respostas',null]
    ].map(([href,k,t,d,q])=>`<a class="portal-collection" href="#${href}"${q?' data-portal-collection="'+q+'"':''}><span class="collection-icon">${icon(k)}</span><strong>${esc(t)}</strong><small>${esc(d)}</small><span class="collection-arrow">${icon('arrow')}</span></a>`).join('');
    $('portalRecent').innerHTML=[...items].sort((a,b)=>String(b.date||'').localeCompare(String(a.date||''))||a.title.localeCompare(b.title,'pt-BR')).slice(0,6).map(card).join('');
    const videoItems=media.filter(m=>m.type==='video'&&/^[\w-]{11}$/.test(m.youtubeId||'')&&(m.people||m.persons||[]).includes('flavio')).sort((a,b)=>String(b.date||'').localeCompare(String(a.date||''))).slice(0,3);
    $('portalVideos').innerHTML=videoItems.map(m=>{
      const local=/^assets\/[\w.-]+$/.test(m.thumbnail||'')?m.thumbnail:null;
      const thumb=local||`https://i.ytimg.com/vi/${m.youtubeId}/hqdefault.jpg`;
      const pub=m.creditShort||m.publisher||m.credit||'Publicador';
      return `<article class="portal-video"><button class="portal-video-cover" data-action="media" data-id="${esc(m.id)}" aria-label="Abrir vídeo: ${esc(m.title)}"><strong>${esc(pub)}</strong><img src="${esc(thumb)}" alt="" width="480" height="270" loading="lazy" decoding="async" referrerpolicy="no-referrer"><span class="portal-video-play">${icon('play')}</span></button><div class="portal-video-meta"><span>${esc(pub)}</span><h3>${esc(m.title)}</h3><small>${esc(date(m.date))} · ${esc(m.role||'Registro do publicador')}</small></div></article>`;
    }).join('');
    if(!videoItems.length)$('portalVideos').innerHTML='<p class="portal-empty">Nenhum vídeo com origem identificada nesta seleção. Consulte a midiateca para todos os registros disponíveis.</p>';
    renderSearch();
  }
  function renderSearch(){
    const raw=$('portalSearch').value.trim(),tokens=norm(raw).split(/\s+/).filter(Boolean);
    $('portalSearchArea').hidden=!tokens.length;$('portalDiscovery').hidden=!!tokens.length;
    if(!tokens.length)return;
    const results=searchItems.filter(i=>tokens.every(t=>i._search.includes(t)));
    $('portalSearchStatus').textContent=`${results.length} resultados para “${raw}”`;
    $('portalSearchResults').innerHTML=results.slice(0,searchLimit).map(card).join('')||'<p class="portal-empty">Nenhum resultado. Tente outro assunto, nome ou palavra.</p>';
    $('portalSearchMore').hidden=results.length<=searchLimit;
  }
  let timer;
  $('portalSearch').addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(()=>{searchLimit=12;openPane('inicio');if(location.hash!=='#inicio')history.replaceState(null,'','#inicio');renderSearch();},140);});
  $('portalSearchClear').addEventListener('click',()=>{$('portalSearch').value='';renderSearch();$('portalSearch').focus();});
  $('portalSearchMore').addEventListener('click',()=>{searchLimit+=12;renderSearch();});
  $('portalSearchJump').addEventListener('click',()=>{history.pushState(null,'','#inicio');openPane('inicio',true);$('portalSearch').focus();});
  $('portalJair').addEventListener('click',()=>{openPane('acervo',true);history.pushState(null,'','#acervo');document.querySelector('[data-person="jair"]')?.click();});
  document.addEventListener('click',e=>{
    const a=e.target.closest('a[href^="#"]');if(!a)return;
    const id=a.getAttribute('href').slice(1);
    if(!titles[id]&&id!=='explorar')return;
    if(e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;
    e.preventDefault();
    if(a.dataset.portalCollection==='parlamento'){
      // A single publisher filter prevents treating every topic match as a parliamentary record.
      $('researchClear').click();$('researchPublisher').value='Senado Federal';$('researchPublisher').dispatchEvent(new Event('change',{bubbles:true}));
    }
    history.pushState(null,'','#'+id);openPane(id,true);
    $('mobileMenu').hidden=true;$('menuToggle').setAttribute('aria-expanded','false');
    if(id==='explorar')$('portalSearch').focus();
  });
  document.addEventListener('keydown',e=>{
    if(e.key==='/'&&!e.ctrlKey&&!e.metaKey&&!document.querySelector('dialog[open]')&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)){
      e.preventDefault();openPane('inicio');$('portalSearch').focus();
    }
  },true);
  document.addEventListener('error',e=>{if(e.target.tagName==='IMG'&&e.target.closest('.portal-video-cover'))e.target.hidden=true;},true);
  document.addEventListener('arquivo-navigate',e=>{if(titles[e.detail?.pane])openPane(e.detail.pane,false);});
  document.addEventListener('arquivo-research',e=>{
    const c=e.detail;
    if(!c||c.schemaVersion!==1||!Array.isArray(c.items)||c.items.length>10000)return;
    if(new Date(c.metadata?.generatedAt||0)<=new Date(report.metadata?.generatedAt||0))return;
    report=c;rebuild();
  });
  for(const id of ['researchDialog','caseDialog'])$(id).addEventListener('close',()=>fromHash(false));
  window.addEventListener('hashchange',()=>fromHash(true));
  window.addEventListener('popstate',()=>fromHash(true));
  // Short mobile labels without changing the full accessible names.
  const mobileLabels={inicio:'Início',pesquisa:'Catálogo',acervo:'Checagens',midiateca:'Mídias',fontes:'Fontes'};
  document.querySelectorAll('.portal-bottom-nav a').forEach(a=>{const label=a.querySelector('span');if(label)label.textContent=mobileLabels[a.hash.slice(1)]||label.textContent;});
  openPane('inicio');rebuild();fromHash();
})();
