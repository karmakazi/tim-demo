const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

// Exercise the real search code with an old-style index: no facet settings,
// no numeric timestamps, and no media fields on its search hits.
function setup() {
  const elements = new Map();
  const context = vm.createContext({
    document: {querySelector(selector) {
      if (!elements.has(selector)) elements.set(selector, {
        value:'', textContent:'', innerHTML:'', hidden:false,
        classList:{remove(){}, add(){}}
      });
      return elements.get(selector);
    }},
    window:{TORAH_SEARCH_CONFIG:{appId:'TEST',apiKey:'test-only',indexName:'test-index'}},
    localStorage:{getItem(){return null;}}, URL, console
  });
  const source = fs.readFileSync(path.join(__dirname,'../app.js'),'utf8');
  vm.runInContext(source.slice(0,source.indexOf("$('#class-list').addEventListener")),context);
  const rows = [
    {objectID:'1',title:'Palachi (Part 1)',series:'Palachi',speakers:['Dr. Marc Shapiro'],topics:[],date:'2026-10-19',formats:[]},
    {objectID:'3',title:'Palachi (Part 3)',series:'Palachi',speakers:['Dr. Marc Shapiro'],topics:[],date:'2026-11-02',formats:[]},
    {objectID:'5',title:'Palachi (Part 5)',series:'Palachi',speakers:['Dr. Marc Shapiro'],topics:[],date:'2026-11-16',formats:[]},
    {objectID:'a',title:'Chanukah A',series:'',speakers:['Rabbi Jay Kelman'],topics:['Chanukah'],date:'2026-11-13',formats:['Article']},
    {objectID:'b',title:'Chanukah B',series:'',speakers:['Rabbi Jay Kelman'],topics:['Chanukah'],date:'2026-11-13',formats:['Article']},
    {objectID:'c',title:'Chanukah C',series:'',speakers:['Rabbi Jay Kelman'],topics:['Chanukah'],date:'2025-12-01',formats:['Article']}
  ];
  context.rows=rows;
  vm.runInContext(`state.records=rows.map(r=>({...r,audio_url:r.series?'https://torahinmotion.org/'+r.objectID+'.mp3':''}));updateControls=()=>{};refreshFacets=()=>{};`,context);
  let requests=0;
  context.searchAlgolia=async params=>{
    assert.equal(params.facetFilters,undefined,'must work without index facet configuration');
    assert.equal(params.numericFilters,undefined,'must not rely on absent numeric date fields');
    requests++;
    return {hits:rows,nbHits:rows.length,nbPages:1};
  };
  const run=code=>vm.runInContext(code,context);
  const element=selector=>{run(`$('${selector}')`);return elements.get(selector);};
  return {run,element,requests:()=>requests,context};
}

test('live-style hits support speaker, topic, and inclusive date filters without index changes',async()=>{
  const h=setup();
  h.run("state.speakers.add('Dr. Marc Shapiro')");
  await h.run('run()');
  assert.match(h.element('#result-count').textContent,/3 talks & articles/);
  h.element('#date-from').value='2026-11-01';h.element('#date-to').value='2026-11-16';
  await h.run('run()');
  assert.match(h.element('#result-count').textContent,/2 talks & articles/);
  assert.match(h.element('#class-list').innerHTML,/Part 3/);
  assert.doesNotMatch(h.element('#class-list').innerHTML,/Part 1/);
  h.run("state.speakers.clear();state.topics.add('Chanukah')");
  h.element('#date-from').value='2026-11-13';h.element('#date-to').value='2026-11-13';
  await h.run('run()');
  assert.match(h.element('#result-count').textContent,/2 standalone · 2 talks & articles/);
  assert.equal(h.requests(),1,'changing filters reuses the same query result');
});

test('facet options come from live record fields, even without Algolia facets',async()=>{
  const h=setup();await h.run('loadOnlineFacets()');
  assert.equal(h.run("state.facets.speakers['Dr. Marc Shapiro']"),3);
  assert.equal(h.run("state.facets.topics.Chanukah"),3);
});

test('invalid ranges show an error, and clearing dates recovers',async()=>{
  const h=setup();h.element('#date-from').value='2026-11-16';h.element('#date-to').value='2026-11-01';
  await h.run('run()');assert.match(h.element('#status').textContent,/start date/);
  assert.equal(h.requests(),0);
  h.element('#date-from').value='';h.element('#date-to').value='';await h.run('run()');
  assert.equal(h.element('#status').hidden,true);assert.match(h.element('#result-count').textContent,/6 talks & articles/);
});

test('incomplete retrieval is reported instead of misleading empty filters',async()=>{
  const h=setup();h.context.searchAlgolia=async()=>({hits:h.context.rows,nbHits:1001,nbPages:1});
  await h.run('run()');assert.equal(h.element('#status').hidden,false);
  assert.match(h.element('#status').textContent,/retrieval limit/);
});
