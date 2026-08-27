#!/usr/bin/env python3
"""Validate AB3DMOT comma-separated detection input files.

The script is self-contained: it does not import AB3DMOT and it does not need
images, calibration, labels, or nuScenes metadata. It checks the text files that
AB3DMOT expects under data/<dataset>/detection/<det>_<category>_<split>/.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

KITTI_IDS: Dict[int, str] = {1: "Pedestrian", 2: "Car", 3: "Cyclist"}
NUSCENES_IDS: Dict[int, str] = {
    1: "Pedestrian",
    2: "Car",
    3: "Bicycle",
    4: "Motorcycle",
    5: "Bus",
    6: "Trailer",
    7: "Truck",
    8: "Construction_vehicle",
    9: "Barrier",
    10: "Traffic_cone",
}
COLUMNS = [
    "frame",
    "type_id",
    "x1",
    "y1",
    "x2",
    "y2",
    "score",
    "h",
    "w",
    "l",
    "x",
    "y",
    "z",
    "ry",
    "alpha",
]


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate AB3DMOT 15-column comma-separated detection text files."
    )
    parser.add_argument("files", nargs="+", type=Path, help="Detection .txt files to validate")
    parser.add_argument(
        "--dataset",
        choices=["KITTI", "nuScenes"],
        default=None,
        help="When set, validate type_id against the dataset category map.",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=20,
        help="Maximum detailed errors to print before summarizing.",
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow empty files. By default an empty file is an error.",
    )
    parser.add_argument(
        "--strict-2d-box",
        action="store_true",
        help="Treat x2 < x1 or y2 < y1 as errors instead of warnings.",
    )
    return parser.parse_args(argv)


def category_map(dataset: Optional[str]) -> Optional[Dict[int, str]]:
    if dataset == "KITTI":
        return KITTI_IDS
    if dataset == "nuScenes":
        return NUSCENES_IDS
    return None


def finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"not finite: {value!r}")
    return parsed


def validate_row(
    path: Path,
    line_no: int,
    row: List[str],
    ids: Optional[Dict[int, str]],
    strict_2d_box: bool,
) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    label = f"{path}:{line_no}"

    if len(row) != 15:
        return [f"{label}: expected 15 comma-separated columns, got {len(row)}"], warnings

    try:
        values = [finite_float(cell.strip()) for cell in row]
    except ValueError as exc:
        return [f"{label}: non-numeric or non-finite value ({exc})"], warnings

    frame_raw, type_raw = values[0], values[1]
    frame, type_id = int(frame_raw), int(type_raw)
    if frame != frame_raw or frame < 0:
        errors.append(f"{label}: frame must be a nonnegative integer, got {frame_raw!r}")
    if type_id != type_raw:
        errors.append(f"{label}: type_id must be an integer, got {type_raw!r}")
    if ids is not None and type_id not in ids:
        errors.append(f"{label}: type_id {type_id} is not valid for selected dataset")

    x1, y1, x2, y2 = values[2], values[3], values[4], values[5]
    if x2 < x1 or y2 < y1:
        msg = f"{label}: suspicious 2D box order x1,y1,x2,y2={x1},{y1},{x2},{y2}"
        if strict_2d_box:
            errors.append(msg)
        else:
            warnings.append(msg)

    h, w, length = values[7], values[8], values[9]
    for name, val in [("h", h), ("w", w), ("l", length)]:
        if val <= 0:
            errors.append(f"{label}: 3D dimension {name} must be positive, got {val}")

    return errors, warnings


def validate_file(path: Path, args: argparse.Namespace) -> Tuple[int, int, int]:
    ids = category_map(args.dataset)
    errors: List[str] = []
    warnings: List[str] = []
    rows = 0
    type_counts: Dict[int, int] = {}
    min_frame: Optional[int] = None
    max_frame: Optional[int] = None

    if not path.exists():
        print(f"ERROR {path}: file does not exist", file=sys.stderr)
        return 0, 1, 0
    if not path.is_file():
        print(f"ERROR {path}: not a regular file", file=sys.stderr)
        return 0, 1, 0

    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        for line_no, row in enumerate(reader, start=1):
            if not row or all(not cell.strip() for cell in row):
                continue
            rows += 1
            row_errors, row_warnings = validate_row(path, line_no, row, ids, args.strict_2d_box)
            errors.extend(row_errors)
            warnings.extend(row_warnings)
            if not row_errors and len(row) == 15:
                frame = int(float(row[0]))
                type_id = int(float(row[1]))
                type_counts[type_id] = type_counts.get(type_id, 0) + 1
                min_frame = frame if min_frame is None else min(min_frame, frame)
                max_frame = frame if max_frame is None else max(max_frame, frame)

    if rows == 0 and not args.allow_empty:
        errors.append(f"{path}: no detection rows found")

    for message in warnings[: args.max_errors]:
        print(f"WARNING {message}", file=sys.stderr)
    for message in errors[: args.max_errors]:
        print(f"ERROR {message}", file=sys.stderr)
    if len(errors) > args.max_errors:
        print(f"ERROR {path}: {len(errors) - args.max_errors} additional errors omitted", file=sys.stderr)
    if len(warnings) > args.max_errors:
        print(f"WARNING {path}: {len(warnings) - args.max_errors} additional warnings omitted", file=sys.stderr)

    if errors:
        print(f"FAIL {path}: rows={rows}, errors={len(errors)}, warnings={len(warnings)}")
    else:
        categories = []
        for type_id, count in sorted(type_counts.items()):
            if ids and type_id in ids:
                categories.append(f"{type_id}:{ids[type_id]}={count}")
            else:
                categories.append(f"{type_id}={count}")
        frame_span = "none" if min_frame is None else f"{min_frame}..{max_frame}"
        print(
            f"OK {path}: rows={rows}, frames={frame_span}, "
            f"categories={','.join(categories) if categories else 'none'}, warnings={len(warnings)}"
        )
    return rows, len(errors), len(warnings)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    total_rows = total_errors = total_warnings = 0
    for path in args.files:
        rows, errors, warnings = validate_file(path, args)
        total_rows += rows
        total_errors += errors
        total_warnings += warnings
    print(f"SUMMARY files={len(args.files)} rows={total_rows} errors={total_errors} warnings={total_warnings}")
    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
