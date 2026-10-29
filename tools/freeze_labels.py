"""After explicit review and a local commit, register immutable input hashes."""
import sys,json,subprocess,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from hw8_common import digest,save
import loader

def main():
 path=ROOT/'evals/sets/l09_labels.jsonl';cases=loader.load(path)
 if len(cases)<30 or sum(bool(c['additional_metadata'].get('disputed')) for c in cases)<10:raise ValueError('Need >=30 cases / >=10 disputed')
 for c in cases:
  m=c['additional_metadata']
  if m.get('human_review_confirmed') is not True or m.get('label') not in ['PASS','FAIL']:raise ValueError('Review incomplete')
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();f={'commit':commit,'human_review_confirmed':True,'registered_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 for key,name in {'labels':'evals/sets/l09_labels.jsonl','rubric':'rubrics/rubric.v1.md','forecast':'docs/forecast-before-runs.md'}.items():
  if subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT)!=(ROOT/name).read_bytes():raise ValueError('Commit reviewed inputs before freeze: '+name)
  f[key+'_path']=name;f[key+'_sha256']=digest(ROOT/name)
 if (ROOT/'evidence/labels-freeze.json').exists():raise ValueError('Freeze already exists; do not overwrite')
 save(ROOT/'evidence/labels-freeze.json',f);print('Reviewed inputs committed and frozen; paid calls still require explicit flag.')
if __name__=='__main__':main()
