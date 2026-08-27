#!/usr/bin/env python3
"""Compare two binary/file sizes and report absolute and percentage delta."""
from __future__ import annotations
import argparse, json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="Compare before/after file sizes.")
    ap.add_argument("--before", type=Path, required=True)
    ap.add_argument("--after", type=Path, required=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    before = args.before.stat().st_size
    after = args.after.stat().st_size
    delta = after - before
    pct = (delta / before * 100.0) if before else None
    report = {"before": str(args.before), "after": str(args.after), "before_bytes": before, "after_bytes": after, "delta_bytes": delta, "delta_percent": pct}
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        sign = "+" if delta >= 0 else ""
        pct_text = "n/a" if pct is None else f"{pct:+.2f}%"
        print(f"before={before} bytes after={after} bytes delta={sign}{delta} bytes ({pct_text})")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

