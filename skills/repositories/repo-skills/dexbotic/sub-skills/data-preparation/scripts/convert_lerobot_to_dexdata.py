#!/usr/bin/env python3
"""Conservative LeRobot-parquet to DexData JSONL adapter.

This adapter converts tabular state/action rows and does not copy, transcode,
or execute media commands. Provide camera references with repeated
--camera NAME=URL options; URLs are written as metadata only.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any

def tasks(meta: Path) -> list[str]:
    p=meta/"tasks.jsonl"
    if not p.exists(): return []
    out=[]
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            d=json.loads(line); out.append(str(d.get("task",d.get("instruction",""))))
    return out

def native(v: Any):
    if hasattr(v,"tolist"): return v.tolist()
    if isinstance(v,(list,tuple)): return list(v)
    return v

def convert(input_dir: Path, output_dir: Path, camera: dict[str,str], prompt_override: str|None, max_files: int|None):
    try: import pandas as pd
    except ImportError: raise SystemExit("This adapter requires pandas and a parquet engine; install them in an isolated data environment")
    files=sorted(input_dir.rglob("*.parquet")); files=files[:max_files] if max_files else files
    if not files: raise SystemExit(f"no parquet files below {input_dir}")
    task_list=tasks(input_dir/"meta")
    output_dir.mkdir(parents=True,exist_ok=True); total=0
    for idx,path in enumerate(files):
        df=pd.read_parquet(path); records=[]
        for row_idx, row in df.iterrows():
            state=native(row.get("observation.state", [])); action=native(row.get("action", []))
            if not isinstance(state,list) or not isinstance(action,list): continue
            task_idx=int(row.get("task_index",0)) if "task_index" in df.columns else 0
            prompt=prompt_override or (task_list[task_idx] if task_idx<len(task_list) else input_dir.name.replace("_"," "))
            rec={"state":state,"action":action,"prompt":prompt,"is_robot":True,"extra":{"source_file":path.name,"source_row":int(row_idx)}}
            frame=int(row.get("frame_index",row_idx))
            for n,(name,url) in enumerate(sorted(camera.items()),1): rec[f"images_{n}"]={"type":"video" if url.lower().endswith((".mp4",".webm",".avi")) else "image","url":url,"frame_idx":frame} if "." in url.rsplit("/",1)[-1] else {"type":"image","url":url}
            records.append(rec)
        if records:
            (output_dir/f"episode_{idx:05d}.jsonl").write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in records),encoding="utf-8"); total+=len(records)
    print(json.dumps({"files":len(files),"records":total,"output":str(output_dir)},indent=2))

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("-i","--input-dir",type=Path,required=True); ap.add_argument("-o","--output-dir",type=Path,required=True); ap.add_argument("--camera",action="append",default=[],metavar="NAME=URL"); ap.add_argument("--prompt"); ap.add_argument("--max-files",type=int); a=ap.parse_args()
    cams={}
    for item in a.camera:
        if "=" not in item: raise SystemExit("--camera must be NAME=URL")
        k,v=item.split("=",1); cams[k]=v
    convert(a.input_dir,a.output_dir,cams,a.prompt,a.max_files)
if __name__=="__main__":main()
