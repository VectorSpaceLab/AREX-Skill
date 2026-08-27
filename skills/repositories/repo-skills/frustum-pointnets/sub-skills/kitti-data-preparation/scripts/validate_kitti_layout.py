#!/usr/bin/env python3
"""Validate KITTI Object Detection layout and optional split/detector files."""
import argparse
import math
from pathlib import Path
import sys


def read_ids(path):
    ids = []
    for number, raw in enumerate(Path(path).read_text().splitlines(), 1):
        text = raw.strip()
        if not text:
            continue
        try:
            value = int(text)
        except ValueError:
            raise ValueError("%s:%d is not an integer frame id" % (path, number))
        if value < 0:
            raise ValueError("%s:%d has a negative frame id" % (path, number))
        ids.append(value)
    if not ids:
        raise ValueError("index file contains no frame ids")
    return ids


def validate_detector(path):
    errors = []
    rows = 0
    for number, raw in enumerate(Path(path).read_text().splitlines(), 1):
        text = raw.strip()
        if not text:
            continue
        rows += 1
        parts = text.split()
        if len(parts) != 7:
            errors.append("line %d: expected 7 columns, got %d" % (number, len(parts)))
            continue
        try:
            frame = int(Path(parts[0]).stem)
            type_id = int(parts[1])
            values = [float(v) for v in parts[2:]]
        except ValueError as exc:
            errors.append("line %d: invalid numeric/image id (%s)" % (number, exc))
            continue
        if frame < 0 or type_id not in (1, 2, 3):
            errors.append("line %d: frame must be nonnegative and type_id in 1,2,3" % number)
        if not all(math.isfinite(v) for v in values):
            errors.append("line %d: non-finite score or coordinate" % number)
        _, xmin, ymin, xmax, ymax = values
        if xmax <= xmin or ymax <= ymin:
            errors.append("line %d: reversed or empty box" % number)
    if rows == 0:
        errors.append("detector file contains no rows")
    return rows, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", required=True, help="KITTI object root containing training/testing")
    parser.add_argument("--index-file", help="one integer frame id per line")
    parser.add_argument("--detector-file", help="RGB detector rows: image type score xmin ymin xmax ymax")
    parser.add_argument("--split", choices=("training", "testing"), default="training")
    parser.add_argument("--require-labels", action="store_true", help="require label_2 files (training only)")
    parser.add_argument("--check-complete", action="store_true", help="check every id rather than the first 25")
    args = parser.parse_args()

    root = Path(args.dataset_root)
    split = root / args.split
    required_dirs = [split / "calib", split / "image_2", split / "velodyne"]
    if args.require_labels:
        if args.split != "training":
            parser.error("--require-labels is only valid for the training split")
        required_dirs.append(split / "label_2")
    errors = ["missing directory: %s" % p for p in required_dirs if not p.is_dir()]

    ids = None
    if args.index_file:
        try:
            ids = read_ids(args.index_file)
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
    if ids and not errors:
        selected = ids if args.check_complete else ids[:25]
        suffixes = [("calib", ".txt"), ("image_2", ".png"), ("velodyne", ".bin")]
        if args.require_labels:
            suffixes.append(("label_2", ".txt"))
        for value in selected:
            stem = "%06d" % value
            for folder, suffix in suffixes:
                path = split / folder / (stem + suffix)
                if not path.is_file():
                    errors.append("missing frame file: %s" % path)

    detector_rows = 0
    if args.detector_file:
        try:
            detector_rows, detector_errors = validate_detector(args.detector_file)
            errors.extend(detector_errors)
        except OSError as exc:
            errors.append(str(exc))

    if errors:
        for error in errors:
            print("ERROR:", error, file=sys.stderr)
        return 1
    print("KITTI layout OK; checked %d id(s); detector rows %d" %
          ((len(ids) if args.check_complete else min(len(ids or []), 25)), detector_rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
