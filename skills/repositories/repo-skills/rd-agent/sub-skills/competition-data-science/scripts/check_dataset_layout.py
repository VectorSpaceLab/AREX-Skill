#!/usr/bin/env python3
"""Validate the documented custom RD-Agent data-science task layout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("task")
    args = parser.parse_args()
    task_root = args.root / args.task
    candidates = {
        "source_prepare": args.root / "source_data" / args.task / "prepare.py",
        "description": task_root / "description.md",
        "sample": task_root / "sample.py",
        "grade": args.root / "eval" / args.task / "grade.py",
        "valid": args.root / "eval" / args.task / "valid.py",
    }
    result = {name: {"path": str(path), "exists": path.exists()} for name, path in candidates.items()}
    required = ("source_prepare", "description")
    print(json.dumps(result, indent=2))
    return 0 if all(result[name]["exists"] for name in required) else 2


if __name__ == "__main__":
    raise SystemExit(main())
