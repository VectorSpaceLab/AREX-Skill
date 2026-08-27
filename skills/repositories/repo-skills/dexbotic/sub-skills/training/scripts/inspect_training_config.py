#!/usr/bin/env python3
"""Static training-config preflight; never launches a job or downloads weights."""
from __future__ import annotations
import argparse, json
from pathlib import Path

BACKENDS={"ddp","deepspeed","fsdp","fsdp2"}

def load(path):
    text=path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".json"}:
        return json.loads(text)
    try:
        import yaml
    except ImportError:
        raise SystemExit("YAML input requires PyYAML; use JSON or install it in the inspection environment")
    return yaml.safe_load(text)

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("config",type=Path); ap.add_argument("--report",type=Path); a=ap.parse_args()
    try: cfg=load(a.config)
    except Exception as e: print(json.dumps({"ok":False,"error":str(e)},indent=2)); raise SystemExit(1)
    if not isinstance(cfg,dict): raise SystemExit("config root must be a mapping")
    flat=cfg
    # Accept common nested config layouts without pretending to resolve Hydra.
    trainer=cfg.get("trainer_config",cfg.get("trainer",{})) or {}
    model=cfg.get("model_config",cfg.get("model",{})) or {}
    data=cfg.get("data_config",cfg.get("data",{})) or {}
    backend=trainer.get("train_backend",cfg.get("train_backend","deepspeed"))
    errors=[]; warnings=[]
    if backend not in BACKENDS: errors.append(f"unsupported train_backend: {backend}")
    for key,obj in (("model_name_or_path",model),("dataset_name",data)):
        if key not in obj and key not in cfg: warnings.append(f"missing visible {key}; Hydra/dataclass composition may provide it")
    out=trainer.get("output_dir",cfg.get("output_dir"));
    if out and Path(str(out)).exists(): warnings.append("output_dir already exists; confirm it is not an input checkpoint")
    if backend=="deepspeed" and (trainer.get("fsdp") or cfg.get("fsdp")): errors.append("DeepSpeed selected while FSDP strategy is configured")
    if backend in {"fsdp","fsdp2"} and not (trainer.get("fsdp") or cfg.get("fsdp")): errors.append(f"{backend} requires an fsdp strategy")
    result={"ok":not errors,"requested_backend":backend,"errors":errors,"warnings":warnings,"model":model,"data":data,"trainer":trainer}
    print(json.dumps(result,indent=2,default=str));
    if a.report: a.report.write_text(json.dumps(result,indent=2,default=str)+"\n",encoding="utf-8")
    raise SystemExit(0 if not errors else 1)
if __name__=="__main__": main()
