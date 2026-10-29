import unittest,sys,json,os,tempfile,types,math
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
import loader,judge,stand
import calibrate_run as cal
from hw8_guard import require_paid

def sample(label='PASS',disputed=False):return {'id':'TEST','input':'Question','answer_under_test':'Recorded answer','additional_metadata':{'layer':'judge','oracle':'human','assertion':'judge','source':'fixture','severity':'high','gate':'release','runs':5,'rubric':'Rubric','criterion':'Criterion','rubric_version':'rubric.v1','label':label,'labeled_on':'2026-10-29','label_status':'human_review_confirmed','disputed':disputed,'ground_truth_from':'text','why_disputed':'boundary'}}
class Calibration(unittest.TestCase):
 def test_wilson_small_sample_and_empty(self):
  w=cal.wilson(25,30);self.assertAlmostEqual(w['low'],.66435,places=4);self.assertAlmostEqual(w['high'],.92664,places=4);self.assertAlmostEqual(w['half_width'],(w['high']-w['low'])/2);self.assertIsNone(cal.wilson(0,0)['estimate'])
 def test_majority_is_not_stability_and_matrix_direction(self):
  c=sample('FAIL',True);r=cal.case_result(c,[{'verdict':x} for x in ['PASS']*3+['FAIL']*2]);self.assertFalse(r['agree']);self.assertFalse(r['stable']);m=cal.metrics([r]);self.assertEqual(m['confusion_matrix']['missed_defect'],1);self.assertEqual(m['agreement'],[0,1]);self.assertEqual(m['groups']['disputed']['agreement']['n'],1)
 def test_recorded_answers_and_five_calls_not_agent(self):
  c=sample();seen=[]
  def fake(q,a,r,m,t):seen.append(a);return {'verdict':'PASS','quote':'Recorded','judge_model':m,'temperature':t}
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'set.jsonl';p.write_text(json.dumps(c)+'\n',encoding='utf-8');out=Path(tmp)/'report.json'
   with patch.object(stand,'_call',side_effect=AssertionError('No stand in calibration')):code,_,r=cal.run([c],p,'fixture-model',.7,infer=fake,output=out)
   self.assertEqual(code,0);self.assertEqual(seen,['Recorded answer']*5);self.assertEqual(r['agreement'],[1,1]);self.assertEqual(r['self_consistency'],[1,1]);self.assertEqual(r['runs'],5)
 def test_partial_paid_results_survive_next_failure(self):
  c=sample();hits=[]
  def fake(*args):
   hits.append(1)
   if len(hits)==2:raise ValueError('invalid JSON fixture')
   return {'verdict':'PASS','quote':'Recorded'}
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'input';p.write_text('fixture',encoding='utf-8');code,out,r=cal.run([c],p,'fixture',.7,infer=fake,output=Path(tmp)/'report.json');saved=json.loads(out.read_text(encoding='utf-8'));self.assertEqual(code,2);self.assertEqual(len(hits),2);self.assertEqual(saved['cases'][0]['verdicts'],['PASS']);self.assertIsNone(saved['cases'][0]['majority']);self.assertEqual(saved['incomplete_cases'],1)
 def test_disagreement_has_nonzero_exit(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'input';p.write_text('fixture');code,_,r=cal.run([sample('FAIL')],p,'fixture',.7,infer=lambda *x:{'verdict':'PASS'},output=Path(tmp)/'out.json');self.assertEqual(code,1)
 def test_draft_cannot_become_human_label(self):
  cases=loader.load(ROOT/'evals/sets/l09_labels.draft.jsonl');self.assertEqual(len(cases),30);self.assertEqual(sum(c['additional_metadata']['disputed'] for c in cases),10);self.assertTrue(all('label' not in c['additional_metadata'] for c in cases));cal.validate(cases,allow_draft=True)
  with self.assertRaises(ValueError):cal.validate(cases)
 def test_working_gates_and_rubric(self):
  cases=loader.load(ROOT/'sets/l09_escalation.jsonl');judges=[c for c in cases if c['additional_metadata']['assertion']=='judge'];self.assertEqual(len(judges),5)
  for c in judges:self.assertEqual((c['additional_metadata']['gate'],c['additional_metadata']['runs']),('release',5));self.assertNotIn('answer_under_test',c)
  self.assertEqual(cases[0]['additional_metadata']['gate'],'daily');self.assertEqual(cases[1]['additional_metadata']['runs'],5)
class PaidSafety(unittest.TestCase):
 def test_no_network_without_explicit_paid_flag(self):
  with patch.dict(os.environ,{},clear=True),patch.object(judge._opener,'open',side_effect=AssertionError('Network forbidden')):
   with self.assertRaises(RuntimeError):judge.judge('q','a','r','fixture',.7)
   with self.assertRaises(RuntimeError):stand.chat('q')
 def test_paid_flag_is_not_human_approval(self):
  with tempfile.TemporaryDirectory() as tmp,patch('hw8_guard.ROOT',Path(tmp)),patch.dict(os.environ,{'HW8_PAID':'1'}):
   with self.assertRaises(RuntimeError):require_paid()
 def test_quote_and_single_answer_turn(self):
  base={'verdict':'PASS','trigger':'T1','evidence_turn':1,'quote':'human'};self.assertEqual(judge._parse(json.dumps(base),'A human agent.'),base)
  with self.assertRaises(ValueError):judge._parse(json.dumps(dict(base,quote='invented')),'A human agent.')
  with self.assertRaises(ValueError):judge._parse(json.dumps(dict(base,evidence_turn=2)),'A human agent.')
 def test_bad_provider_output_is_saved_and_never_retried(self):
  class Response:
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self):return json.dumps({'id':'fixture-response','model':'fixture','usage':{'input_tokens':42},'content':[{'type':'text','text':'not JSON'}]}).encode()
  with tempfile.TemporaryDirectory() as tmp,patch.object(judge,'ROOT',Path(tmp)),patch.object(judge,'require_paid'),patch.dict(os.environ,{'ANTHROPIC_API_KEY':'fixture-not-a-key'}),patch.object(judge._opener,'open',return_value=Response()) as opened:
   with self.assertRaises(ValueError):judge.judge('q','answer','rubric','fixture',.7)
   self.assertEqual(opened.call_count,1);record=json.loads(next(Path(tmp).glob('evidence/judge-calls/*/call.json')).read_text(encoding='utf-8'));self.assertEqual(record['usage']['input_tokens'],42);self.assertEqual(record['output_text'],'not JSON');self.assertEqual(record['effective_temperature'],.7);self.assertIsNotNone(record['error'])

class WindowsConfiguration(unittest.TestCase):
 def test_system_temp_is_not_a_sampling_parameter(self):
  import tempfile
  from unittest.mock import patch
  with patch.dict(os.environ,{'TEMP':'C:\\system-temp','HW8_JUDGE_TEMPERATURE':'0.7'}):
   class Response:
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self):return json.dumps({'id':'fixture','model':'fixture','usage':{},'content':[{'type':'text','text':json.dumps({'verdict':'PASS','trigger':'T1','evidence_turn':1,'quote':'human'})}]}).encode()
   with tempfile.TemporaryDirectory() as tmp,patch.object(judge,'ROOT',Path(tmp)),patch.object(judge,'require_paid'),patch.dict(os.environ,{'ANTHROPIC_API_KEY':'fixture-not-a-key'}),patch.object(judge._opener,'open',return_value=Response()) as opened:
    r=judge.judge('q','human answer','rubric','fixture');self.assertEqual(r['temperature'],.7);request=opened.call_args.args[0];self.assertEqual(json.loads(request.data)['temperature'],.7);self.assertEqual(os.environ['TEMP'],'C:\\system-temp')
