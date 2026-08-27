#!/usr/bin/env python3
"""Validate a KITTI detection-result directory without running an evaluator."""
import argparse
import math
from pathlib import Path
import sys

TYPES = {"Car", "Pedestrian", "Cyclist", "Van", "Truck", "Tram", "Person_sitting", "Misc", "DontCare"}


def validate_file(path):
    errors = []
    for number, raw in enumerate(path.read_text().splitlines(), 1):
        if not raw.strip():
            continue
        fields = raw.split()
        if len(fields) not in (15, 16):
            errors.append("%s:%d expected 15 or 16 fields, got %d" % (path, number, len(fields)))
            continue
        if fields[0] not in TYPES:
            errors.append("%s:%d unknown object type %s" % (path, number, fields[0]))
        try:
            values = [float(v) for v in fields[1:]]
            if not all(math.isfinite(v) for v in values):
                errors.append("%s:%d contains non-finite numeric values" % (path, number))
            xmin, ymin, xmax, ymax = values[3:7]
            if xmax < xmin or ymax < ymin:
                errors.append("%s:%d has reversed 2D box" % (path, number))
        except ValueError:
            errors.append("%s:%d contains a non-numeric field" % (path, number))
    return errors


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("result_dir", type=Path, help="directory containing per-frame KITTI text files")
    p.add_argument("--require-data-subdir", action="store_true", help="look under result-dir/data")
    a = p.parse_args()
    root = a.result_dir / "data" if a.require_data_subdir else a.result_dir
    if not root.is_dir():
        print("ERROR: missing result directory: %s" % root, file=sys.stderr)
        return 1
    files = sorted(root.glob("*.txt"))
    if not files:
        print("ERROR: no per-frame .txt files under %s" % root, file=sys.stderr)
        return 1
    errors = []
    for path in files:
        errors.extend(validate_file(path))
    if errors:
        for error in errors:
            print("ERROR:", error, file=sys.stderr)
        return 1
    print("KITTI result rows OK: %d file(s)" % len(files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
