const $ = selector => document.querySelector(selector);
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const normalize = value => String(value ?? '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').trim();
const state = {records: [], speakers: new Set(), topics: new Set(), formats: new Set(), page: 0, request: 0, facets: null};
const pageSize = 20;
let timer;
let config = {...window.TORAH_SEARCH_CONFIG};
try { const stored = JSON.parse(localStorage.getItem('torah-search-config')); if (stored) config = {...config,...stored}; } catch {}
const online = () => Boolean(config.appId && config.apiKey && config.indexName);
const synonymGroups = [['shabbat','shabbos'],['bereishit','breisheet','bereshit','bereishis'],['chanukah','hanukkah','chanuka','hanukah'],['pesach','passover'],['sukkot','succot','sukkos']];
function tokens(text) {return normalize(text).replace(/[^a-z0-9\u0590-\u05ff]+/g,' ').split(' ').filter(Boolean).map(w => synonymGroups.find(g => g.includes(w))?.[0] || w);}
function record(item) {
  const array = value => Array.isArray(value) ? value : value ? [value] : [];
  return {...item, speakers: array(item.speakers), topics: array(item.topics), formats: array(item.formats)};
}
function url(value) {try {const u = new URL(value);return u.protocol === 'https:' && ['torahinmotion.org','www.torahinmotion.org','youtu.be','youtube.com','www.youtube.com'].includes(u.hostname) ? u.href : '';} catch {return '';}}
function highlight(value) {
  const terms = [...new Set(tokens($('#query').value))].sort((a,b) => b.length-a.length);
  if (!terms.length) return escapeHtml(value);
  const pattern = new RegExp('('+terms.join('|')+')','gi');
  return String(value ?? '').split(pattern).map((part,i) => i%2 ? '<mark>'+escapeHtml(part)+'</mark>' : escapeHtml(part)).join('');
}
function active() {return Boolean($('#query').value || $('#date-from').value || $('#date-to').value || state.speakers.size || state.topics.size || state.formats.size);}
function updateControls() {
  $('#clear-filters').hidden = !active();
  $('#clear-dates').hidden = !$('#date-from').value && !$('#date-to').value;
  $('#clear-from').hidden = !$('#date-from').value;
  $('#clear-to').hidden = !$('#date-to').value;
  for (const [key,prefix] of [['speakers','speaker'],['topics','tag']]) {
    $('#'+prefix+'-selected').innerHTML = [...state[key]].map(v => `<span class="selected-facet">${escapeHtml(v)}<button type="button" data-remove="${key}" data-value="${escapeHtml(v)}" aria-label="Remove ${escapeHtml(v)}">×</button></span>`).join('');
  }
  $('#format-options').innerHTML = ['Article','Audio','Video'].map(v => `<button type="button" class="format-option${state.formats.has(v)?' is-selected':''}" data-format="${v}" aria-pressed="${state.formats.has(v)}">${v.toLowerCase()}</button>`).join('');
}
function renderFacet(key,prefix) {
  const term = normalize($('#'+prefix+'-search').value);
  const values = state.facets?.[key] ? Object.keys(state.facets[key]) : [...new Set(state.records.flatMap(r => r[key]))];
  const matches = values.filter(v => !state[key].has(v) && normalize(v).includes(term)).sort((a,b) => a.localeCompare(b));
  $('#'+prefix+'-options').innerHTML = matches.length ? matches.map(v => `<button class="facet-option" type="button" data-facet="${key}" data-value="${escapeHtml(v)}">${escapeHtml(v)}</button>`).join('') : '<span class="status">No matches</span>';
}
function refreshFacets() {renderFacet('speakers','speaker');renderFacet('topics','tag');}
function localMatches() {
  const query = tokens($('#query').value);
  return state.records.map(r => {
    const title = tokens(r.title).join(' ');
    const text = tokens([r.title,r.description,...r.speakers,...r.topics,r.series].join(' ')).join(' ');
    const match = query.every(t => text.includes(t));
    return {...r,_score:query.reduce((s,t) => s+(title.includes(t)?2:0),0),_match:match};
  }).filter(r => r._match && ['speakers','topics','formats'].every(k => !state[k].size || r[k].some(v => state[k].has(v))) && (!$('#date-from').value || r.date >= $('#date-from').value) && (!$('#date-to').value || r.date <= $('#date-to').value))
    .sort((a,b) => b._score-a._score || (b.date||'').localeCompare(a.date||''));
}
function resultCard(r) {
  const link = url(r.url);
  const date = r.date ? new Date(r.date.slice(0,10)+'T12:00:00') : null;
  const displayDate = date && !Number.isNaN(+date) ? date.toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric',year:'numeric'}) : '';
  const actions = [];
  if (r.content_type === 'Article' && link) actions.push(['Read article',link,'▤']);
  if (url(r.audio_url)) actions.push(['Listen',url(r.audio_url),'◖']);
  if (url(r.video_url)) actions.push(['Watch video',url(r.video_url),'▶']);
  if (!actions.length && link) actions.push(['View class',link,'↗']);
  return `<article class="class-card"><div class="class-card-content"><div class="class-date">${escapeHtml(displayDate)}</div><h3>${link?`<a href="${escapeHtml(link)}" target="_blank" rel="noopener">${highlight(r.title)}</a>`:highlight(r.title)}</h3>${r.description?`<p>${highlight(r.description)}</p>`:''}<div class="card-meta"><span class="speaker">${escapeHtml(r.speakers.join(' · '))}</span>${r.topics.length?`<span class="tags"><strong>Topics/Tags:</strong> ${escapeHtml(r.topics.join(' · '))}</span>`:''}${r.series?`<span class="series">${escapeHtml(r.series)}</span>`:''}</div></div><div class="format-actions">${actions.map(([label,href,icon]) => `<a class="format-action" href="${escapeHtml(href)}" target="_blank" rel="noopener" aria-label="${escapeHtml(label+': '+r.title)}"><span aria-hidden="true">${icon}</span>${label}<span aria-hidden="true">→</span></a>`).join('')}</div></article>`;
}
function results(hits,total,pages) {
  $('#status').hidden = true;
  $('#results-heading').textContent = active() ? 'Matching classes & articles' : 'All classes & articles';
  $('#result-count').textContent = `${total.toLocaleString()} ${total === 1 ? 'result' : 'results'}`;
  $('#class-list').innerHTML = hits.length ? hits.map(resultCard).join('') : '<div class="empty"><h3>No classes found</h3><p>Try broadening your search or clearing a filter.</p></div>';
  const start = Math.max(0,Math.min(state.page-2,pages-5));
  $('#pagination').innerHTML = pages > 1 ? `${state.page?`<button data-page="${state.page-1}" aria-label="Previous page">←</button>`:''}${Array.from({length:Math.min(5,pages)},(_,i) => start+i).map(p => `<button data-page="${p}" ${p===state.page?'aria-current="page"':''}>${p+1}</button>`).join('')}${state.page<pages-1?`<button data-page="${state.page+1}" aria-label="Next page">→</button>`:''}` : '';
}
async function searchAlgolia(params) {
  if (!/^[a-zA-Z0-9]+$/.test(config.appId)) throw Error('Check your Algolia Application ID.');
  const response = await fetch(`https://${config.appId}-dsn.algolia.net/1/indexes/${encodeURIComponent(config.indexName)}/query`, {method:'POST',headers:{'Content-Type':'application/json','X-Algolia-Application-Id':config.appId,'X-Algolia-API-Key':config.apiKey},body:JSON.stringify(params)});
  if (!response.ok) throw Error(response.status===403?'Algolia rejected the search key. Check its search permission and index restriction.':response.status===404?'Algolia index not found. Check the index name in settings.':'Algolia search failed. Check that speakers, topics, and formats are enabled for faceting.');
  return response.json();
}
async function run() {
  const request = ++state.request;
  updateControls();refreshFacets();
  $('#status').hidden = true;$('#status').classList.remove('error');
  $('#connection-status').textContent = online() ? `Algolia · ${config.indexName}` : `${state.records.length} public sample records · Local demo · Connect Algolia in settings`;
  const from = $('#date-from').value, to = $('#date-to').value;
  try {
    if (from && to && from > to) throw Error('The start date must be on or before the end date.');
    if (online()) {
      $('#result-count').textContent = 'Searching…';
      const facetFilters = ['speakers','topics','formats'].filter(k => state[k].size).map(k => [...state[k]].map(v => `${k}:${v.replace(/^-/,'\\-')}`));
      const numericFilters = [];
      if (from) numericFilters.push('date_timestamp>='+Date.parse(from+'T00:00:00Z')/1000);
      if (to) numericFilters.push('date_timestamp<='+Date.parse(to+'T00:00:00Z')/1000);
      const data = await searchAlgolia({query:$('#query').value,facetFilters,numericFilters,hitsPerPage:pageSize,page:state.page});
      if (request !== state.request) return;
      results(data.hits.map(record),data.nbHits,data.nbPages);
    } else {
      const matches = localMatches();
      results(matches.slice(state.page*pageSize,(state.page+1)*pageSize),matches.length,Math.ceil(matches.length/pageSize));
    }
  } catch(error) {
    if (request !== state.request) return;
    $('#status').hidden = false;$('#status').classList.add('error');$('#status').textContent = error.message || 'Unable to load search results.';
    $('#result-count').textContent = 'Search unavailable';$('#class-list').innerHTML = '';$('#pagination').innerHTML = '';
  }
}
async function loadOnlineFacets() {
  const identity = JSON.stringify(config);
  state.facets = null;
  if (!online()) {refreshFacets();return;}
  try {
    const data = await searchAlgolia({query:'',hitsPerPage:0,facets:['speakers','topics'],maxValuesPerFacet:1000});
    if (JSON.stringify(config)!==identity) return;
    state.facets = data.facets || {};refreshFacets();
  } catch { /* Main search displays connection failures; local facets remain available. */ }
}
function changed() {state.page=0;run();}
function clearAll() {
  $('#query').value='';$('#date-from').value='';$('#date-to').value='';
  for (const key of ['speakers','topics','formats']) state[key].clear();
  $('#speaker-search').value='';$('#tag-search').value='';changed();$('#query').focus();
}
$('#query').addEventListener('input',() => {clearTimeout(timer);timer=setTimeout(changed,180);});
$('#search-form').addEventListener('submit',e => {e.preventDefault();clearTimeout(timer);changed();});
for (const [key,prefix] of [['speakers','speaker'],['topics','tag']]) {
  $('#'+prefix+'-search').addEventListener('input',() => renderFacet(key,prefix));
  $('#'+prefix+'-options').addEventListener('click',e => {
    const b=e.target.closest('[data-facet]');if(!b)return;
    state[key].add(b.dataset.value);$('#'+prefix+'-search').value='';changed();$('#'+prefix+'-search').focus();
  });
  $('#'+prefix+'-selected').addEventListener('click',e => {const b=e.target.closest('[data-remove]');if(!b)return;state[key].delete(b.dataset.value);changed();$('#'+prefix+'-search').focus();});
  $('#'+prefix+'-search').addEventListener('keydown',e => {if(e.key==='Escape'){$('#'+prefix+'-search').blur();}if(e.key==='ArrowDown'){e.preventDefault();$('#'+prefix+'-options button')?.focus();}});
  $('#'+prefix+'-options').addEventListener('keydown',e => {const buttons=[...$('#'+prefix+'-options').querySelectorAll('button')],i=buttons.indexOf(document.activeElement);if(e.key==='ArrowDown'){e.preventDefault();buttons[(i+1)%buttons.length]?.focus();}if(e.key==='ArrowUp'){e.preventDefault();buttons[(i-1+buttons.length)%buttons.length]?.focus();}if(e.key==='Escape')$('#'+prefix+'-search').focus();});
}
$('#format-options').addEventListener('click',e => {const b=e.target.closest('[data-format]');if(!b)return;state.formats.has(b.dataset.format)?state.formats.delete(b.dataset.format):state.formats.add(b.dataset.format);changed();});
for(const side of ['from','to']) {
  $('#date-'+side).addEventListener('change',changed);
  $('#clear-'+side).addEventListener('click',() => {$('#date-'+side).value='';changed();});
}
$('#clear-dates').addEventListener('click',() => {$('#date-from').value='';$('#date-to').value='';changed();});
$('#clear-filters').addEventListener('click',clearAll);
$('#toggle-filters').addEventListener('click',() => {const hidden=!$('#filter-controls').hidden;$('#filter-controls').hidden=hidden;$('#toggle-filters').setAttribute('aria-expanded',String(!hidden));$('#toggle-filters').textContent=hidden?'Show filters':'Hide filters';});
$('#pagination').addEventListener('click',e => {const b=e.target.closest('[data-page]');if(!b)return;state.page=Number(b.dataset.page);run();$('#results-heading').scrollIntoView({block:'start'});});
$('#connect').addEventListener('click',() => {for(const k of ['appId','apiKey','indexName'])$('#configform').elements[k].value=config[k]|| (k==='indexName'?'torah-demo-records':'');$('#settings').showModal();});
$('#close').addEventListener('click',() => $('#settings').close());
$('#configform').addEventListener('submit',e => {e.preventDefault();config=Object.fromEntries([...new FormData(e.target)].map(([k,v]) => [k,v.trim()]));try{localStorage.setItem('torah-search-config',JSON.stringify(config));}catch{}$('#settings').close();state.page=0;run();loadOnlineFacets();});
$('#disconnect').addEventListener('click',() => {config={indexName:'torah-demo-records'};try{localStorage.removeItem('torah-search-config');}catch{}state.facets=null;$('#settings').close();changed();});
fetch('records.json').then(r => {if(!r.ok)throw Error('The sample records could not be loaded.');return r.json();}).then(data => {state.records=data.map(record);run();loadOnlineFacets();}).catch(error => {$('#status').textContent=error.message;$('#status').classList.add('error');});
