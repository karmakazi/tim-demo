#!/usr/bin/env python3
"""Import the public prototype data without deleting existing index records.

The private write key is prompted locally and never saved or echoed.
"""
import argparse,getpass,json,re,time,sys
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import quote

def main():
 root=Path(__file__).resolve().parents[1]
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--app-id',default='JMCK1WQ9XL')
 parser.add_argument('--index',default='torah-demo-records')
 parser.add_argument('--records',type=Path,default=root/'records.json')
 parser.add_argument('--settings',type=Path,default=root/'algolia-settings.json')
 parser.add_argument('--dry-run',action='store_true',help='Validate files only; do not connect or ask for a key')
 args=parser.parse_args()
 if not re.fullmatch('[A-Za-z0-9]+',args.app_id):parser.error('Invalid Application ID')
 records=json.loads(args.records.read_text());settings=json.loads(args.settings.read_text())
 if not records or any(not r.get('objectID') for r in records):parser.error('Every record needs a stable objectID')
 if len({r['objectID'] for r in records})!=len(records):parser.error('Duplicate objectIDs')
 if any(not isinstance(r.get('search_partition'),int) for r in records):parser.error('Missing numeric search_partition')
 print(f'Validated {len(records)} records for {args.app_id} / {args.index}.')
 if args.dry_run:return
 key=getpass.getpass('Algolia write key (addObject + editSettings + search; kept local): ')
 if not key:parser.error('No key entered')
 base=f'https://{args.app_id}.algolia.net/1/indexes/{quote(args.index,safe="")}'
 def request(method,path,body=None):
  encoded=json.dumps(body,ensure_ascii=False).encode() if body is not None else None
  req=Request(base+path,data=encoded,method=method,headers={'Content-Type':'application/json','X-Algolia-Application-Id':args.app_id,'X-Algolia-API-Key':key})
  try:
   with urlopen(req,timeout=60) as response:return json.load(response)
  except HTTPError as e:
   # Avoid echoing headers, request objects, or private credential values.
   raise RuntimeError(f'Algolia returned HTTP {e.code}. Check key permissions and index restrictions.') from None
 def wait(task):
  for attempt in range(120):
   result=request('GET','/task/'+str(task))
   if result.get('status')=='published':return
   time.sleep(min(1+attempt/10,3))
  raise RuntimeError(f'Task {task} is still pending; inspect its status before retrying.')
 response=request('PUT','/settings',settings)
 if response.get('taskID') is not None:wait(response['taskID'])
 for start in range(0,len(records),100):
  batch=records[start:start+100]
  response=request('POST','/batch',{'requests':[{'action':'addObject','body':r} for r in batch]})
  wait(response['taskID'])
  print(f'Indexed {min(start+100,len(records))}/{len(records)}',flush=True)
 verify=request('POST','/query',{'query':'','hitsPerPage':0})
 print(f'Import completed. The index reports {verify.get("nbHits")} total records.')
 print('Stable objectIDs updated matching records. No existing records were deleted.')

if __name__=='__main__':
 try:main()
 except (RuntimeError,OSError,ValueError) as e:print(str(e),file=sys.stderr);sys.exit(1)
