#!/usr/bin/env python3
"""Statically inspect a MiniMind-V Transformers-format export directory."""
from __future__ import annotations
import argparse, json
from pathlib import Path
WEIGHT_SUFFIXES=(".bin",".safetensors"); INDEX_NAMES=("pytorch_model.bin.index.json","model.safetensors.index.json")

def read_json(path: Path):
    if not path.is_file(): return None, "missing"
    try:
        data=json.loads(path.read_text(encoding="utf-8"))
        return (data, None) if isinstance(data, dict) else (None, "JSON root is not an object")
    except Exception as exc: return None, f"invalid JSON: {type(exc).__name__}: {exc}"

def weights(d: Path):
    return [] if not d.is_dir() else [p.name for p in sorted(d.iterdir()) if p.is_file() and (p.name in INDEX_NAMES or p.name.endswith(WEIGHT_SUFFIXES))]

def add(res, level, msg): res[level].append(msg)
def eq(res,label,value,expected,level="fail"):
    add(res,"pass",f"{label}: {value!r}") if value==expected else add(res,level,f"{label}: expected {expected!r}, got {value!r}")

def summarize(export_dir: Path):
    d=export_dir.expanduser(); res={"pass":[],"warn":[],"fail":[]}; report={"export_dir":str(d),"results":res,"weight_files":[]}
    if not d.exists(): add(res,"fail","export directory does not exist"); return report
    if not d.is_dir(): add(res,"fail","export path is not a directory"); return report
    add(res,"pass","export directory exists")
    cfg,err=read_json(d/"config.json")
    if err: add(res,"fail",f"config.json {err}")
    else:
        add(res,"pass","config.json is readable"); eq(res,"config.model_type",cfg.get("model_type"),"minimind-v","warn"); eq(res,"config.tie_word_embeddings",cfg.get("tie_word_embeddings"),True,"warn")
        if cfg.get("image_special_token") is not None: eq(res,"config.image_special_token",cfg.get("image_special_token"),"<|image_pad|>","warn")
        else: add(res,"warn","config.image_special_token missing")
        ids=cfg.get("image_ids"); add(res,"pass","config.image_ids includes 12") if isinstance(ids,list) and 12 in ids else add(res,"warn",f"config.image_ids expected to include 12, got {ids!r}")
        if cfg.get("image_hidden_size") is not None: eq(res,"config.image_hidden_size",cfg.get("image_hidden_size"),768,"warn")
        if cfg.get("image_token_len") is not None: eq(res,"config.image_token_len",cfg.get("image_token_len"),64,"warn")
        add(res,"pass","config.auto_map present") if "auto_map" in cfg else add(res,"warn","config.auto_map missing")
        add(res,"warn","config.rope_parameters present") if "rope_parameters" in cfg else add(res,"pass","config.rope_parameters absent")
    tok,terr=read_json(d/"tokenizer_config.json")
    if terr: add(res,"fail",f"tokenizer_config.json {terr}")
    else:
        add(res,"pass","tokenizer_config.json is readable")
        if tok.get("tokenizer_class") == "PreTrainedTokenizerFast": add(res,"pass","tokenizer_class is PreTrainedTokenizerFast")
        else: add(res,"warn",f"tokenizer_class is {tok.get('tokenizer_class')!r}")
        if tok.get("extra_special_tokens") == {}: add(res,"pass","extra_special_tokens is {}")
        else: add(res,"warn","extra_special_tokens is missing or non-empty")
    for name in ["tokenizer.json","tokenizer_config.json"]:
        add(res,"pass",f"{name} exists") if (d/name).is_file() else add(res,"fail",f"{name} missing")
    wf=weights(d); report["weight_files"]=wf
    add(res,"pass","model weight file or shard index present: "+", ".join(wf[:6])) if wf else add(res,"fail","no .bin/.safetensors weight file or known shard index found")
    py=[p.name for p in sorted(d.iterdir()) if p.is_file() and p.suffix==".py"]
    if py: add(res,"pass","custom code file(s) present: "+", ".join(py[:6]))
    elif cfg and "auto_map" in cfg: add(res,"pass","custom code may be resolved by auto_map")
    else: add(res,"warn","no custom .py files and no auto_map")
    return report

def main(argv=None):
    p=argparse.ArgumentParser(description="Inspect MiniMind-V Transformers export metadata without loading weights.")
    p.add_argument("--export-dir", required=True, type=Path); p.add_argument("--json", action="store_true"); p.add_argument("--strict", action="store_true")
    a=p.parse_args(argv); report=summarize(a.export_dir)
    if a.json: print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("MiniMind-V Transformers export static inspection"); print("Export directory:", report["export_dir"])
        for level,title in [("pass","PASS"),("warn","WARN"),("fail","FAIL")]:
            if report["results"][level]:
                print(f"\n{title}:"); [print("  -",x) for x in report["results"][level]]
        print("\nThis helper did not import Transformers, execute custom code, or load weights.")
    return 1 if report["results"]["fail"] or (a.strict and report["results"]["warn"]) else 0
if __name__=="__main__": raise SystemExit(main())
