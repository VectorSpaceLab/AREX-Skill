#!/usr/bin/env python3
"""Validate that a CULane or TuSimple dataset root looks ready for this repo.

The helper only checks paths and file names; it does not download or modify
anything.

Example:
    python validate_dataset_layout.py --dataset Tusimple --root /path/to/TuSimple
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

CULANE_REQUIRED = [
    "driver_100_30frame",
    "driver_161_90frame",
    "driver_182_30frame",
    "driver_193_90frame",
    "driver_23_30frame",
    "driver_37_30frame",
    "laneseg_label_w16",
    "list",
]

CULANE_LISTS = [
    "list/train_gt.txt",
    "list/test.txt",
    "list/test_split/test0_normal.txt",
    "list/test_split/test1_crowd.txt",
    "list/test_split/test2_hlight.txt",
    "list/test_split/test3_shadow.txt",
    "list/test_split/test4_noline.txt",
    "list/test_split/test5_arrow.txt",
    "list/test_split/test6_curve.txt",
    "list/test_split/test7_cross.txt",
    "list/test_split/test8_night.txt",
]

TUSIMPLE_REQUIRED = [
    "clips",
    "label_data_0313.json",
    "label_data_0531.json",
    "label_data_0601.json",
    "test_tasks_0627.json",
    "test_label.json",
    "readme.md",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the dataset layout used by Ultra-Fast-Lane-Detection.")
    parser.add_argument("--dataset", required=True, choices=["CULane", "Tusimple"], help="Dataset family to validate")
    parser.add_argument("--root", required=True, help="Dataset root path")
    return parser.parse_args()


def missing_paths(root: Path, names: Iterable[str]) -> List[str]:
    missing = []
    for name in names:
        if not (root / name).exists():
            missing.append(name)
    return missing


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        print(f"missing root: {root}")
        return 2

    if args.dataset == "CULane":
        missing = missing_paths(root, CULANE_REQUIRED + CULANE_LISTS)
    else:
        missing = missing_paths(root, TUSIMPLE_REQUIRED)

    if missing:
        print("missing:")
        for item in missing:
            print(f"- {item}")
        return 1

    print(f"{args.dataset} layout looks ready at {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
