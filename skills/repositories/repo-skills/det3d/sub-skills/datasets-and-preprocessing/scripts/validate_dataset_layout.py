#!/usr/bin/env python3
"""Non-mutating checks for documented Det3D dataset layouts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def checks(root: Path, dataset: str):
    if dataset == "kitti":
        expected = ["training", "testing"]
        optional = ["training/velodyne", "training/calib", "training/label_2", "testing/velodyne"]
    elif dataset == "nuscenes":
        expected = ["samples", "sweeps", "maps"]
        optional = []
    elif dataset == "lyft":
        expected = ["trainval", "test"]
        optional = ["trainval/data", "trainval/lidar", "test/data", "test/lidar"]
    else:
        raise SystemExit(f"unsupported dataset: {dataset}")
    return {
        "root": str(root),
        "dataset": dataset,
        "root_exists": root.is_dir(),
        "expected": {p: (root / p).is_dir() for p in expected},
        "optional": {p: (root / p).is_dir() for p in optional},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Det3D dataset directories without writing")
    parser.add_argument("root", type=Path)
    parser.add_argument("--dataset", choices=["kitti", "nuscenes", "lyft"], required=True)
    args = parser.parse_args()
    result = checks(args.root, args.dataset)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["root_exists"] and all(result["expected"].values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
