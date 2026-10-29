"""Offline analysis of the completed, separately identified cohorts."""
import json,sys,statistics,hashlib
from pathlib import Path
from collections import Counter
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from hw8_common import save,digest
from hw8_budget import spent
import stand

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def main():
 idx=read('evidence/calibration-index.json');v1=read(idx['baseline_v1']);v2=read(idx['v2']);assert v1['status']==v2['status']=='complete';assert len(v1['cases'])==len(v2['cases'])==30
 assert v1['set_sha256']==v2['set_sha256']==digest(ROOT/'evals/sets/l09_labels.jsonl')
 old={c['id']:c for c in v1['cases']};new={c['id']:c for c in v2['cases']};changed={'improved':[i for i in old if not old[i]['agree'] and new[i]['agree']],'regressed':[i for i in old if old[i]['agree'] and not new[i]['agree']]}
 labels={c['id']:c for c in [json.loads(x) for x in (ROOT/'evals/sets/l09_labels.jsonl').read_text(encoding='utf-8').splitlines()]}
 disagreements=[]
 for ident in sorted(old):
  if not old[ident]['agree'] or not new[ident]['agree']:
   c=labels[ident];disagreements.append({'id':ident,'label':old[ident]['label'],'v1':old[ident]['majority'],'v2':new[ident]['majority'],'v1_votes':old[ident]['verdicts'],'v2_votes':new[ident]['verdicts'],'answer':c['answer_under_test'],'lines':len(c['answer_under_test'].splitlines()),'digits':any(x.isdigit() for x in c['answer_under_test']),'language':'uk' if any('\u0400'<=x<='\u04ff' for x in c['answer_under_test']) else 'en'})
 # Cost is counted once per raw transport capture, including rejected schemas.
 judge_rows=[]
 for p in sorted((ROOT/'evidence/judge-calls').glob('*/call.json')):
  r=json.loads(p.read_text(encoding='utf-8'));u=r.get('usage')
  if u is None:continue
  detail=u.get('cache_creation',{});five=detail.get('ephemeral_5m_input_tokens',u.get('cache_creation_input_tokens',0));hour=detail.get('ephemeral_1h_input_tokens',0)
  cost=(Decimal(str(u.get('input_tokens',0)))+5*Decimal(str(u.get('output_tokens',0)))+Decimal('.1')*Decimal(str(u.get('cache_read_input_tokens',0)))+Decimal('1.25')*Decimal(str(five))+2*Decimal(str(hour)))/1000000
  judge_rows.append({'capture':p.parent.relative_to(ROOT).as_posix(),'estimated_usd':float(cost),'input_tokens':u.get('input_tokens',0),'output_tokens':u.get('output_tokens',0),'protocol_error':r.get('error'),'duration_ms':r['duration_ms']})
 by_capture={r['capture']:r for r in judge_rows};cohort_costs={}
 for name,r in [('v1',v1),('v2',v2)]:
  calls=[by_capture[o['capture'].replace('\\','/')] for c in r['cases'] for o in c['outputs']];cohort_costs[name]={'valid_150_calls_estimated_usd':sum(x['estimated_usd'] for x in calls),'mean_input_tokens':statistics.mean(x['input_tokens'] for x in calls),'median_duration_ms':statistics.median(x['duration_ms'] for x in calls)}
 agent=[];ids=set()
 for p in sorted((ROOT/'evidence/runs').glob('*/agent-captures.json')):
  manifest=json.loads((p.parent/'manifest.json').read_text(encoding='utf-8'))
  for n,h in manifest['sha256'].items():assert digest(p.parent/n)==h
  for r in json.loads(p.read_text(encoding='utf-8')):
   ident=r['response']['request_id'];assert ident not in ids;ids.add(ident);assert r['trace'] is not None;agent.append({'request_id':ident,'folder':p.parent.relative_to(ROOT).as_posix(),'case':r['case_id'],'profile':r['profile']})
 working=[]
 if (ROOT/'evidence/working-index.json').exists():
  for s in read('evidence/working-index.json')['series']:
   r=read(s['folder']+'/native-results.json');working.append({'profile':r['profile'],'passed':r['passed'],'total':r['total'],'skipped':r['skipped'],'native_exit':s['native_exit'],'report_folder':s['folder'],'judge_model':r['judge_model'],'rubric_version':r['rubric_version'],'cases':[{'id':c['id'],'passed':c['verdict']['passed'],'runs':c['runs']} for c in r['cases']]})
 result={'calibration_index':idx,'v1':v1['groups'],'v2':v2['groups'],'v1_confusion':v1['confusion_matrix'],'v2_confusion':v2['confusion_matrix'],'v1_protocol_errors':v1.get('protocol_errors',0),'v2_protocol_errors':v2.get('protocol_errors',0),'v1_end_to_end_consistency':v1.get('end_to_end_self_consistency'),'v2_end_to_end_consistency':v2.get('end_to_end_self_consistency'),'changed':changed,'disagreements':disagreements,'cohort_costs':cohort_costs,'frequency':read('evidence/escalation-frequency.json'),'working':working,'agent_chat_count':len(agent),'judge_provider_call_count':len(judge_rows),'judge_protocol_error_count':sum(bool(x['protocol_error']) for x in judge_rows),'anthropic_estimated_usd':sum(x['estimated_usd'] for x in judge_rows),'openrouter_provider_usd':float(spent('openrouter')),'raw_judge_calls':judge_rows,'agent_requests':agent}
 save(ROOT/'evidence/final-analysis.json',result);print(json.dumps({k:result[k] for k in ['changed','agent_chat_count','judge_provider_call_count','anthropic_estimated_usd','openrouter_provider_usd']},indent=2))
if __name__=='__main__':main()
