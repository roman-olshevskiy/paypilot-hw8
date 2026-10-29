"""Replay native working CLI from full saved response/trace fixtures; no HTTP/inference."""
import sys,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def worker(profile,out):
 sys.path.insert(0,str(ROOT));import stand,runner,cli,judge
 index=json.loads((ROOT/'evidence/working-index.json').read_text(encoding='utf-8'));entry=next(x for x in index['series'] if x['profile']==profile);folder=ROOT/entry['folder'];rows=json.loads((folder/'agent-captures.json').read_text(encoding='utf-8'));expected=json.loads((folder/'native-results.json').read_text(encoding='utf-8'));bycase={};traces={}
 for r in rows:bycase.setdefault(r['case_id'],[]).append(r);traces[r['response']['request_id']]=r['trace']
 calls=[]
 for p in (ROOT/'evidence/judge-calls').glob('*/call.json'):
  r=json.loads(p.read_text(encoding='utf-8'));c=r.get('capture_context',{})
  if c.get('HW8_PHASE')=='working' and c.get('HW8_PROFILE')==profile:calls.append(r)
 state={'case':None,'repeat':0,'chat_calls':0,'judge_calls':0};original_case=runner.run_case
 def case(c):state.update(case=c['id'],repeat=0);return original_case(c)
 def fake(method,path,payload=None,**kwargs):
  if path=='/health':return {'status':'ok','provider':'recorded-replay'}
  if path=='/api/_test/defects':return {'profile':profile,'extra_defects':[]}
  if path=='/api/_test/prompt':return {'version':expected['prompt_version']}
  if path=='/api/_test/profile':return {'profile':profile}
  if path=='/api/_test/reset':state['repeat']+=1;return {}
  if path=='/api/_test/clock':return {'now':payload['now']}
  if path=='/chat':
   r=bycase[state['case']][state['repeat']-1];assert payload['message']==r['request']['message'];assert payload['customer_id']==r['request']['customer_id'];state['chat_calls']+=1;return r['response']
  if path.startswith('/api/_test/traces/'):return traces[path.rsplit('/',1)[1]]
  raise RuntimeError('HTTP forbidden in replay: '+method+' '+path)
 def fakejudge(question,answer,rubric,model=None,temperature=None):
  matching=[r for r in calls if r['capture_context']['HW8_CASE_ID']==state['case']];assert len(matching)==1
  r=matching[0];body=r['request_body']['messages'][0]['content'];assert 'CUSTOMER QUESTION:\n'+question+'\n' in body;assert 'AGENT ANSWER:\n'+answer+'\n' in body;state['judge_calls']+=1;return r['parsed']
 stand._call=fake;runner.run_case=case;judge.judge=fakejudge;runner.JUDGE_MODEL=expected['judge_model'];runner.RUBRIC_VERSION=expected['rubric_version'];runner.REPORTS_DIR=Path(out);runner.RUN_STAMP='recorded-replay-'+profile
 code=cli.main(['--set','l09_escalation','--gate','all','--profile',profile])
 actual=json.loads(next(Path(out).glob('*.json')).read_text(encoding='utf-8'))
 assert [(c['id'],c['verdict']['passed'],c['skipped']) for c in actual['cases']]==[(c['id'],c['verdict']['passed'],c['skipped']) for c in expected['cases']]
 assert code==(0 if expected['passed']==expected['total'] else 1)
 print(json.dumps({'profile':profile,'native_exit':code,'verdicts_reproduced':len(actual['cases']),'fixture_chats':state['chat_calls'],'fixture_judgements':state['judge_calls'],'real_http_calls':0,'real_model_calls':0}))

def main():
 if len(sys.argv)>1 and sys.argv[1]=='--worker':worker(sys.argv[2],sys.argv[3]);return
 with tempfile.TemporaryDirectory(prefix='hw8-clean-clone-') as tmp:
  clone=Path(tmp)/'repo';subprocess.run(['git','clone','--quiet','--no-hardlinks',str(ROOT),str(clone)],check=True);assert not subprocess.check_output(['git','status','--porcelain'],cwd=clone)
  outputs=[]
  for profile in ['clean','lesson-09']:
   r=subprocess.run([sys.executable,str(clone/'tools/replay_saved.py'),'--worker',profile,str(Path(tmp)/profile)],cwd=clone,capture_output=True,text=True,encoding='utf-8')
   if r.returncode:print(r.stdout[-2000:]);print(r.stderr);raise RuntimeError('Native replay failed')
   outputs.append(json.loads(r.stdout.splitlines()[-1]))
  assert not subprocess.check_output(['git','status','--porcelain'],cwd=clone)
  proof={'clone_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=clone,text=True).strip(),'clean_before_and_after':True,'scope':'Clean Git clone, actual native CLI on recorded full response/trace/judge fixtures. Not a new live run.','results':outputs}
  (ROOT/'evidence/clean-clone-replay.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
