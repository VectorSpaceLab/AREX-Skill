#!/usr/bin/env python3
"""Validate a local JSON task-sample contract without clinical data access."""
import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("samples", type=Path, help="JSON array of task samples")
    parser.add_argument("--input", action="append", default=[], help="required input key")
    parser.add_argument("--output", action="append", default=[], help="required output/label key")
    parser.add_argument("--id-key", default="patient_id")
    args = parser.parse_args()
    rows = json.loads(args.samples.read_text())
    if not isinstance(rows, list) or not rows or not all(isinstance(row, dict) for row in rows):
        raise SystemExit("samples must be a non-empty JSON array of objects")
    required = args.input + args.output + [args.id_key]
    missing = {key: [i for i, row in enumerate(rows) if key not in row] for key in required}
    missing = {key: indices for key, indices in missing.items() if indices}
    ids = [row.get(args.id_key) for row in rows]
    result = {"count": len(rows), "unique_ids": len(set(ids)), "missing": missing}
    print(json.dumps(result, indent=2))
    return 0 if not missing else 1

if __name__ == "__main__":
    raise SystemExit(main())
