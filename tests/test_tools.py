import unittest,types,json,tempfile,sys,io
from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stdout
ROOT=Path(__file__).resolve().parents[1]
def module(name):
 path=ROOT/'scripts'/name
 result=types.ModuleType(name);result.__file__=str(path)
 exec(compile(path.read_text(),str(path),'exec'),result.__dict__)
 return result
class ImportTests(unittest.TestCase):
 def test_import_updates_records_without_delete_or_credential_output(self):
  tool=module('upload-algolia.py');requests=[]
  class Response(io.BytesIO):
   def __enter__(self):return self
   def __exit__(self,*args):self.close()
  def fake_urlopen(req,timeout=60):
   payload=json.loads(req.data) if req.data else None
   requests.append((req.get_method(),req.full_url,payload))
   if '/task/' in req.full_url:return Response(b'{"status":"published"}')
   if req.full_url.endswith('/query'):return Response(b'{"nbHits":2}')
   return Response(b'{"taskID":123}')
  with tempfile.TemporaryDirectory() as d:
   records=Path(d)/'records.json';settings=Path(d)/'settings.json'
   records.write_text(json.dumps([{'objectID':'one','title':'One','search_partition':0},{'objectID':'two','title':'Two','search_partition':0}]))
   settings.write_text('{"searchableAttributes":["title"]}')
   argv=['upload','--app-id','TESTAPP','--records',str(records),'--settings',str(settings)]
   out=io.StringIO()
   with patch.object(sys,'argv',argv),patch.object(tool.getpass,'getpass',return_value='private-test-key'),patch.object(tool,'urlopen',fake_urlopen),redirect_stdout(out):tool.main()
   self.assertNotIn('private-test-key',out.getvalue())
   self.assertIn('Import completed',out.getvalue())
   batch=next(body for method,url,body in requests if url.endswith('/batch'))
   self.assertEqual([r['action'] for r in batch['requests']],['addObject','addObject'])
   self.assertEqual([r['body']['objectID'] for r in batch['requests']],['one','two'])
   self.assertFalse(any(method=='DELETE' or '/clear' in url for method,url,body in requests))
 def test_duplicate_ids_fail_before_prompt_or_network(self):
  tool=module('upload-algolia.py')
  with tempfile.TemporaryDirectory() as d:
   records=Path(d)/'records.json';settings=Path(d)/'settings.json'
   records.write_text('[{"objectID":"one"},{"objectID":"one"}]');settings.write_text('{}')
   with patch.object(sys,'argv',['upload','--records',str(records),'--settings',str(settings)]),patch.object(tool.getpass,'getpass') as prompt,patch.object(tool,'urlopen') as network,redirect_stdout(io.StringIO()),patch('sys.stderr',io.StringIO()):
    with self.assertRaises(SystemExit):tool.main()
    prompt.assert_not_called();network.assert_not_called()
class ValidationTests(unittest.TestCase):
 def test_validation_detects_inconsistent_formats_and_duplicate_pages(self):
  tool=module('validate-data.py')
  row={'objectID':'one','title':'A','url':'https://torahinmotion.org/classes/a','date':'2026-11-01','date_timestamp':1793491200,'content_type':'Class','speakers':['Speaker'],'topics':['Topic'],'formats':[],'audio_url':'https://torahinmotion.org/file.mp3','search_partition':0}
  result=tool.inspect([row,dict(row)])
  self.assertIn('Duplicate objectIDs',result['validation_errors'])
  self.assertIn('Duplicate canonical URLs',result['validation_errors'])
  self.assertTrue(any('format mismatch' in e for e in result['validation_errors']))
if __name__=='__main__':unittest.main()
