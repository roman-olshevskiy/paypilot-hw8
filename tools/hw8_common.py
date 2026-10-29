"""Local configuration helpers. Never print secret values."""
import os,json,hashlib,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load_env():
 p=ROOT/'.env'
 if p.exists():
  for line in p.read_text(encoding='utf-8-sig').splitlines():
   if '=' in line and not line.lstrip().startswith('#'):
    key,value=line.split('=',1);os.environ.setdefault(key.strip(),value.strip().strip(chr(34)).strip(chr(39)))
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp-'+uuid.uuid4().hex);tmp.write_bytes((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8'));os.replace(tmp,path)
