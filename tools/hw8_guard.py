"""Paid inference is impossible until explicitly enabled after human-label freeze."""
import os,json,subprocess
from pathlib import Path
from hw8_common import ROOT,digest

def verify_freeze():
 path=ROOT/'evidence/labels-freeze.json'
 if not path.exists():raise RuntimeError('Human labels are not frozen. Finish human review before any judge inference.')
 f=json.loads(path.read_text(encoding='utf-8'));labels=ROOT/f['labels_path']
 if f.get('human_review_confirmed') is not True:raise RuntimeError('Human review not confirmed')
 for field in ['labels','rubric','forecast']:
  p=ROOT/f[field+'_path']
  if digest(p)!=f[field+'_sha256']:raise RuntimeError(field+' changed after freeze')
  raw=subprocess.check_output(['git','show',f['commit']+':'+f[field+'_path']],cwd=ROOT)
  if raw!=p.read_bytes():raise RuntimeError(field+' differs from its committed freeze')
 return f

def require_paid():
 if os.environ.get('HW8_PAID')!='1':raise RuntimeError('Paid inference disabled. HW8_PAID=1 must be explicit; stop before pilot.')
 return verify_freeze()
