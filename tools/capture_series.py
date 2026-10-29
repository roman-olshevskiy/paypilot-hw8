"""Native L09 CLI with full durable captures; one profile per capture folder."""
import sys,os,json,datetime,uuid,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from hw8_common import load_env,save,digest
from hw8_guard import require_paid

def run_series(label,profiles,cli_args,rubric_version='rubric.v1'):
 load_env();require_paid();import stand,runner,cli,judge
 runner.JUDGE_MODEL=os.environ['JUDGE_MODEL'];runner.RUBRIC_VERSION=rubric_version;judge.RUBRIC_VERSION=rubric_version
 summaries=[]
 for profile in profiles:
  stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'evidence/runs'/f'{stamp}-{label}-{profile}-{uuid.uuid4().hex[:6]}';folder.mkdir(parents=True)
  before=stand.profile();rows=[];attempts=[];context={'case':None,'run':0};error=None;code=None
  manifest={'label':label,'profile':profile,'before':before,'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_cli_args':cli_args,'error':None,'agent_responses':0}
  save(folder/'manifest.json',manifest);original_call=stand._call;original_case=runner.run_case
  def call(method,path,payload=None,**kwargs):
   if path!='/chat':return original_call(method,path,payload,**kwargs)
   context['run']+=1;attempt={'case_id':context['case'],'run':context['run'],'request':payload,'response':None,'error':None};attempts.append(attempt);save(folder/'attempts.json',attempts)
   try:response=original_call(method,path,payload,**kwargs)
   except Exception as e:attempt['error']=str(e);save(folder/'attempts.json',attempts);raise RuntimeError('Chat transport failed; no automatic retry: '+str(e)) from e
   attempt['response']=response;save(folder/'attempts.json',attempts)
   row={'case_id':context['case'],'run':context['run'],'profile':profile,'request':payload,'response':response,'trace':None,'disputes':None};rows.append(row);save(folder/'agent-captures.json',rows)
   row['trace']=original_call('GET','/api/_test/traces/'+response['request_id']);row['disputes']=stand.state('disputes');row['escalate_to_human']=stand.has_span(row['trace'],'tool.escalate_to_human');save(folder/'agent-captures.json',rows)
   if response.get('usage',{}).get('model')!='anthropic/claude-haiku-5.5':raise RuntimeError('Unexpected actual agent model; stop before mixing conditions')
   return response
  def case(c):
   context.update(case=c['id'],run=0);return original_case(c)
  stand._call=call;runner.run_case=case
  # Upstream shares its stamp across CLI calls; isolate profile trace folders.
  runner.RUN_STAMP=stamp+'-'+label+'-'+profile
  os.environ.pop('CASE',None);os.environ.pop('REPEAT',None)
  try:
   stand.set_defects('');code=cli.main(['--set','l09_escalation','--gate','all','--profile',profile,'--traces',*cli_args])
   if code not in [0,1]:raise RuntimeError('Native CLI infrastructure exit '+str(code))
   native=ROOT/'reports'/f'l09_escalation-{profile}-{runner.RUN_STAMP}.json';shutil.copyfile(native,folder/'native-results.json')
  except Exception as e:error=f'{type(e).__name__}: {e}';raise
  finally:
   stand._call=original_call;runner.run_case=original_case
   try:stand.set_profile(before['profile']);stand.set_defects(','.join(before.get('extra_defects',[])));manifest['restored']=stand.profile()
   except Exception as e:manifest['restore_error']=str(e)
   manifest.update(error=error,native_exit=code,agent_responses=len(rows),finished_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sha256={p.name:digest(p) for p in folder.glob('*.json') if p.name!='manifest.json'});save(folder/'manifest.json',manifest)
   summary={'profile':profile,'folder':folder.relative_to(ROOT).as_posix(),'native_exit':code,'agent_responses':len(rows),'error':error};summaries.append(summary);save(ROOT/f'evidence/{label}-index.json',{'series':summaries});print('SERIES CAPTURE',summary,flush=True)
 return summaries
