#!/usr/bin/env python3
"""Inspect a labelme-exported label PNG for dtype, shape, and values."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import PIL.Image


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("label_png", type=Path)
    parser.add_argument("--expect-values", help="comma-separated integer values expected to be present")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    arr = np.asarray(PIL.Image.open(args.label_png))
    values = sorted(int(v) for v in np.unique(arr))
    report = {"path": str(args.label_png), "dtype": str(arr.dtype), "shape": list(arr.shape), "values": values}
    ok = True
    if args.expect_values:
        expected = sorted(int(v.strip()) for v in args.expect_values.split(",") if v.strip())
        missing = sorted(set(expected) - set(values))
        report["expectedValues"] = expected
        report["missingValues"] = missing
        ok = not missing
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"{report['path']}: dtype={report['dtype']} shape={tuple(report['shape'])} values={report['values']}")
        if report.get("missingValues"):
            print(f"ERROR: missing expected values {report['missingValues']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
