"""Explicit small paid pilot. Four stand chats and three recorded-answer judge calls.
No calibration agreement is inferred from these one-off pilot calls.
"""
import unittest,os,sys,json,datetime,uuid,hashlib,urllib.request,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from hw8_common import load_env,save,digest
from hw8_guard import require_paid

def private_key_usage():
 vals={}
 for line in (ROOT.parent/'paypilot-stand-shared/.env').read_text(encoding='utf-8-sig').splitlines():
  if '=' in line and not line.lstrip().startswith('#'):
   k,v=line.split('=',1);vals[k.strip()]=v.strip().strip(chr(34)).strip(chr(39))
 req=urllib.request.Request('https://openrouter.ai/api/v1/key',headers={'Authorization':'Bearer '+vals['OPENROUTER_API_KEY']})
 with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req,timeout=45) as r:data=json.load(r)['data']
 return {k:data.get(k) for k in ['usage','byok_usage']}

@unittest.skipUnless(os.environ.get('HW8_PILOT')=='1','Explicit paid pilot disabled')
class Pilot(unittest.TestCase):
 def test_small_pilot(self):
  load_env();require_paid();import stand,judge
  stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'evidence/runs'/f'{stamp}-pilot-{uuid.uuid4().hex[:8]}';folder.mkdir(parents=True)
  before=stand.profile();rows=[];judged=[];error=None;agent_attempts=0;judge_attempts=0
  manifest={'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'frozen_inputs':json.loads((ROOT/'evidence/labels-freeze.json').read_text(encoding='utf-8')),'scope':'Pilot only: 4 agent chats,3 judge calls, one per condition/case, not final 5-run calibration','before':before,'agent_attempts':0,'judge_attempts':0,'error':None}
  save(folder/'manifest.json',manifest)
  private=ROOT.parent/'Lectures/HW08/work/billing';private.mkdir(exist_ok=True)
  save(private/(folder.name+'-before.json'),private_key_usage())
  try:
   cases={c['id']:c for c in [json.loads(x) for x in (ROOT/'evals/sets/l09_labels.jsonl').read_text(encoding='utf-8').splitlines()]}
   for ident in ['HW8-01','HW8-11','HW8-25']:
    c=cases[ident];judge_attempts+=1;manifest['judge_attempts']=judge_attempts;save(folder/'manifest.json',manifest)
    result=judge.judge(c['input'],c['answer_under_test'],c['additional_metadata']['rubric'],os.environ['JUDGE_MODEL'],float(os.environ['TEMP']))
    judged.append({'case_id':ident,'label':c['additional_metadata']['label'],'result':result});save(folder/'judge-results.json',judged)
    self.assertEqual(result['temperature'],.7);self.assertEqual(result['judge_model'],'claude-haiku-4-5-20251001')
   working=[json.loads(x) for x in (ROOT/'sets/l09_escalation.jsonl').read_text(encoding='utf-8').splitlines()][:2]
   for profile in ['clean','lesson-09']:
    stand.set_profile(profile);stand.set_defects('')
    for c in working:
     stand.reset();agent_attempts+=1;manifest['agent_attempts']=agent_attempts;save(folder/'manifest.json',manifest)
     started=time.perf_counter();answer=stand.chat(c['input']);row={'case_id':c['id'],'profile':profile,'input':c['input'],'response':answer,'duration_ms':round((time.perf_counter()-started)*1000),'trace':None,'disputes':None};rows.append(row);save(folder/'agent-captures.json',rows)
     row['trace']=stand.trace(answer['request_id']);row['disputes']=stand.state('disputes');row['escalate_to_human']=stand.has_span(row['trace'],'tool.escalate_to_human') or stand.has_span(row['trace'],'escalate_to_human');save(folder/'agent-captures.json',rows)
     self.assertIsNotNone(row['trace']);self.assertTrue(answer.get('request_id'))
   self.assertEqual(len(judged),3);self.assertEqual(len(rows),4)
  except Exception as e:error=f'{type(e).__name__}: {e}';raise
  finally:
   try:
    stand.set_profile(before['profile']);stand.set_defects(','.join(before.get('extra_defects',[])));manifest['restored']=stand.profile()
   except Exception as e:manifest['restore_error']=str(e)
   try:save(private/(folder.name+'-after.json'),private_key_usage())
   except Exception as e:manifest['billing_read_error']=str(e)
   manifest.update(error=error,finished_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),agent_attempts=agent_attempts,judge_attempts=judge_attempts)
   manifest['sha256']={p.name:digest(p) for p in folder.glob('*.json') if p.name!='manifest.json'};save(folder/'manifest.json',manifest)
   save(ROOT/'evidence/pilot-index.json',{'folder':str(folder.relative_to(ROOT)),'status':'complete' if error is None else 'ERROR'});print('PILOT CAPTURE',folder)
