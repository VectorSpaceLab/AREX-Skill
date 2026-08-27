#!/usr/bin/env python3
"""Validate the ImageNet folder layout used by the benchmark branches.

This helper only checks the directory shape; it does not start training or
sampling.

Examples:
    python check_imagenet_layout.py --root /path/to/imagenet
"""

from __future__ import annotations

import argparse
from pathlib import Path


def count_class_dirs(split_dir: Path) -> int:
    return sum(1 for path in split_dir.iterdir() if path.is_dir())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--min-classes", type=int, default=1)
    args = parser.parse_args()

    root = args.root.resolve()
    print(f"root={root}")
    if not root.exists():
        print("FAIL: ImageNet root does not exist")
        return 1
    if not root.is_dir():
        print("FAIL: ImageNet root is not a directory")
        return 1

    ok = True
    for split in ["train", "val"]:
        split_dir = root / split
        print(f"[{split}] {split_dir}")
        if not split_dir.exists():
            print(f"FAIL: missing {split} directory")
            ok = False
            continue
        if not split_dir.is_dir():
            print(f"FAIL: {split} is not a directory")
            ok = False
            continue
        class_count = count_class_dirs(split_dir)
        print(f"class_dirs={class_count}")
        if class_count < args.min_classes:
            print(f"FAIL: expected at least {args.min_classes} class folders in {split}")
            ok = False

    if ok:
        print("Result: ImageNet layout looks valid.")
        return 0

    print("Result: ImageNet layout has problems.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
