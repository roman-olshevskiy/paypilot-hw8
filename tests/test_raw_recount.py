import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from recount_raw import score

class RawRecount(unittest.TestCase):
 def test_invalid_fail_cannot_agree_with_fail_label(self):
  r=score('FAIL',[{'verdict':'MISS'}]*3+[{'verdict':'FAIL'}]*2)
  self.assertFalse(r['agree']);self.assertEqual(r['majority'],'MISS');self.assertEqual(r['correct_attempts'],2);self.assertFalse(r['stable'])
 def test_five_invalid_outputs_are_not_consistency(self):
  self.assertFalse(score('PASS',[{'verdict':'MISS'}]*5)['stable'])
 def test_report_contains_fixed_slots_not_replacements(self):
  r=json.loads((ROOT/'reports/calibration-raw-recount.json').read_text(encoding='utf-8'))
  for version,agree,stable,bad in [('rubric.v1',25,29,1),('rubric.v2',24,28,2)]:
   d=r['versions'][version];self.assertEqual(d['groups']['all']['agreement']['k'],agree);self.assertEqual(d['groups']['all']['self_consistency']['k'],stable);self.assertEqual(d['invalid_attempts'],bad);self.assertEqual(d['groups']['disputed']['agreement']['k'],5)
   self.assertEqual(sum(len(c['outputs']) for c in d['cases']),150)
   chosen=[o['capture'] for c in d['cases'] for o in c['outputs']];excluded=[p for c in d['cases'] for p in c['excluded_later_captures']];self.assertFalse(set(chosen)&set(excluded));self.assertEqual(len(excluded),bad)
  self.assertEqual(r['diagnostic']['agreement']['k'],1);self.assertEqual(r['diagnostic']['correct_attempts'],7);self.assertEqual(r['new_inference_calls'],0)
