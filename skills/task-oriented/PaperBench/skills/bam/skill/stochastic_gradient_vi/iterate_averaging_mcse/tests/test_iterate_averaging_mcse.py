import json,subprocess,sys,tempfile
from pathlib import Path
def test_skill_smoke():
 d=Path(tempfile.mkdtemp()); scr=Path(__file__).resolve().parents[1]/'scripts'/'robust_svi.py'; chain=d/'chain.json'; rh=d/'rhat.json'; av=d/'avg.json'; subprocess.run([sys.executable,str(scr),'chain','--output',str(chain),'--iterations','140'],check=True); subprocess.run([sys.executable,str(scr),'rhat','--input',str(chain),'--output',str(rh),'--window-size','40'],check=True); rr=json.loads(rh.read_text()); start=rr.get('start_iteration') or 79; subprocess.run([sys.executable,str(scr),'avg','--input',str(chain),'--output',str(av),'--start-iteration',str(start)],check=True); aa=json.loads(av.read_text()); assert aa['sample_count']>0
