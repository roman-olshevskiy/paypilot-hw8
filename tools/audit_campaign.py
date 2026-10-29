"""Offline audit for frozen labels, saved generations, and native series."""
import json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hw8_common import digest,save

def audit():
 reports=[]
 for path in sorted((ROOT/'reports').glob('calibration-*.json')):
  r=json.loads(path.read_text(encoding='utf-8'))
  reports.append({'file':path.relative_to(ROOT).as_posix(),'status':r['status'],'completed':len(r['cases']),'planned':r['planned_cases'],'agreement':r.get('agreement'),'self_consistency':r.get('self_consistency'),'confusion':r.get('confusion_matrix'),'disagreements':[{'id':c['id'],'label':c['label'],'majority':c['majority'],'verdicts':c['verdicts']} for c in r['cases'] if c['complete'] and not c['agree']]})
 return reports
if __name__=='__main__':print(json.dumps(audit(),ensure_ascii=False,indent=2))
