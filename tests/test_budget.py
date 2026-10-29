import unittest,tempfile,sys,json
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import hw8_budget as b
from hw8_common import save
class StopBudget(unittest.TestCase):
 def test_agent_request_ids_not_double_counted(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(b,'ROOT',Path(tmp)):
   row={'response':{'request_id':'r1'},'trace':{'name':'agent.request','children':[{'name':'llm.call','attributes':{'provider.cost_usd':.01}}]}}
   save(Path(tmp)/'evidence/runs/a/agent-captures.json',[row]);save(Path(tmp)/'evidence/runs/b/agent-captures.json',[row]);self.assertEqual(float(b.spent('openrouter')),.01)
 def test_missing_price_is_not_free(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(b,'ROOT',Path(tmp)):
   save(Path(tmp)/'evidence/runs/a/agent-captures.json',[{'response':{'request_id':'r1'},'trace':{'name':'llm.call','attributes':{}}}])
   with self.assertRaises(RuntimeError):b.spent('openrouter')
 def test_before_call_reserve_stops_next_inference(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(b,'ROOT',Path(tmp)):
   save(Path(tmp)/'evidence/campaign-budget.json',{'remaining_limits_usd':{'anthropic':.005},'pilot_baseline_usd':{'anthropic':0}})
   with self.assertRaises(RuntimeError):b.check('anthropic')
 def test_atomic_json_save_leaves_no_partial_file(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'data.json';save(p,{'x':[1,2,3]});self.assertEqual(json.loads(p.read_text()),{'x':[1,2,3]});self.assertEqual(len(list(Path(tmp).iterdir())),1)
