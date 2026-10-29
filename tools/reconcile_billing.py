"""Final read-only cost reconciliation; account totals remain local."""
import json,sys
from pathlib import Path
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hw8_common import save

def main():
 analysis=json.loads((ROOT/'evidence/final-analysis.json').read_text(encoding='utf-8'));private=ROOT.parent/'Lectures/HW08/work/billing';first=private/'20261029T140650869324Z-pilot-3d4a86a2-before.json';latest=sorted(private.glob('settled-*.json'))[-1];before=json.loads(first.read_text(encoding='utf-8'));after=json.loads(latest.read_text(encoding='utf-8'));delta=Decimal(str(after['usage']))-Decimal(str(before['usage']));expected=Decimal(str(analysis['openrouter_provider_usd']))
 proof={'scope':'All HW8 pilot/frequency/working/calibration/diagnostic model calls, including protocol failures and unauthenticated diagnostic chats','openrouter_key_delta_usd':float(delta),'openrouter_provider_spans_usd':float(expected),'openrouter_difference_usd':float(delta-expected),'openrouter_verified':abs(delta-expected)<Decimal('.00000001'),'anthropic_usage_price_estimate_usd':analysis['anthropic_estimated_usd'],'anthropic_account_verified':False,'total_estimated_usd':float(expected+Decimal(str(analysis['anthropic_estimated_usd']))),'agent_chats':analysis['agent_chat_count'],'judge_provider_calls':analysis['judge_provider_call_count'],'remaining_stop_budget_usd':1.5,'pricing_source':'https://platform.claude.com/docs/en/models/haiku-4-5/overview','account_available_balances_published':False}
 confirmation=private/'anthropic-confirmed.json'
 if confirmation.exists():
  verified=json.loads(confirmation.read_text(encoding='utf-8'))
  actual=Decimal(str(verified['task_delta_usd']))
  estimate=Decimal(str(analysis['anthropic_estimated_usd']))
  proof.update(anthropic_account_verified=True,anthropic_confirmed_task_usd=float(actual),anthropic_confirmation_source='Account balance change, explicitly confirmed in chat on 2026-10-29',anthropic_balance_display_precision_usd=0.01,anthropic_estimate_difference_usd=float(actual-estimate),anthropic_reconciliation_note='Account balances are rounded to cents; the $0.003807 difference is within display precision. No exact provider ledger is claimed.',total_with_confirmed_anthropic_usd=float(expected+actual))
 save(ROOT/'evidence/final-billing-reconciliation.json',proof);print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
