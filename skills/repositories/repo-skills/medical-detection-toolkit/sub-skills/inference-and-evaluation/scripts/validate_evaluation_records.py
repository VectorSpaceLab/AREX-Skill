#!/usr/bin/env python3
"""Validate a bounded JSON patient/result record shape before evaluation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-file", type=Path, required=True)
    args = p.parse_args()
    records = json.loads(args.input_file.read_text())
    errors = []
    if not isinstance(records, list) or not records:
        errors.append("top-level JSON must be a non-empty list")
    for i, record in enumerate(records if isinstance(records, list) else []):
        if not isinstance(record, dict):
            errors.append(f"record {i} must be an object")
            continue
        if "pid" not in record:
            errors.append(f"record {i} is missing pid")
        boxes = record.get("boxes", [])
        if not isinstance(boxes, list):
            errors.append(f"record {i}.boxes must be a list")
            continue
        for j, box in enumerate(boxes):
            if not isinstance(box, dict):
                errors.append(f"record {i} box {j} must be an object")
                continue
            required = {"box_type", "box_coords"}
            missing = required - box.keys()
            if missing:
                errors.append(f"record {i} box {j} missing {sorted(missing)}")
            coords = box.get("box_coords")
            if not isinstance(coords, list) or len(coords) not in (4, 6):
                errors.append(f"record {i} box {j} coordinates must have length 4 or 6")
    result = {"valid": not errors, "records": len(records) if isinstance(records, list) else 0, "errors": errors}
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
