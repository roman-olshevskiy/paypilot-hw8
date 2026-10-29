"""Offline pilot accounting. Private account snapshots are read locally, not copied to Git."""
from pathlib import Path
from decimal import Decimal
import json,statistics,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from hw8_common import save,digest
import stand

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def money(x):return Decimal(str(x or 0))
def anthropic_cost(u):
 detail=u.get('cache_creation',{});five=detail.get('ephemeral_5m_input_tokens',u.get('cache_creation_input_tokens',0));hour=detail.get('ephemeral_1h_input_tokens',0)
 return (money(u.get('input_tokens'))+money(u.get('output_tokens'))*5+money(u.get('cache_read_input_tokens'))*Decimal('.1')+money(five)*Decimal('1.25')+money(hour)*2)/1000000

def main():
 indices=[read(ROOT/'evidence/pilot-unauthenticated-index.json'),read(ROOT/'evidence/pilot-index.json')];agent=[];judges=[];stages=[];total_key=Decimal(0)
 for index in indices:
  folder=ROOT/index['folder'].replace('\\','/');m=read(folder/'manifest.json');assert m['error'] is None
  for n,h in m['sha256'].items():assert digest(folder/n)==h
  a=read(folder/'agent-captures.json');j=read(folder/'judge-results.json') if (folder/'judge-results.json').exists() else [];agent+=a;judges+=j
  private=ROOT.parent/'Lectures/HW08/work/billing';key_delta=money(read(private/(folder.name+'-after.json'))['usage'])-money(read(private/(folder.name+'-before.json'))['usage']);total_key+=key_delta
  stages.append({'folder':str(folder.relative_to(ROOT)).replace('\\','/'),'authenticated_agent':bool(m.get('agent_only')),'chat_responses':len(a),'judge_responses':len(j),'key_usage_delta_usd':float(key_delta)})
 agent_cost=[]
 for row in agent:
  spans=[s for s in stand.spans(row['trace']) if s['name'] in ['llm.call','agent.summarize']]
  if any(s['attributes'].get('provider.cost_usd') is None for s in spans):raise ValueError('Missing provider costs')
  agent_cost.append(sum((money(s['attributes']['provider.cost_usd']) for s in spans),Decimal(0)))
 judge_cost=[anthropic_cost(row['result']['usage']) for row in judges]
 authenticated=agent[-4:];auth_cost=agent_cost[-4:];assert len(judges)==3 and len(agent)==8
 auth_results=[{'case':r['case_id'],'profile':r['profile'],'escalation':r['escalate_to_human'],'tools':[s['name'] for s in stand.spans(r['trace']) if s['name'].startswith('tool.')],'provider_usd':float(cost)} for r,cost in zip(authenticated,auth_cost)]
 private=ROOT.parent/'Lectures/HW08/work/billing';settled=sorted(private.glob('settled-*.json'))
 if settled:
  first=ROOT/indices[0]['folder'].replace('\\','/');total_key=money(read(settled[-1])['usage'])-money(read(private/(first.name+'-before.json'))['usage'])
 result={'scope':'All pilot stages including four unauthenticated diagnostic chats; one pre-inference TEMP failure had zero model calls. Pilot repeats never count as final calibration.','chat_responses':len(agent),'judge_responses':len(judges),'openrouter_provider_sum_usd':float(sum(agent_cost)),'openrouter_key_delta_usd':float(total_key),'openrouter_key_minus_spans_usd':float(total_key-sum(agent_cost)),'anthropic_price_estimate_usd':float(sum(judge_cost)),'anthropic_account_billing_verified':False,'openrouter_billing_status':'matched' if abs(total_key-sum(agent_cost))<Decimal('.00000001') else 'pending_counter_update','total_pilot_estimated_usd':float(sum(agent_cost)+sum(judge_cost)),'judge_model':'claude-haiku-4-5-20251001','temperature_requested_and_accepted':.7,'judge_agreements_pilot_only':sum(x['label']==x['result']['verdict'] for x in judges),'judge_calls':[{'case':r['case_id'],'verdict':r['result']['verdict'],'price_usd':float(cost)} for r,cost in zip(judges,judge_cost)],'authenticated_agent_results':auth_results,'stages':stages,'rates_source':'https://platform.claude.com/docs/en/models/haiku-4-5/overview','rough_remaining_estimate_usd':{'anthropic_330_calls_at_pilot_mean':float(statistics.mean(judge_cost)*330),'openrouter_102_chats_at_authenticated_pilot_mean':float(statistics.mean(auth_cost)*102)},'proposed_remaining_stop_budgets_usd':{'anthropic':1.0,'openrouter':.5,'combined':1.5},'budget_status':'Proposed after pilot; full matrix not started. Estimates from small sample, not spending guarantees.'}
 save(ROOT/'evidence/pilot-accounting.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
