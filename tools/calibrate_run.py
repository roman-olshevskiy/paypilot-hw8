"""Adapted from upstream6439a32 calibrate_run: recorded answers, loader, durable rows, human freeze."""
import argparse,hashlib,json,os,sys,datetime,uuid,subprocess
from collections import Counter
from math import sqrt
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
import loader,judge as judge_module
from hw8_common import load_env,save,digest
from hw8_guard import require_paid

def wilson(k,n,z=1.96):
 if n<=0:return {'k':k,'n':n,'estimate':None,'low':None,'high':None,'half_width':None}
 if not 0<=k<=n:raise ValueError('k outside [0,n]')
 p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;h=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/d
 return {'k':k,'n':n,'estimate':p,'low':c-h,'high':c+h,'half_width':h}

def validate(cases,allow_draft=False,reference=False):
 for c in cases:
  m=c['additional_metadata']
  if m.get('assertion')!='judge' or m.get('oracle')!='human' or m.get('gate')!='release' or m.get('runs')!=5:raise ValueError(c['id']+': calibration must be human/judge/release/5')
  if not c.get('answer_under_test') or not m.get('rubric') or not m.get('criterion'):raise ValueError(c['id']+': recorded answer and self-contained rubric/criterion required')
  if not allow_draft and not reference:
   if m.get('label') not in ['PASS','FAIL'] or not m.get('labeled_on'):raise ValueError(c['id']+': confirmed label/labeled_on required')
   if m.get('label_status')!='human_review_confirmed':raise ValueError(c['id']+': labels must be reviewed')
  if not reference and m.get('disputed') and not m.get('why_disputed'):raise ValueError('Missing why_disputed')
  if not reference and not m.get('disputed') and not m.get('ground_truth_from'):raise ValueError('Missing ground_truth_from')
 return cases

def case_result(c,outputs,error=None):
 m=c['additional_metadata'];vs=[r['verdict'] for r in outputs];complete=len(vs)==5 and error is None
 major=Counter(vs).most_common(1)[0][0] if complete else None
 return {'id':c['id'],'label':m['label'],'disputed':bool(m.get('disputed')),'verdicts':vs,'outputs':outputs,'majority':major,'complete':complete,'stable':complete and len(set(vs))==1,'agree':complete and major==m['label'],'error':error,'answer_lines':len(c['answer_under_test'].splitlines()),'contains_digits':any(x.isdigit() for x in c['answer_under_test'])}

def metrics(rows):
 complete=[r for r in rows if r['complete']];groups={}
 for name,part in [('all',complete),('obvious',[r for r in complete if not r['disputed']]),('obvious_PASS',[r for r in complete if not r['disputed'] and r['label']=='PASS']),('obvious_FAIL',[r for r in complete if not r['disputed'] and r['label']=='FAIL']),('disputed',[r for r in complete if r['disputed']])]:
  groups[name]={'agreement':wilson(sum(r['agree'] for r in part),len(part)),'self_consistency':wilson(sum(r['stable'] for r in part),len(part))}
 matrix={'missed_defect':sum(r['label']=='FAIL' and r['majority']=='PASS' for r in complete),'false_alarm':sum(r['label']=='PASS' and r['majority']=='FAIL' for r in complete),'correct_PASS':sum(r['label']=='PASS' and r['majority']=='PASS' for r in complete),'correct_FAIL':sum(r['label']=='FAIL' and r['majority']=='FAIL' for r in complete)}
 agreement=groups['all']['agreement'];sc=groups['all']['self_consistency']
 return {'groups':groups,'confusion_matrix':matrix,'incomplete_cases':len(rows)-len(complete),'agreement':[agreement['k'],agreement['n']],'self_consistency':[sc['k'],sc['n']],'agreement_wilson':[agreement['low'],agreement['high']]}

def run(cases,path,model,temp,infer=None,output=None,rubric_override=None):
 infer=infer or judge_module.judge;stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=Path(output) if output else ROOT/'reports'/f'calibration-{Path(path).stem}-{stamp}-{uuid.uuid4().hex[:8]}.json'
 if out.exists():raise ValueError('Never overwrite a calibration report')
 report={'set':Path(path).stem,'set_hash':digest(path)[:12],'set_sha256':digest(path),'judge_model':model,'rubric_version':judge_module.RUBRIC_VERSION,'temperature_requested':temp,'temperature':temp,'planned_cases':len(cases),'agent_prompt_snapshot':'evidence/environment/readiness.json','agent_prompt_snapshot_sha256':digest(ROOT/'evidence/environment/readiness.json') if (ROOT/'evidence/environment/readiness.json').exists() else None,'runs':5,'ran_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cases':[],'status':'running','scope':'Frozen recorded answers, not fresh agent responses; n is cases, not 5n generations'}
 save(out,report)
 for c in cases:
  outputs=[];error=None
  for repeat in range(5):
   try:outputs.append(infer(c['input'],c['answer_under_test'],rubric_override or c['additional_metadata']['rubric'],model,temp))
   except Exception as e:error=f'{type(e).__name__}: {e}';break
   # Every successful paid verdict is durable before the next call.
   report['in_progress']={'id':c['id'],'outputs':outputs};save(out,report)
  report['cases'].append(case_result(c,outputs,error));report.pop('in_progress',None);report.update(metrics(report['cases']));save(out,report)
  if error:report['status']='ERROR';break
 else:report['status']='complete'
 if digest(path)!=report['set_sha256']:report['status']='ERROR';report['error']='Input changed during run'
 report.update(metrics(report['cases']));report['models_actual']=sorted({o.get('judge_model',model) for r in report['cases'] for o in r['outputs']});report['temperatures_effective']=sorted({o['temperature'] for r in report['cases'] for o in r['outputs'] if 'temperature' in o});save(out,report)
 code=2 if report['status']=='ERROR' else (0 if all(r['agree'] for r in report['cases']) else 1)
 return code,out,report

def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('set',nargs='?',default='l09_labels');p.add_argument('--validate-only',action='store_true');p.add_argument('--draft',action='store_true');p.add_argument('--diagnostic',action='store_true');p.add_argument('--rubric',type=Path);a=p.parse_args(argv);load_env()
 path=Path(a.set)
 if not path.exists():path=ROOT/'evals/sets'/(a.set+'.jsonl')
 if a.diagnostic:
  original=ROOT/'sources/l09-original'/path.name
  if not original.exists() or digest(path)!=digest(original):raise ValueError('Diagnostic must be an unchanged supplied source set')
  rows=loader.load(path)
  if any(c['additional_metadata'].get('label') not in ['PASS','FAIL'] for c in rows):raise ValueError('Reference diagnostic has no source labels')
  cases=validate(rows,reference=True)
 else:cases=validate(loader.load(path),allow_draft=a.draft and a.validate_only)
 if a.validate_only:print(json.dumps({'cases':len(cases),'draft':a.draft,'inference_calls':0}));return 0
 frozen=require_paid()
 if not a.diagnostic and path.resolve()!=(ROOT/frozen['labels_path']).resolve():raise ValueError('Only canonical frozen human labels may be calibrated')
 if not a.diagnostic and any(c['additional_metadata']['rubric']!=(ROOT/frozen['rubric_path']).read_text(encoding='utf-8') for c in cases):raise ValueError('Case rubric differs from frozen rubric file')
 if a.draft:raise ValueError('Draft inputs can never be run')
 model=os.environ.get('JUDGE_MODEL');temp=float(os.environ.get('HW8_JUDGE_TEMPERATURE','0.7'))
 if not model:raise ValueError('Exact JUDGE_MODEL required')
 versions={c['additional_metadata']['rubric_version'] for c in cases}
 if len(versions)!=1:raise ValueError('Mixed rubric versions')
 version=next(iter(versions));override=None
 if a.rubric:
  rp=a.rubric.resolve();name=rp.relative_to(ROOT).as_posix()
  if subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT)!=rp.read_bytes():raise ValueError('Commit rubric amendment before inference')
  override=rp.read_text(encoding='utf-8');version=rp.stem
  if version==next(iter(versions)):raise ValueError('Amendment needs a new version')
 judge_module.RUBRIC_VERSION=version
 code,out,report=run(cases,path,model,temp,rubric_override=override);print(out.relative_to(ROOT));print(report['groups']['all']);return code
if __name__=='__main__':
 try:sys.exit(main())
 except (ValueError,RuntimeError,loader.SetError) as e:print(str(e),file=sys.stderr);sys.exit(2)
