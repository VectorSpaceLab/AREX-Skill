#!/usr/bin/env python3
"""Check a JSON weighted-box-clustering input before running post-processing."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-file", type=Path, required=True, help="JSON object with dets and box_patch_id arrays")
    args = p.parse_args()
    obj = json.loads(args.input_file.read_text())
    errors = []
    if not isinstance(obj, dict):
        errors.append("top-level JSON must be an object")
    else:
        dets = obj.get("dets")
        patch_ids = obj.get("box_patch_id")
        if not isinstance(dets, list) or not dets:
            errors.append("dets must be a non-empty list")
        if not isinstance(patch_ids, list) or len(patch_ids) != len(dets or []):
            errors.append("box_patch_id must be a list with one entry per detection")
        for i, row in enumerate(dets or []):
            if not isinstance(row, list) or len(row) not in (7, 9):
                errors.append(f"dets[{i}] must have 7 (2D) or 9 (3D) numeric columns: coordinates, score, patch-center factor, overlap count")
                continue
            if not all(isinstance(x, (int, float)) for x in row):
                errors.append(f"dets[{i}] contains a non-numeric value")
    result = {"valid": not errors, "errors": errors}
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
