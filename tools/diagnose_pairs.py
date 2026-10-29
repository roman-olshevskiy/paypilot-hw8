"""Five RAW emissions per supplied diagnostic case, reusing existing captures.
A wrong quote is retained as protocol failure; verdict-only views never imply valid evidence.
Primary calibration still requires five valid structured verdicts.
"""
import json,sys,os,datetime,uuid
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
import judge,loader
from hw8_common import load_env,save,digest
from hw8_guard import require_paid

def matches(c):
 prompt=f"CUSTOMER QUESTION:\n{c['input']}\n\nAGENT ANSWER:\n{c['answer_under_test']}\n\nRUBRIC:\n{c['additional_metadata']['rubric']}\n\nJSON:"
 found=[]
 for p in sorted((ROOT/'evidence/judge-calls').glob('*/call.json')):
  r=json.loads(p.read_text(encoding='utf-8'));body=r.get('request_body',{})
  if body.get('messages',[{}])[0].get('content')==prompt and body.get('model')==os.environ['JUDGE_MODEL'] and body.get('temperature')==.7:found.append((p,r))
 return found

def view(p,r):
 text=r.get('output_text','');start=text.find('{');value=None
 if start>=0:
  try:
   d,end=json.JSONDecoder().raw_decode(text[start:]);tail=text[start+end:]
   if '{' not in tail and d.get('verdict') in ['PASS','FAIL']:value=d['verdict']
  except (ValueError,TypeError):pass
 return {'capture':p.relative_to(ROOT).as_posix(),'raw_verdict':value,'protocol_valid':r.get('error') is None,'protocol_error':r.get('error'),'output_text':text}

def main():
 load_env();require_paid();path=ROOT/'sets/l09_step5_pairs.jsonl';original=ROOT/'sources/l09-original/l09_step5_pairs.jsonl';assert digest(path)==digest(original);cases=loader.load(path)
 out=ROOT/'reports'/('diagnostic-pairs-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json');report={'scope':'First five raw provider emissions per supplied pair; reuses stopped calibrate_run captures. Verbatim quote failures remain failures. Not the 30-case calibration and not five valid structured outputs.','judge_model':os.environ['JUDGE_MODEL'],'temperature':.7,'cases':[],'source_sha256':digest(path)};save(out,report)
 for c in cases:
  prior=matches(c)
  if len(prior)>5:raise RuntimeError('More than five raw emissions exist; do not select a convenient subset')
  while len(prior)<5:
   try:judge.judge(c['input'],c['answer_under_test'],c['additional_metadata']['rubric'],os.environ['JUDGE_MODEL'],.7)
   except ValueError:pass # A schema error is one measured raw emission, not a hidden retry.
   next_rows=matches(c)
   if len(next_rows)!=len(prior)+1:raise RuntimeError('Expected exactly one durable provider capture')
   prior=next_rows
   report['in_progress']={'id':c['id'],'raw_attempts':len(prior)};save(out,report)
  outputs=[view(p,r) for p,r in prior];vs=[r['raw_verdict'] for r in outputs];major=Counter(vs).most_common(1)[0][0] if all(v in ['PASS','FAIL'] for v in vs) else None
  report['cases'].append({'id':c['id'],'source_label':c['additional_metadata']['label'],'raw_attempts':5,'verdicts':vs,'majority_verdict_only':major,'agrees_verdict_only':major==c['additional_metadata']['label'],'valid_protocol_emissions':sum(r['protocol_valid'] for r in outputs),'outputs':outputs});report.pop('in_progress',None);save(out,report)
 report['status']='all_raw_attempts_collected';report['total_raw_attempts']=sum(c['raw_attempts'] for c in report['cases']);report['protocol_failures']=sum(5-c['valid_protocol_emissions'] for c in report['cases']);save(out,report);save(ROOT/'evidence/diagnostic-index.json',{'file':out.relative_to(ROOT).as_posix()});print(json.dumps({k:report[k] for k in ['total_raw_attempts','protocol_failures','status']},indent=2))
if __name__=='__main__':main()
