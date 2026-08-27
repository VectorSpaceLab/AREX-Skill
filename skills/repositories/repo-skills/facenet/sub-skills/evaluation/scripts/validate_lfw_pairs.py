#!/usr/bin/env python3
"""Validate a Facenet LFW pairs file against an aligned LFW directory."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


def has_image(base: Path) -> bool:
    return base.with_suffix(".jpg").exists() or base.with_suffix(".png").exists()


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Facenet LFW pair files.")
    parser.add_argument("pairs_file", type=Path)
    parser.add_argument("lfw_dir", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.pairs_file.exists():
        print(f"pairs file missing: {args.pairs_file}", file=sys.stderr)
        return 1

    lines = args.pairs_file.read_text().splitlines()[1:]
    missing = []
    for lineno, line in enumerate(lines, start=2):
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) == 3:
            refs = [(fields[0], fields[1]), (fields[0], fields[2])]
        elif len(fields) == 4:
            refs = [(fields[0], fields[1]), (fields[2], fields[3])]
        else:
            missing.append((lineno, line, "expected 3 or 4 columns"))
            continue
        for person, num in refs:
            base = args.lfw_dir / person / f"{person}_{int(num):04d}"
            if not has_image(base):
                missing.append((lineno, str(base), "image missing"))

    ok = not missing
    if args.json:
        import json
        print(json.dumps({"ok": ok, "missing": missing}, indent=2))
    else:
        print(f"OK={ok} missing={len(missing)}")
        for item in missing[:20]:
            print(f"row {item[0]}: {item[1]} ({item[2]})")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
