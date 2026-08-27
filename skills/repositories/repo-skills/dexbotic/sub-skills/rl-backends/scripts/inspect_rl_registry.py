#!/usr/bin/env python3
"""Read-only inspection of a Dexbotic RL registry module."""
from __future__ import annotations
import argparse, importlib, json

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("module",nargs="?",default="dexbotic.rl.rlinf_registry"); a=ap.parse_args()
    try: m=importlib.import_module(a.module)
    except Exception as e: print(json.dumps({"ok":False,"module":a.module,"error":repr(e),"external_runtime_required":True},indent=2)); raise SystemExit(1)
    names=[n for n in dir(m) if not n.startswith("_")]
    print(json.dumps({"ok":True,"module":a.module,"public_names":names,"external_runtime_required":True},indent=2))
if __name__=="__main__":main()
