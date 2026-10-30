"""Offline correction: fixed first five provider emissions; invalid evidence is MISS."""
import json,sys,hashlib,datetime
from pathlib import Path
from collections import Counter
from decimal import Decimal
import statistics
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from calibrate_run import wilson
from hw8_common import save,digest
import judge

def score(label,outputs):
 votes=[o['verdict'] for o in outputs]
 counts=Counter(v for v in votes if v in ('PASS','FAIL'))
 majority=next((v for v,n in counts.items() if n>=3),'MISS')
 return {'majority':majority,'agree':majority==label,'stable':len(votes)==5 and len(set(votes))==1 and 'MISS' not in votes,'correct_attempts':sum(v==label for v in votes),'invalid_attempts':votes.count('MISS')}

def groups(rows):
 out={}
 for name,part in [('all',rows),('obvious',[r for r in rows if not r['disputed']]),('obvious_PASS',[r for r in rows if not r['disputed'] and r['label']=='PASS']),('obvious_FAIL',[r for r in rows if not r['disputed'] and r['label']=='FAIL']),('disputed',[r for r in rows if r['disputed']])]:
  out[name]={'agreement':wilson(sum(r['agree'] for r in part),len(part)),'self_consistency':wilson(sum(r['stable'] for r in part),len(part)),'attempt_agreement':{'k':sum(r['correct_attempts'] for r in part),'n':5*len(part)}}
 return out

def main():
 labels=[json.loads(x) for x in (ROOT/'evals/sets/l09_labels.jsonl').read_text(encoding='utf-8').splitlines()]
 captures=[(p,json.loads(p.read_text(encoding='utf-8'))) for p in sorted((ROOT/'evidence/judge-calls').glob('*/call.json'))]
 result={'policy':'Within each original calibration time window (pilot excluded), first five chronological raw provider emissions per exact frozen question/answer/rubric/model/temperature. Invalid quote/JSON/schema = MISS, never dropped or replaced. Case verdict needs at least 3 valid identical votes; otherwise MISS. A MISS never matches PASS or FAIL. Wilson denominator is cases, not correlated repeats.','new_inference_calls':0,'labels_sha256':digest(ROOT/'evals/sets/l09_labels.jsonl'),'versions':{}}
 index=json.loads((ROOT/'evidence/calibration-index.json').read_text(encoding='utf-8'))
 for version in ['rubric.v1','rubric.v2']:
  key='baseline_v1' if version=='rubric.v1' else 'v2'
  historical=json.loads((ROOT/index[key]).read_text(encoding='utf-8'))
  first_report=index['baseline_v1_error_source'] if version=='rubric.v1' else index['v2_error_sources'][0]
  start=datetime.datetime.fromisoformat(json.loads((ROOT/first_report).read_text(encoding='utf-8'))['ran_at']).strftime('%Y%m%dT%H%M%S%fZ')
  end=max(Path(o['capture'].replace(chr(92),'/')).name for c in historical['cases'] for o in c['outputs'])
  rubric=(ROOT/f'rubrics/{version}.md').read_text(encoding='utf-8');rows=[]
  for c in labels:
   prompt=f"CUSTOMER QUESTION:\n{c['input']}\n\nAGENT ANSWER:\n{c['answer_under_test']}\n\nRUBRIC:\n{rubric}\n\nJSON:"
   matches=[(p,r) for p,r in captures if start<=p.parent.name<=end and r.get('request_body',{}).get('messages',[{}])[0].get('content')==prompt and r.get('model_requested')=='claude-haiku-4-5-20251001' and r.get('temperature_requested')==0.7]
   assert len(matches)>=5,(version,c['id'],len(matches))
   outputs=[]
   for p,r in matches[:5]:
    error=r.get('error');parsed=None
    try:
     parsed=judge._parse(r.get('output_text',''),c['answer_under_test'])
    except (ValueError,TypeError) as exc:error=error or str(exc)
    outputs.append({'capture':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'verdict':'MISS' if error or parsed is None else parsed['verdict'],'protocol_error':error})
   m=c['additional_metadata'];row={'id':c['id'],'label':m['label'],'disputed':m['disputed'],'outputs':outputs,'excluded_later_captures':[p.relative_to(ROOT).as_posix() for p,r in matches[5:]]};row.update(score(row['label'],outputs));rows.append(row)
  result['versions'][version]={'cohort_window_start_utc':start,'cohort_window_end_capture':end,'original_completed_report':index[key],'original_first_report':first_report,'groups':groups(rows),'cases':rows,'invalid_attempts':sum(r['invalid_attempts'] for r in rows),'total_attempts':150,'excluded_later_attempts':sum(len(r['excluded_later_captures']) for r in rows),'confusion_matrix':{'missed_defect':sum(r['label']=='FAIL' and r['majority']=='PASS' for r in rows),'false_alarm':sum(r['label']=='PASS' and r['majority']=='FAIL' for r in rows),'no_valid_majority':sum(r['majority']=='MISS' for r in rows)}}
 diag=json.loads((ROOT/'reports/diagnostic-pairs-20261029T143539150040Z.json').read_text(encoding='utf-8'));ds=[]
 for c in diag['cases']:
  outputs=[{'capture':o['capture'],'verdict':o['raw_verdict'] if o['protocol_valid'] else 'MISS','protocol_error':o['protocol_error']} for o in c['outputs']]
  row={'id':c['id'],'label':c['source_label'],'disputed':False,'outputs':outputs};row.update(score(row['label'],outputs));ds.append(row)
 result['diagnostic']={'cases':ds,'agreement':wilson(sum(r['agree'] for r in ds),len(ds)),'correct_attempts':sum(r['correct_attempts'] for r in ds),'total_attempts':20,'invalid_attempts':sum(r['invalid_attempts'] for r in ds),'D18':{'correct_attempts':sum(r['correct_attempts'] for r in ds if 'D18' in r['id']),'total_attempts':10,'case_agreement':wilson(sum(r['agree'] for r in ds if 'D18' in r['id']),2)}}
 # Prices are reused from the already reconciled campaign; no model/billing requests.
 costs={x['capture']:x for x in json.loads((ROOT/'evidence/final-analysis.json').read_text(encoding='utf-8'))['raw_judge_calls']}
 for version,cohort in result['versions'].items():
  first=[costs[o['capture'].removesuffix('/call.json')] for c in cohort['cases'] for o in c['outputs']]
  later=[costs[p.removesuffix('/call.json')] for c in cohort['cases'] for p in c['excluded_later_captures']]
  cohort['cost']={'first_150_attempts_estimated_usd':float(sum((Decimal(str(x['estimated_usd'])) for x in first),Decimal(0))),'all_paid_attempts_estimated_usd':float(sum((Decimal(str(x['estimated_usd'])) for x in first+later),Decimal(0))),'mean_input_tokens':statistics.mean(x['input_tokens'] for x in first),'median_duration_ms':statistics.median(x['duration_ms'] for x in first)}
 save(ROOT/'reports/calibration-raw-recount.json',result)
 print(json.dumps({v:{'agreement':r['groups']['all']['agreement'],'disputed':r['groups']['disputed']['agreement'],'invalid_attempts':r['invalid_attempts']} for v,r in result['versions'].items()},indent=2))
if __name__=='__main__':main()
