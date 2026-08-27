#!/usr/bin/env python3
"""Summarize numeric fields in line-delimited JSON Det3D logs."""
from __future__ import annotations
import argparse
import json
from collections import defaultdict
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description="Summarize Det3D JSON-lines logs without plotting")
    p.add_argument("log", type=Path)
    args = p.parse_args()
    values = defaultdict(list)
    skipped = 0
    records = 0
    with args.log.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except (json.JSONDecodeError, TypeError):
                skipped += 1
                continue
            records += 1
            for key, value in row.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    values[key].append(float(value))
    summary = {k: {"count": len(v), "latest": v[-1], "min": min(v), "max": max(v), "mean": sum(v)/len(v)} for k, v in sorted(values.items()) if v}
    print(json.dumps({"records": records, "skipped_lines": skipped, "metrics": summary}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
