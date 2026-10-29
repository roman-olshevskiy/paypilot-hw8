"""Explicit live native-CLI series, no manual chat calls."""
import unittest,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
@unittest.skipUnless(os.environ.get('HW8_SERIES') in ['frequency','working'],'Explicit live series disabled')
class NativeSeries(unittest.TestCase):
 def test_native_profiles(self):
  from capture_series import run_series
  label=os.environ['HW8_SERIES'];args=['--only','ESC-001,ESC-002','--repeat','10'] if label=='frequency' else []
  results=run_series(label,['clean','lesson-09'],args,os.environ.get('RUBRIC_VERSION','rubric.v1'));self.assertEqual(len(results),2);self.assertTrue(all(x['error'] is None for x in results))
