#!/usr/bin/env python3
"""Check common OpenPCDet dataset layouts without reading large point clouds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

DATASET_EXPECTATIONS = {
    "kitti": ["training/velodyne", "training/label_2", "training/calib", "ImageSets"],
    "nuscenes": ["v1.0-trainval", "samples", "sweeps"],
    "waymo": ["raw_data"],
    "lyft": ["train_data", "v1.01-train"],
    "once": ["data", "ImageSets"],
    "pandaset": ["pandaset"],
    "custom": ["points", "ImageSets"],
    "argo2": ["sensor"],
}

INFO_PATTERNS = {
    "kitti": ["kitti_infos_train.pkl", "kitti_infos_val.pkl", "kitti_dbinfos_train.pkl"],
    "nuscenes": ["nuscenes_infos_*.pkl", "nuscenes_dbinfos_*.pkl"],
    "waymo": ["waymo_infos_*.pkl", "waymo_processed_data_*"],
    "lyft": ["lyft_infos_*.pkl", "lyft_dbinfos_*.pkl"],
    "once": ["once_infos_*.pkl", "once_dbinfos_*.pkl"],
    "pandaset": ["pandaset_infos_*.pkl", "pandaset_dbinfos_*.pkl"],
    "custom": ["custom_infos_*.pkl", "custom_dbinfos_*.pkl"],
    "argo2": ["argo2_infos_*.pkl"],
}


def exists_any(root: Path, patterns: Iterable[str]) -> list[str]:
    found: list[str] = []
    for pattern in patterns:
        if any(root.glob(pattern)):
            found.append(pattern)
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="Check OpenPCDet dataset layout")
    parser.add_argument("--dataset", required=True, choices=sorted(DATASET_EXPECTATIONS))
    parser.add_argument("--root", type=Path, required=True, help="Dataset root used by DATA_CONFIG.DATA_PATH")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = args.root
    required = DATASET_EXPECTATIONS[args.dataset]
    checks = []
    for rel in required:
        path = root / rel
        checks.append({"path": rel, "exists": path.exists(), "is_dir": path.is_dir()})

    info_patterns = INFO_PATTERNS.get(args.dataset, [])
    found_info = exists_any(root, info_patterns)
    report = {
        "dataset": args.dataset,
        "root": str(root),
        "required_layout": checks,
        "info_patterns_expected": info_patterns,
        "info_patterns_found": found_info,
        "missing_required": [x["path"] for x in checks if not x["exists"]],
        "missing_info_patterns": [p for p in info_patterns if p not in found_info],
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Dataset: {args.dataset}")
        print(f"Root: {root}")
        print("Required layout:")
        for check in checks:
            status = "OK" if check["exists"] else "MISSING"
            print(f"- {status:7} {check['path']}")
        if info_patterns:
            print("Info/database products:")
            for pattern in info_patterns:
                status = "FOUND" if pattern in found_info else "NOT FOUND"
                print(f"- {status:9} {pattern}")

    return 1 if report["missing_required"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
