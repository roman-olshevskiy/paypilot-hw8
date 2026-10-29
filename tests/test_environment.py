"""Explicit read-only readiness: no POST /chat or judge inference."""
import unittest,os,sys,json,urllib.request,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hw8_common import load_env,save
@unittest.skipUnless(os.environ.get('HW8_ENV')=='1','Explicit read-only external check disabled')
class Environment(unittest.TestCase):
 def test_readonly_services_and_catalog(self):
  load_env();opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
  def get(url,headers=None):
   with opener.open(urllib.request.Request(url,headers=headers or {}),timeout=45) as r:return json.load(r)
  health=get('http://localhost:8000/health');self.assertEqual(health['provider'],'openrouter')
  defects=get('http://localhost:8000/api/_test/defects');prompt=get('http://localhost:8000/api/_test/prompt')
  self.assertIn('lesson-09',defects['known_profiles']);self.assertTrue(prompt)
  self.assertEqual(get('http://localhost:3000/api/public/health').get('status'),'OK')
  key=os.environ.get('ANTHROPIC_API_KEY');self.assertTrue(key)
  models=get('https://api.anthropic.com/v1/models',{'x-api-key':key,'anthropic-version':'2023-06-01'})
  safe=[{k:m[k] for k in ['id','display_name','created_at'] if k in m} for m in models['data']]
  save(ROOT/'evidence/environment/anthropic-models.json',{'models':safe,'has_more':models.get('has_more'),'scope':'GET models only; no inference'})
  script="import os,json;print(json.dumps({k:os.environ.get(k,'') for k in ['LLM_PROVIDER','LLM_MODEL','CLOCK_OVERRIDE','HTTPS_PROXY','TRACE_CAPTURE_CONTENT']}))"
  runtime=json.loads(subprocess.check_output(['docker','compose','exec','-T','stand','python','-c',script],cwd=ROOT.parent/'paypilot-stand-shared',text=True))
  self.assertEqual(runtime['LLM_PROVIDER'],'openrouter');self.assertEqual(runtime['CLOCK_OVERRIDE'],'2026-09-15T10:00:00Z');self.assertFalse(runtime['HTTPS_PROXY']);self.assertEqual(runtime['TRACE_CAPTURE_CONTENT'],'1');self.assertTrue(health['trace_content'])
  save(ROOT/'evidence/environment/readiness.json',{'health':health,'runtime':runtime,'defects':defects,'prompt':prompt,'paid_inference_calls':0,'recorded_at_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()})
  print('Agent provider:',health['provider']);print('Anthropic model IDs:',[m['id'] for m in safe])
