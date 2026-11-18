import concurrent.futures as cf, threading,time,json,gzip,hashlib,re,urllib.request,urllib.error
from pathlib import Path
from urllib.parse import urljoin,urlsplit,urlunsplit,unquote
from datetime import datetime,timezone
from bs4 import BeautifulSoup
REPO=Path(__file__).resolve().parents[1]
ROOT=REPO/'.crawl-cache'; ROOT.mkdir(exist_ok=True)
CACHE=ROOT/'cache'; CACHE.mkdir(exist_ok=True)
BASE='https://torahinmotion.org'; lock=threading.Lock(); next_request=0
errors=[]
def canonical(url):
 p=urlsplit(urljoin(BASE,url));path=re.sub(r'^/index\.php','',unquote(p.path));return urlunsplit(('https','torahinmotion.org',path.rstrip('/') or '/','',''))
def fetch(url):
 global next_request
 key=hashlib.sha256(url.encode()).hexdigest();p=CACHE/(key+'.gz')
 if p.exists():return gzip.decompress(p.read_bytes()).decode()
 for attempt in range(3):
  with lock:
   delay=max(0,next_request-time.monotonic());next_request=max(next_request,time.monotonic())+.34
  if delay:time.sleep(delay)
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'TiM-Search-Prototype/1.0 (public content research)','Accept':'text/html'})
   with urllib.request.urlopen(req,timeout=30) as r:
    content=r.read().decode('utf-8');final=r.geturl()
    if '/user/login' in final:raise ValueError('login required')
   p.write_bytes(gzip.compress(content.encode()));return content
  except urllib.error.HTTPError as e:
   if e.code not in [429,500,502,503,504]:raise
   time.sleep(3*(attempt+1))
  except (TimeoutError, OSError):
   if attempt==2:raise
   time.sleep(attempt+1)
 raise ValueError('retries exhausted')
def soup(url):return BeautifulSoup(fetch(url),'html.parser')
def text(el):return el.get_text(' ',strip=True) if el else ''
def uniq(xs):return list(dict.fromkeys(x for x in xs if x))
def date_value(value):
 m=re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s*(\d{4})',value)
 return datetime.strptime(m.group(0),'%B %d, %Y').strftime('%Y-%m-%d') if m else ''
def list_page(args):
 kind,page=args;url=f'{BASE}/{kind}?page={page}';s=soup(url);rows=[]
 for row in s.select('main .views-row'):
  a=row.select_one('h3 a')
  if not a:continue
  link=canonical(a['href']);title=text(a)
  if not link.startswith(BASE+'/'+kind+'/'):continue
  speakers=uniq(text(a) for a in row.select('.past-class--speaker a, .article-author--content a'))
  series=row.select_one('.past-class--program a');d=date_value(text(row.select_one('time')))
  if not d:
   for p in row.select('.past-class--details > p'):
    d=date_value(text(p))
    if d:break
  rows.append(dict(url=link,title=title,speakers=speakers,topics=uniq(text(a) for a in row.select('.article-tags--content a')),series=text(series),series_url=canonical(series['href']) if series else '',date=d,description=text(row.select_one('.article-body')),content_type='Class' if kind=='classes' else 'Article'))
 return rows

def detail(seed):
 r=dict(seed);url=r['url'];s=soup(url);main=s.select_one('main');article=main.select_one('article') if main else None
 if not main or not article:raise ValueError('no public content article')
 r['title']=text(main.select_one('h1')) or r['title'];r['source_url']=url;r['scraped_at']=datetime.now(timezone.utc).isoformat(timespec='seconds')
 r['source']='public_detail_page';r['objectID']=hashlib.sha256(url.encode()).hexdigest()[:20]
 canonical_tag=s.select_one('link[rel="canonical"]')
 if canonical_tag:r['url']=canonical(canonical_tag['href'])
 r['objectID']=hashlib.sha256(r['url'].encode()).hexdigest()[:20]
 if r['content_type']=='Class':
  for h in article.select('.event--meta h3'):
   val=h.find_next_sibling('p')
   if not val:continue
   label=text(h).lower()
   if label=='date':r['date']=date_value(text(val)) or r['date'];r['date_display']=text(val)
   if label=='program':
    a=val.find('a',href=True)
    if a:r['series']=text(a);r['series_url']=canonical(a['href'])
   if label=='topics':r['topics']=uniq(text(a) for a in val.select('a'))
  bios=article.select('.class--speakers .speaker-bio h3')
  if bios:r['speakers']=uniq(text(x) for x in bios)
  body=article.select_one('.field--name-body')
 else:
  authors=article.select('.article--metadata--author a')
  if authors:r['speakers']=uniq(text(x) for x in authors)
  r['topics']=uniq(text(x) for x in article.select('.article--metadata--tags a')) or r['topics']
  r['date']=date_value(text(article.select_one('.article--metadata--date'))) or r['date']
  body=article.select_one('.field--name-body')
 full=text(body);r['description']=(full[:700].rsplit(' ',1)[0]+'…' if len(full)>700 else full) or r.get('description','')
 # Store a bounded searchable excerpt rather than republishing the full article.
 r['description_source']='detail_excerpt' if full else 'listing_excerpt'
 links=[urljoin(url,a['href']) for a in article.select('.class--media a[href], .field--name-field-source-material a[href], a[href$=".pdf"]')]
 r['audio_urls']=uniq(u for u in links if '.mp3' in urlsplit(u).path.lower())
 r['video_urls']=uniq(u for u in links if urlsplit(u).hostname in ['youtu.be','youtube.com','www.youtube.com','vimeo.com','www.vimeo.com'])
 r['pdf_urls']=uniq(u for u in links if urlsplit(u).path.lower().endswith('.pdf'))
 for field,plural in [('audio_url','audio_urls'),('video_url','video_urls'),('pdf_url','pdf_urls')]:r[field]=r[plural][0] if r[plural] else ''
 r['formats']=(['Article'] if r['content_type']=='Article' else [])+(['Audio'] if r['audio_url'] else [])+(['Video'] if r['video_url'] else [])+(['Source sheet'] if r['pdf_url'] else [])
 r['date_timestamp']=int(datetime.strptime(r['date'],'%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp()) if r['date'] else 0
 r['series_id']=hashlib.sha256(r['series_url'].encode()).hexdigest()[:20] if r['series_url'] else ''
 m=re.search(r'\bpart\s+(\d+(?:\.\d+)?)',r['title'],re.I);r['part_number']=float(m[1]) if m else None
 lang=s.find('html');r['language']=lang.get('lang','') if lang else ''
 return r

def main():
 seeds={};jobs=[('classes',p) for p in range(100)]+[('articles',p) for p in range(35)]
 with cf.ThreadPoolExecutor(max_workers=2) as pool:
  for n,(job,result) in enumerate(zip(jobs,pool.map(list_page,jobs)),1):
   for r in result:seeds[r['url']]=r
   if n%20==0:print('Listing pages',n,'unique records',len(seeds),flush=True)
 # Keep the most recent 1,400 classes and 600 articles, preserving current records.
 old=json.load(open(REPO/'records.json'))
 for r in old:seeds.setdefault(canonical(r['url']),dict(r,url=canonical(r['url'])))
 selected=[]
 for kind,limit in [('Class',1400),('Article',600)]:
  rows=sorted((r for r in seeds.values() if r['content_type']==kind),key=lambda r:r.get('date',''),reverse=True)
  selected+=rows[:limit]
 json.dump(selected,open(ROOT/'seeds.json','w'),ensure_ascii=False,indent=2)
 print('Detail pages queued',len(selected),flush=True)
 results=[]
 def task(seed):
  try:return detail(seed)
  except Exception as e:
   errors.append(dict(url=seed['url'],error=str(e)));return None
 with cf.ThreadPoolExecutor(max_workers=2) as pool:
  for i,r in enumerate(pool.map(task,selected),1):
   if r:results.append(r)
   if i%50==0:
    json.dump(results,open(ROOT/'expanded-checkpoint.json','w'),ensure_ascii=False)
    print('Details',i,'/',len(selected),'valid',len(results),'errors',len(errors),flush=True)
 results=list({r['url']:r for r in results}.values())
 old_ids={canonical(r['url']):r['objectID'] for r in old}
 for r in results:r['objectID']=old_ids.get(canonical(r['url']),old_ids.get(canonical(r.get('source_url',r['url'])),r['objectID']))
 results.sort(key=lambda r:(r.get('date',''),r['title']),reverse=True)
 for i,r in enumerate(results):r['search_partition']=i//500
 json.dump(results,open(ROOT/'expanded-records.json','w'),ensure_ascii=False,indent=2)
 json.dump(errors,open(ROOT/'errors.json','w'),indent=2)
 print('COMPLETE',len(results),'records',len(errors),'errors',flush=True)
if __name__=='__main__':main()
