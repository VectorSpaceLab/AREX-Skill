#!/usr/bin/env python3
"""Validate a small deployment manifest without contacting hardware."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("manifest",type=Path); a=ap.parse_args()
    try:
        d=json.loads(a.manifest.read_text(encoding="utf-8"))
    except Exception as e: raise SystemExit(f"invalid JSON: {e}")
    required=("checkpoint","server_url","camera_order","action_dim","action_mode","fps")
    missing=[k for k in required if k not in d]
    errors=[]
    if missing: errors.append("missing: "+", ".join(missing))
    if "action_dim" in d and (not isinstance(d["action_dim"],int) or d["action_dim"]<=0): errors.append("action_dim must be positive integer")
    if "camera_order" in d and (not isinstance(d["camera_order"],list) or not d["camera_order"]): errors.append("camera_order must be non-empty list")
    if d.get("action_mode") not in {"absolute","relative","unknown",None}: errors.append("action_mode must be absolute, relative, or unknown")
    if "fps" in d and (not isinstance(d["fps"],(int,float)) or d["fps"]<=0): errors.append("fps must be positive")
    out={"ok":not errors,"errors":errors,"hardware_contacted":False,"manifest":d}; print(json.dumps(out,indent=2)); raise SystemExit(0 if not errors else 1)
if __name__=="__main__":main()
