"""Fresh clone + Docker offline suite. No account secrets and no inference flags."""
import json,os,re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 with tempfile.TemporaryDirectory(prefix='hw8-docker-clone-') as tmp:
  clone=Path(tmp)/'repo';subprocess.run(['git','clone','--quiet','--no-hardlinks',str(ROOT),str(clone)],check=True);assert not (clone/'.env').exists();assert not subprocess.check_output(['git','status','--porcelain'],cwd=clone)
  env=dict(os.environ);env['STAND_DIR']=str(ROOT.parent/'paypilot-stand-shared');env['COMPOSE_PROJECT_NAME']='hw8-offline-verification'
  for name in ['HW8_PAID','HW8_PILOT','HW8_SERIES','HW8_ENV','HW8_SETTLE']:env.pop(name,None)
  cmd=['docker','compose','run','--rm','eval','python','-m','unittest','discover','-s','tests','-v'];r=subprocess.run(cmd,cwd=clone,env=env,capture_output=True,text=True,encoding='utf-8');text=r.stdout+r.stderr
  if r.returncode:print(text[-5000:]);raise RuntimeError('Docker offline clone tests failed')
  count=int(re.search(r'Ran (\d+) tests',text).group(1));skip=int(re.search(r'OK \(skipped=(\d+)\)',text).group(1));assert not subprocess.check_output(['git','status','--porcelain'],cwd=clone)
  proof={'clone_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=clone,text=True).strip(),'clean_before_and_after':True,'scope':'Actual offline unittest suite in Docker from a fresh Git clone; .env absent, explicit live flags absent','tests':count,'passed':count-skip,'skipped':skip,'inference_calls':0,'command':cmd}
  (ROOT/'evidence/clean-clone-docker.json').write_bytes((json.dumps(proof,indent=2)+'\n').encode('utf-8'));print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
