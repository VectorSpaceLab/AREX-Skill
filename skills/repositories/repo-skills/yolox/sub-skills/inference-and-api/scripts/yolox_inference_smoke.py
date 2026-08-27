#!/usr/bin/env python3
"""Safe YOLOX inference/API smoke check."""
from __future__ import annotations
import argparse, importlib, sys
from typing import Dict, Iterable, Tuple
BUILTIN_NAMES=("yolox-s","yolox-m","yolox-l","yolox-x","yolox-tiny","yolox-nano","yolov3")
CORE_IMPORTS=("torch","torchvision","cv2","yolox","yolox.exp","yolox.data.data_augment","yolox.utils")
OPTIONAL_IMPORTS=("loguru","tqdm","thop","tabulate","psutil","pycocotools","onnx","onnxsim","onnxruntime")

def parse_args():
    p=argparse.ArgumentParser(description="Check YOLOX imports, resolve an experiment, build a model, report model info, and optionally run a dummy forward.")
    p.add_argument("--name",default="yolox-nano",choices=BUILTIN_NAMES)
    p.add_argument("--exp-file","--exp_file",dest="exp_file",default=None)
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--dummy-forward",action="store_true")
    p.add_argument("--test-size",type=int,default=64)
    return p.parse_args()

def check_imports(names:Iterable[str])->Tuple[Dict[str,str],Dict[str,str]]:
    ok,fail={},{}
    for n in names:
        try:
            m=importlib.import_module(n); ok[n]=str(getattr(m,"__version__","imported"))
        except Exception as e:
            fail[n]=f"{type(e).__name__}: {e}"
    return ok,fail

def report(title, ok, fail):
    print(f"[{title}]")
    for n in sorted(ok): print(f"  OK   {n}: {ok[n]}")
    for n in sorted(fail): print(f"  FAIL {n}: {fail[n]}")

def resolve_device(requested, torch):
    if requested=="auto": requested="cuda" if torch.cuda.is_available() else "cpu"
    if requested=="cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but torch.cuda.is_available() is False")
    return torch.device(requested)

def main():
    a=parse_args()
    if a.test_size<=0:
        print("ERROR: --test-size must be positive", file=sys.stderr); return 2
    if a.test_size%32:
        print("WARNING: a test-size multiple of 32 is recommended", file=sys.stderr)
    ok,fail=check_imports(CORE_IMPORTS); report("core imports",ok,fail)
    if fail:
        print("ERROR: core imports failed", file=sys.stderr); return 1
    ok2,fail2=check_imports(OPTIONAL_IMPORTS); report("optional/support imports",ok2,fail2)
    if fail2: print("WARNING: optional imports failed; some dataset/eval/export helpers may be unavailable", file=sys.stderr)
    import torch, yolox
    from yolox.exp import get_exp
    from yolox.utils import get_model_info, postprocess
    print(f"YOLOX version: {getattr(yolox,'__version__','unknown')}")
    try: device=resolve_device(a.device, torch)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr); return 1
    print(f"Selected device: {device}")
    if device.type=="cuda":
        torch.empty((1,),device=device); torch.cuda.synchronize(); print("CUDA allocation check: OK")
    try: exp=get_exp(a.exp_file,a.name)
    except Exception as e:
        print(f"ERROR: experiment resolution failed: {type(e).__name__}: {e}", file=sys.stderr); return 1
    print(f"Experiment resolved from {'file '+a.exp_file if a.exp_file else 'name '+a.name}")
    for f in ("exp_name","num_classes","depth","width","test_size"): print(f"  {f}: {getattr(exp,f,'<missing>')}")
    size=(a.test_size,a.test_size)
    try:
        exp.test_size=size; model=exp.get_model(); model.eval().to(device); print("Model construction: OK")
        try: print(f"Model info at test_size={size}: {get_model_info(model,size)}")
        except Exception as e: print(f"WARNING: get_model_info failed: {type(e).__name__}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"ERROR: model construction failed: {type(e).__name__}: {e}", file=sys.stderr); return 1
    if a.dummy_forward:
        try:
            x=torch.zeros((1,3,a.test_size,a.test_size),device=device)
            with torch.no_grad(): raw=model(x)
            print(f"Dummy forward: OK, raw output shape/type: {tuple(raw.shape) if hasattr(raw,'shape') else type(raw).__name__}")
            out=postprocess(raw.detach().float().cpu(),getattr(exp,"num_classes",80),0.99,0.45,True)
            print("Postprocess smoke: OK", [None if z is None else tuple(z.shape) for z in out])
        except Exception as e:
            print(f"ERROR: dummy forward/postprocess failed: {type(e).__name__}: {e}", file=sys.stderr); return 1
    else: print("Dummy forward: skipped (pass --dummy-forward to enable)")
    print("YOLOX inference smoke completed successfully."); return 0
if __name__=="__main__": raise SystemExit(main())
