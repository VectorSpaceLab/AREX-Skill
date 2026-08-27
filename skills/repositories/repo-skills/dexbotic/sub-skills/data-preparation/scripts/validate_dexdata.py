#!/usr/bin/env python3
"""Read-only DexData JSONL validator.

Usage: python validate_dexdata.py DATA_ROOT [--report REPORT.json]
It checks JSONL syntax, required semantic fields, numeric finiteness, and
cross-record state/action dimensions. It does not open media or modify data.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
from typing import Any


def finite_seq(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(x, (int, float)) and math.isfinite(float(x)) for x in value
    )


def check_record(record: dict[str, Any], path: Path, line: int, state_dim: int|None, action_dim: int|None):
    errors=[]
    image_keys=sorted(k for k in record if k.startswith("images_"))
    if not image_keys: errors.append("missing images_N field")
    if not isinstance(record.get("prompt"), str) and not isinstance(record.get("conversations"), list):
        errors.append("missing prompt or conversations")
    if "state" in record and not finite_seq(record["state"]): errors.append("state is not a finite non-empty numeric list")
    if "action" in record and not finite_seq(record["action"]): errors.append("action is not a finite non-empty numeric list")
    for key in image_keys:
        value=record[key]
        if not isinstance(value, dict) or value.get("type") not in {"image","video"} or not value.get("url"):
            errors.append(f"{key} must contain type image/video and url")
        if isinstance(value, dict) and value.get("type")=="video" and not isinstance(value.get("frame_idx"), int):
            errors.append(f"{key} video frame_idx must be an integer")
    if finite_seq(record.get("state")) and state_dim not in (None, len(record["state"])): errors.append(f"state dimension changed (expected {state_dim})")
    if finite_seq(record.get("action")) and action_dim not in (None, len(record["action"])): errors.append(f"action dimension changed (expected {action_dim})")
    return errors, (len(record["state"]) if finite_seq(record.get("state")) else state_dim), (len(record["action"]) if finite_seq(record.get("action")) else action_dim)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("data_root", type=Path)
    ap.add_argument("--report", type=Path)
    args=ap.parse_args()
    files=sorted(args.data_root.rglob("*.jsonl")) if args.data_root.is_dir() else [args.data_root]
    errors=[]; records=0; state_dim=action_dim=None
    for path in files:
        try:
            with path.open(encoding="utf-8") as fh:
                for line_no, raw in enumerate(fh,1):
                    if not raw.strip(): continue
                    records+=1
                    try: rec=json.loads(raw)
                    except Exception as exc: errors.append({"file":str(path),"line":line_no,"error":f"invalid JSON: {exc}"}); continue
                    if not isinstance(rec,dict): errors.append({"file":str(path),"line":line_no,"error":"record is not an object"}); continue
                    es,state_dim,action_dim=check_record(rec,path,line_no,state_dim,action_dim)
                    errors.extend({"file":str(path),"line":line_no,"error":e} for e in es)
        except OSError as exc: errors.append({"file":str(path),"line":0,"error":str(exc)})
    result={"files":len(files),"records":records,"state_dim":state_dim,"action_dim":action_dim,"errors":errors,"ok":not errors}
    print(json.dumps(result,indent=2))
    if args.report: args.report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    raise SystemExit(0 if not errors else 1)
if __name__=="__main__": main()
