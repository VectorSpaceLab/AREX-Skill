#!/usr/bin/env python3
"""Lightweight validator for HanLP-like Document JSON."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
KNOWN = {"tok","pos","lem","fea","ner","dep","con","srl","sdp","amr"}

def main():
    ap = argparse.ArgumentParser(description="Validate common HanLP Document JSON shape.")
    ap.add_argument("path", nargs="?"); ap.add_argument("--stdin", action="store_true")
    a = ap.parse_args()
    obj = json.load(sys.stdin) if a.stdin else json.loads(Path(a.path).read_text(encoding="utf-8"))
    if not isinstance(obj, dict): raise SystemExit("Document JSON must be an object")
    warnings = []
    for k,v in obj.items():
        if k.split('/',1)[0] not in KNOWN: warnings.append(f"unknown task prefix: {k}")
        if not isinstance(v, list): warnings.append(f"{k}: expected list value")
    print(json.dumps({"ok": not any('expected' in w for w in warnings), "keys": list(obj), "warnings": warnings}, ensure_ascii=False, indent=2))
    return 0 if not any('expected' in w for w in warnings) else 1
if __name__ == "__main__": raise SystemExit(main())
