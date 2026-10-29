"""Pre-call stop budgets from durable usage; independent provider ledgers.
Reserves are conservative campaign checks, not provider-enforced spending limits.
"""
import json
from pathlib import Path
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1]
D=lambda x:Decimal(str(x or 0))
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def spent(kind):
 if kind=='anthropic':
  total=Decimal(0)
  for p in (ROOT/'evidence/judge-calls').glob('*/call.json'):
   r=read(p);u=r.get('usage')
   if u is None:
    if r.get('response_body') is None and not r.get('error'):total+=Decimal('.01')
    elif r.get('http_status') not in [400,401,403,404,429] and r.get('error'):raise RuntimeError('Unpriced judge error; inspect before further paid calls')
    continue
   c=u.get('cache_creation',{});five=c.get('ephemeral_5m_input_tokens',u.get('cache_creation_input_tokens',0));hour=c.get('ephemeral_1h_input_tokens',0)
   total+=(D(u.get('input_tokens'))+5*D(u.get('output_tokens'))+D('.1')*D(u.get('cache_read_input_tokens'))+D('1.25')*D(five)+2*D(hour))/1000000
  return total
 total=Decimal(0);seen=set()
 def spans(t):
  yield t
  for child in t.get('children',[]):yield from spans(child)
 for p in (ROOT/'evidence/runs').glob('*/agent-captures.json'):
  for r in read(p):
   response=r.get('response',{});ident=response.get('request_id')
   if not ident or ident in seen:continue
   seen.add(ident)
   if r.get('trace') is None:total+=D('.05');continue
   for s in spans(r['trace']):
    if s.get('name') in ['llm.call','agent.summarize']:
     cost=s.get('attributes',{}).get('provider.cost_usd')
     if cost is None:raise RuntimeError('Missing provider cost; stop budget cannot be checked')
     total+=D(cost)
 return total

def check(kind):
 path=ROOT/'evidence/campaign-budget.json'
 if not path.exists():return
 b=read(path);cap=D(b['pilot_baseline_usd'][kind])+D(b['remaining_limits_usd'][kind]);reserve=D('.01' if kind=='anthropic' else '.05')
 if spent(kind)+reserve>cap:raise RuntimeError(f'{kind} pre-call stop budget reached; no further inference')
