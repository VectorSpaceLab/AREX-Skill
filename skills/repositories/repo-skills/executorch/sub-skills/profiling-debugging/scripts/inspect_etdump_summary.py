#!/usr/bin/env python3
"""Sanity-check ExecuTorch debug artifacts and Inspector availability."""
from __future__ import annotations
import argparse, json
from pathlib import Path


def file_info(path: str | None):
    if not path:
        return None
    p = Path(path)
    return {"path": str(p), "exists": p.exists(), "size": p.stat().st_size if p.exists() else None}


def main():
    ap = argparse.ArgumentParser(description="Check ETDump/ETRecord/debug-buffer files and Inspector importability.")
    ap.add_argument("--etdump")
    ap.add_argument("--etrecord")
    ap.add_argument("--debug-buffer")
    ap.add_argument("--try-inspector", action="store_true", help="Instantiate Inspector if imports and files allow it.")
    args = ap.parse_args()
    report = {"files": {"etdump": file_info(args.etdump), "etrecord": file_info(args.etrecord), "debug_buffer": file_info(args.debug_buffer)}}
    try:
        from executorch.devtools import Inspector
        report["inspector_import"] = "ok"
        if args.try_inspector and args.etdump:
            inspector = Inspector(etdump_path=args.etdump, etrecord=args.etrecord, debug_buffer_path=args.debug_buffer)
            report["inspector_type"] = type(inspector).__name__
    except Exception as exc:
        report["inspector_import"] = f"{type(exc).__name__}: {exc}"
    print(json.dumps(report, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

