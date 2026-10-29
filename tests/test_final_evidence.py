import unittest,json,sys,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class FinalEvidence(unittest.TestCase):
 def test_all_frozen_labels_and_calibration_cohorts(self):
  sys.path.insert(0,str(ROOT/'tools'));from hw8_guard import verify_freeze
  verify_freeze();idx=json.loads((ROOT/'evidence/calibration-index.json').read_text(encoding='utf-8'))
  for name,expected in [('baseline_v1',[25,30]),('v2',[24,30])]:
   r=json.loads((ROOT/idx[name]).read_text(encoding='utf-8'));self.assertEqual(r['status'],'complete');self.assertEqual(r['agreement'],expected);self.assertEqual(len(r['cases']),30)
   for c in r['cases']:self.assertEqual(len(c['outputs']),5);self.assertEqual(len(c['verdicts']),5)
 def test_raw_counts_unique_ids_and_manifest_hashes(self):
  ids=[]
  for p in (ROOT/'evidence/runs').glob('*/agent-captures.json'):
   m=json.loads((p.parent/'manifest.json').read_text(encoding='utf-8'))
   for name,h in m['sha256'].items():self.assertEqual(hashlib.sha256((p.parent/name).read_bytes()).hexdigest(),h)
   ids += [r['response']['request_id'] for r in json.loads(p.read_text(encoding='utf-8'))]
  self.assertEqual(len(ids),110);self.assertEqual(len(set(ids)),110);calls=list((ROOT/'evidence/judge-calls').glob('*/call.json'));self.assertEqual(len(calls),336)
  response_ids=[json.loads(p.read_text(encoding='utf-8'))['response_id'] for p in calls];self.assertEqual(len(set(response_ids)),336)
 def test_all_verbatim_quotes_remain_exact(self):
  for p in (ROOT/'evidence/judge-calls').glob('*/call.json'):
   r=json.loads(p.read_text(encoding='utf-8'))
   if r.get('parsed'):
    prompt=r['request_body']['messages'][0]['content'];answer=prompt.split('AGENT ANSWER:\n',1)[1].split('\n\nRUBRIC:',1)[0];self.assertIn(r['parsed']['quote'],answer)
 def test_replay_exit_and_no_live_work(self):
  proof=json.loads((ROOT/'evidence/clean-clone-replay.json').read_text(encoding='utf-8'));self.assertTrue(proof['clean_before_and_after'])
  for r in proof['results']:self.assertEqual(r['verdicts_reproduced'],7);self.assertEqual(r['native_exit'],1);self.assertEqual(r['real_http_calls'],0);self.assertEqual(r['real_model_calls'],0)
 def test_agent_prompt_snapshot_hashes_preserved(self):
  idx=json.loads((ROOT/'evidence/calibration-index.json').read_text(encoding='utf-8'))
  for name in ['baseline_v1','v2']:
   r=json.loads((ROOT/idx[name]).read_text(encoding='utf-8'));self.assertEqual(hashlib.sha256((ROOT/r['agent_prompt_snapshot']).read_bytes()).hexdigest(),r['agent_prompt_snapshot_sha256'])
