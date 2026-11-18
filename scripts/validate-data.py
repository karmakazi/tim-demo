#!/usr/bin/env python3
"""Validate the public search sample and print a small quality report."""
import argparse,json,collections,hashlib,re
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit

def inspect(records):
 errors=[]
 def require(condition,message):
  if not condition:errors.append(message)
 ids=[r.get('objectID') for r in records];urls=[r.get('url') for r in records]
 require(len(ids)==len(set(ids)),'Duplicate objectIDs')
 require(len(urls)==len(set(urls)),'Duplicate canonical URLs')
 for i,r in enumerate(records):
  prefix=f'Record {i+1}: '
  require(bool(r.get('objectID')) and bool(r.get('title')),prefix+'missing ID/title')
  u=urlsplit(r.get('url',''));require(u.scheme=='https' and u.hostname=='torahinmotion.org',prefix+'invalid source URL')
  for field in ['speakers','topics','formats']:require(isinstance(r.get(field),list),prefix+'invalid '+field)
  require(isinstance(r.get('search_partition'),int),prefix+'missing numeric search_partition')
  try:
   date=datetime.strptime(r.get('date',''),'%Y-%m-%d').replace(tzinfo=timezone.utc)
   require(r.get('date_timestamp')==int(date.timestamp()),prefix+'date/timestamp mismatch')
  except ValueError:errors.append(prefix+'missing/invalid date')
  require(len(json.dumps(r,ensure_ascii=False).encode())<10000,prefix+'exceeds 10KB record budget')
  for key,label in [('audio_url','Audio'),('video_url','Video'),('pdf_url','Source sheet')]:
   value=r.get(key,'')
   if value:
    parsed=urlsplit(value);require(parsed.scheme=='https',prefix+'non-HTTPS media URL')
   require(bool(value)==(label in r.get('formats',[])),prefix+key+'/format mismatch')
 partitions=collections.Counter(r.get('search_partition') for r in records)
 require(all(n<=500 for n in partitions.values()),'Partition exceeds 500 records')
 series=collections.defaultdict(list)
 for r in records:
  if r.get('series'):series[r.get('series_id') or r['series']].append(r)
 gaps=[]
 for items in series.values():
  parts=sorted({int(r['part_number']) for r in items if isinstance(r.get('part_number'),(int,float)) and r['part_number']==int(r['part_number'])})
  if parts and (parts[0]>1 or len(parts)<parts[-1]-parts[0]+1):
   gaps.append({'series':items[0]['series'],'parts_present':parts,'note':'Sample may not include every part; no missing parts were invented.'})
 dates=[r['date'] for r in records if r.get('date')]
 return dict(record_count=len(records),content_types=dict(collections.Counter(r.get('content_type') for r in records)),date_range={'from':min(dates) if dates else '', 'to':max(dates) if dates else ''},years=dict(sorted(collections.Counter(r.get('date','')[:4] for r in records).items())),unique_speakers=len({v for r in records for v in r.get('speakers',[])}),unique_topics=len({v for r in records for v in r.get('topics',[])}),series_count=len(series),audio_records=sum(bool(r.get('audio_url')) for r in records),video_records=sum(bool(r.get('video_url')) for r in records),pdf_records=sum(bool(r.get('pdf_url')) for r in records),missing_speakers=sum(not r.get('speakers') for r in records),missing_topics=sum(not r.get('topics') for r in records),records_with_descriptions=sum(bool(r.get('description')) for r in records),partitions=dict(partitions),sampled_series_with_gaps=gaps,validation_errors=errors)

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('records',nargs='?',type=Path,default=Path(__file__).resolve().parents[1]/'records.json');parser.add_argument('--report',type=Path);args=parser.parse_args()
 report=inspect(json.loads(args.records.read_text()))
 if args.report:args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='sampled_series_with_gaps'},ensure_ascii=False,indent=2))
 if report['validation_errors']:raise SystemExit(1)
if __name__=='__main__':main()
