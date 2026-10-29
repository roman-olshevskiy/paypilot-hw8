import unittest,subprocess,sys,re,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Preparation(unittest.TestCase):
 def test_authored_links_and_no_final_claim(self):
  from urllib.parse import unquote
  for p in [ROOT/'README.md',ROOT/'SUBMISSION.md',*list((ROOT/'docs').glob('*.md'))]:
   for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
    if '://' not in target:self.assertTrue((p.parent/unquote(target.split('#')[0])).exists(),f'{p.name}: {target}')
  if not (ROOT/'evidence/human-review.json').exists():
   self.assertFalse((ROOT/'evals/sets/l09_labels.jsonl').exists());self.assertFalse((ROOT/'evidence/labels-freeze.json').exists());self.assertFalse(list((ROOT/'reports').glob('calibration-*.json')))
 def test_upstream_calibration_files_preserved(self):
  p=json.loads((ROOT/'evidence/provenance.json').read_text(encoding='utf-8'))
  self.assertEqual(p['l09_commit'],'6439a320c286e72c6643f4d4e8bbbd04895b752b')
  for name in ['judge.py','runner.py','stand.py','loader.py','docker-compose.yml','tools/calibrate_run.py','tools/compare_judges.py']:
   original=ROOT/'sources/l09-original'/name;self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(),p['source_files_sha256'][name])
  self.assertEqual((ROOT/'runner.py').read_bytes(),(ROOT/'sources/l09-original/runner.py').read_bytes())
