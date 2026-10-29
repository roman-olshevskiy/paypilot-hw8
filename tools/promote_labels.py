"""Explicit human-review promotion; no model/API calls and no automatic commit."""
import argparse,json,sys,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from hw8_common import save
import loader

def promote(review_path):
 draft=loader.load(ROOT/'evals/sets/l09_labels.draft.jsonl');review=json.loads(Path(review_path).read_text(encoding='utf-8'))
 if review.get('human_review_confirmed') is not True:raise ValueError('Explicit human review confirmation required')
 labels=review.get('labels',{});ids={c['id'] for c in draft}
 if set(labels)!=ids:raise ValueError('Supply exactly all 30 IDs, no implicit acceptance')
 obvious=[c for c in draft if not c['additional_metadata']['disputed']]
 if min(sum(labels[c['id']]==v for c in obvious) for v in ['PASS','FAIL'])<10:raise ValueError('Need >=10 obvious PASS and >=10 obvious FAIL; adjust/review the draft set before any inference')
 now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 for c in draft:
  m=c['additional_metadata'];value=labels[c['id']]
  if value not in ['PASS','FAIL']:raise ValueError('Only PASS/FAIL are labels')
  m['label']=value;m['label_status']='human_review_confirmed';m['human_review_confirmed']=True;m['labeled_on']=now;m.pop('proposed_label',None);m.pop('proposal_reason',None)
  if m['disputed']:m['why_disputed']=review.get('reasons',{}).get(c['id'],m['why_disputed'])
 path=ROOT/'evals/sets/l09_labels.jsonl'
 if path.exists():raise ValueError('Final labels already exist; never overwrite historical labels')
 path.write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in draft),encoding='utf-8');save(ROOT/'evidence/human-review.json',{'confirmed':True,'confirmed_at_utc':now,'review_path':str(Path(review_path).name),'case_count':len(draft),'source':'Explicit human review of proposed labels; not independent second annotation'})
 return path
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('review_json');a=p.parse_args();print(promote(a.review_json))
