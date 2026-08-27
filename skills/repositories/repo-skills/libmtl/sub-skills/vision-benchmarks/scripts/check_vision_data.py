#!/usr/bin/env python3
"""Validate the preprocessed NYUv2 or Cityscapes directory layout."""

from __future__ import annotations

import argparse
from pathlib import Path


LAYOUTS = {
    "nyu": [
        "train/image",
        "train/label",
        "train/depth",
        "train/normal",
        "val/image",
        "val/label",
        "val/depth",
        "val/normal",
    ],
    "cityscapes": [
        "train/image",
        "train/label",
        "train/depth",
        "val/image",
        "val/label",
        "val/depth",
    ],
}


def _count_npy(path: Path) -> int:
    return sum(1 for _ in path.glob("*.npy"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Check a preprocessed vision dataset layout")
    parser.add_argument("dataset", choices=sorted(LAYOUTS), help="dataset family")
    parser.add_argument("root", type=Path, help="path to the preprocessed dataset root")
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    required = LAYOUTS[args.dataset]
    missing = []
    for rel in required:
        folder = root / rel
        if not folder.is_dir():
            missing.append(rel)
            continue
        count = _count_npy(folder)
        print(f"{rel}: {count} npy files")
        if count == 0:
            missing.append(rel)

    if missing:
        raise SystemExit(f"missing or empty folders: {', '.join(missing)}")

    print(f"vision data layout: ok ({args.dataset})")


if __name__ == "__main__":
    main()
