// Testes de lógica e integração DOM simulada. Não substituem um navegador.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const root=new URL('../',import.meta.url), read=p=>fs.readFileSync(new URL(p,root),'utf8');
const html=read('dist/index.html');
class Element {
  constructor(id,tag='DIV'){this.id=id;this.tagName=tag;this.value='';this.hidden=false;this.open=false;this.dataset={};this.style={};this.listeners={};this.options=[];this.attributes={};this._html='';this._text='';this._classes=new Set();this.classList={toggle:(name,force)=>{const enabled=force??!this._classes.has(name);if(enabled)this._classes.add(name);else this._classes.delete(name);return enabled;},add:name=>this._classes.add(name),remove:name=>this._classes.delete(name),contains:name=>this._classes.has(name)};}
  set innerHTML(v){this._html=v;if(this.tagName==='SELECT'){this.options=[...v.matchAll(/<option(?: value="([^"]*)")?[^>]*>(.*?)<\/option>/g)].map(m=>({value:m[1]??m[2]}));this.value=this.options[0]?.value||'';}}
  get innerHTML(){return this._html;}
  set textContent(v){this._text=String(v);} get textContent(){return this._text;}
  setAttribute(k,v){this.attributes[k]=v;}
  addEventListener(k,f){(this.listeners[k]??=[]).push(f);}
  dispatch(k,event={}){for(const f of this.listeners[k]||[])f({target:this,...event});}
  showModal(){this.open=true;} close(){this.open=false;this.dispatch('close');}
  querySelectorAll(){return [];} getBoundingClientRect(){return {left:0,right:100,top:0,bottom:100};}
  focus(){this.focused=true;document.activeElement=this;} scrollIntoView(){}
}
const portalPanes=[...html.matchAll(/<section\b[^>]*data-portal-pane="([^"]+)"[^>]*>/g)].map(m=>({dataset:{portalPane:m[1]},classList:{toggle(){}}}));
const nodes=new Map();for(const m of html.matchAll(/<([a-z][a-z0-9]*)\b[^>]*\bid="([^"]+)"[^>]*>/g)){assert(!nodes.has(m[2]),'ID HTML repetido: '+m[2]);nodes.set(m[2],new Element(m[2],m[1].toUpperCase()));}
for(const m of html.matchAll(/<select\b[^>]*id="([^"]+)"[^>]*>([\s\S]*?)<\/select>/g))nodes.get(m[1]).innerHTML=m[2];
const events={},storage=new Map();
const document={getElementById(id){assert(nodes.has(id),'Elemento inexistente: '+id);return nodes.get(id);},body:new Element('body'),documentElement:new Element('html'),activeElement:{tagName:'BODY'},visibilityState:'visible',querySelectorAll(s){if(s==='dialog')return [...nodes.values()].filter(n=>n.tagName==='DIALOG');if(s==='dialog[open]')return [...nodes.values()].filter(n=>n.open);if(s==='[data-portal-pane]')return portalPanes;return [];},querySelector(s){return s==='dialog[open]'?[...nodes.values()].find(n=>n.open):null;},addEventListener(k,f){(events[k]??=[]).push(f);},dispatchEvent(e){for(const f of events[e.type]||[])f(e);}};
const location={protocol:'file:',hostname:'localhost',href:'file:///dist/index.html',hash:''};
const sandbox={document,location,console,URL,Map,Set,Date,Intl,JSON,Blob,structuredClone,AbortController,CustomEvent:class{constructor(type,o){this.type=type;this.detail=o.detail;}},setTimeout(f){f();return 1;},clearTimeout(){},setInterval(){},matchMedia(){return {matches:false};},localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)},navigator:{clipboard:{writeText:async()=>{}}},history:{pushState(a,b,h){location.hash=h;},replaceState(a,b,h){location.hash=h;}},requestAnimationFrame:f=>f(),scrollTo(){},innerHeight:900,scrollY:0,addEventListener(k,f){(events[k]??=[]).push(f);},fetch:async()=>{throw new Error('Rede desativada em teste');}};
sandbox.window=sandbox;vm.createContext(sandbox);
for(const p of ['dist/data/acervo.js','dist/data/news.js','dist/data/editorial-updates.js','dist/data/research.js'])vm.runInContext(read(p),sandbox,{filename:p});
// Meta lógica: 1.000 materiais, com dados sintéticos somente nesta VM.
while(sandbox.ARQUIVO_RESEARCH.items.length<999){const n=sandbox.ARQUIVO_RESEARCH.items.length;sandbox.ARQUIVO_RESEARCH.items.push({id:'synthetic-scale-'+n,title:'Registro sintético de desempenho '+n,url:'https://example.org/fixture/'+n,publisher:'Teste técnico',date:'2004-01-01',year:2004,format:'registro',topic:'Teste',stage:'encontrado',summary:'Fixture técnica, nunca persistida no catálogo.'});}
// Texto hostil permanece dado, e URL de script fica fora do catálogo.
sandbox.ARQUIVO_RESEARCH.items.push({id:'synthetic-sanitizer',title:'<img src=x onerror=alert(1)>',url:'https://example.org/synthetic-test',publisher:'Teste técnico',format:'registro',stage:'encontrado',summary:'<script>alert(1)</script>',topic:'Teste'});
sandbox.ARQUIVO_RESEARCH.items.push({id:'synthetic-script-url',title:'Não deve aparecer',url:'javascript:alert(1)'});
vm.runInContext(read('dist/assets/app.js'),sandbox,{filename:'app.js'});
vm.runInContext(read('dist/assets/research.js'),sandbox,{filename:'research.js'});
vm.runInContext(read('dist/assets/portal.js'),sandbox,{filename:'portal.js'});
const get=id=>nodes.get(id), input=(id,v,k='change')=>{get(id).value=v;get(id).dispatch(k);};
assert.equal(get('newMaterialCount').textContent,'1000');assert.equal((get('researchList').innerHTML.match(/class="catalog-row"/g)||[]).length,12);
assert.equal(get('statCases').textContent,'26');assert.match(get('resultsStatus').innerHTML,/>26</);
input('searchInput','mascaras','input');assert.match(get('resultsStatus').innerHTML,/>0</);get('clearFilters').dispatch('click');
input('caseSourceFilter','Aos Fatos');assert(!get('caseGrid').innerHTML.includes('<strong>Jair Bolsonaro</strong>'),'Filtro atribuiu registro a outro autor');
input('researchQuery','Vorcaro','input');assert.match(get('researchList').innerHTML,/Vorcaro/i);assert.doesNotMatch(get('researchList').innerHTML,/synthetic-sanitizer/);
get('researchClear').dispatch('click');input('researchFormat','video');assert.doesNotMatch(get('researchList').innerHTML,/Checagem do veículo/);
get('researchClear').dispatch('click');input('researchStage','revisado');assert.equal(get('researchResults').textContent,'0 materiais encontrados');
get('researchClear').dispatch('click');input('researchQuery','synthetic','input');
// Pesquisa por ID não é recurso. Abrir o item diretamente testa o caminho de detalhe.
const fakeClickedButton={dataset:{researchId:'synthetic-sanitizer'},closest(){return null;}};
for(const f of events.click||[])f({target:{closest:sel=>sel==='button'||sel==='button,a'?fakeClickedButton:null}});
assert(get('researchDialog').open);assert.match(get('researchContent').innerHTML,/&lt;img/);assert.doesNotMatch(get('researchContent').innerHTML,/<script>alert/);
assert(!get('researchList').innerHTML.includes('javascript:'));
get('researchDialog').close();assert.equal(location.hash,'#pesquisa');
input('sourceSearch','Senado','input');assert.match(get('sourceMap').innerHTML,/Senado/);
assert.match(get('coverageRows').innerHTML,/2003/);assert.match(get('reviewedAudioCount').textContent,/0 min/);
assert.equal(get('portalPageName').textContent,'Catálogo documental');
assert.match(get('documentList').innerHTML,/https:\/\/portal\.tcu\.gov\.br/);
assert.doesNotMatch(get('documentList').innerHTML,/href="documentos\//);
get('portalSearchJump').dispatch('click');
assert.equal(get('portalPageName').textContent,'Visão geral');
assert(get('portalSearch').focused,'Botão de busca móvel deve focar a busca geral');
input('portalSearch','Vorcaro','input');
assert.equal(get('portalSearchArea').hidden,false);assert(document.body.classList.contains('portal-searching'));
assert.match(get('portalSearchResults').innerHTML,/Vorcaro/i);
get('portalSearchClear').dispatch('click');
assert.equal(get('portalSearchArea').hidden,true);assert(!document.body.classList.contains('portal-searching'));
location.hash='#registro=synthetic-sanitizer';
for(const f of events.hashchange||[])f({});
assert.equal(get('portalPageName').textContent,'Catálogo documental');
assert(get('researchDialog').open,'Link direto de registro deve abrir a ficha');
get('researchDialog').close();
assert.equal(location.hash,'#pesquisa');
assert(!html.includes('portal-editorial-band'));assert(!html.includes('portal-hero-statement'));
assert(html.includes('class="editorial-nav"'),'Navegação editorial ausente');
assert(!html.includes('class="portal-sidebar"'),'Barra lateral administrativa ainda presente');
assert(html.includes('id="portalSearchLanding"'),'Busca principal ausente');
assert(!html.includes('>GitHub</a>') && !html.includes('class="sidebar-repository"') && !html.includes('aria-label="Código e histórico no GitHub"'));
console.log('Integração DOM simulada: catálogo, busca geral, botão móvel, rotas profundas, links oficiais, ações e integridade editorial passaram.');
