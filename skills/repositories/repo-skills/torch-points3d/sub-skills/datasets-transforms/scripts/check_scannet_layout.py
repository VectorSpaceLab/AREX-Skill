#!/usr/bin/env python3
"""Check a ScanNet raw scene layout without downloading missing files.

This adapts the repository's ScanNet sanity checker but removes the automatic
re-download side effect. It only reads directory names and file existence.

Example:
  python sub-skills/datasets-transforms/scripts/check_scannet_layout.py --base-dir /data/scannet/raw/scans
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_SUFFIXES = [
    ".aggregation.json",
    ".txt",
    "_vh_clean_2.0.010000.segs.json",
    "_vh_clean_2.ply",
]

OPTIONAL_SUFFIXES = [
    ".sens",
    "_vh_clean.ply",
    "_vh_clean_2.labels.ply",
    "_vh_clean.segs.json",
]


def inspect_scene(scene_dir: Path) -> dict:
    scene_id = scene_dir.name
    required = {suffix: (scene_dir / f"{scene_id}{suffix}").is_file() for suffix in REQUIRED_SUFFIXES}
    optional = {suffix: (scene_dir / f"{scene_id}{suffix}").is_file() for suffix in OPTIONAL_SUFFIXES}
    return {
        "scene": scene_id,
        "complete": all(required.values()),
        "required": required,
        "optional": optional,
        "missing_required": [suffix for suffix, ok in required.items() if not ok],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ScanNet scene file presence without downloads.")
    parser.add_argument("--base-dir", required=True, type=Path, help="Directory containing ScanNet scene subdirectories.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    parser.add_argument("--allow-empty", action="store_true", help="Return success when base-dir has no scene directories.")
    args = parser.parse_args()

    if not args.base_dir.exists():
        raise SystemExit(f"base-dir does not exist: {args.base_dir}")
    if not args.base_dir.is_dir():
        raise SystemExit(f"base-dir is not a directory: {args.base_dir}")

    scenes = [p for p in sorted(args.base_dir.iterdir()) if p.is_dir()]
    reports = [inspect_scene(scene) for scene in scenes]
    incomplete = [r for r in reports if not r["complete"]]
    result = {
        "base_dir": str(args.base_dir),
        "scene_count": len(scenes),
        "complete_count": len(reports) - len(incomplete),
        "incomplete_count": len(incomplete),
        "scenes": reports,
    }

    ok = (len(scenes) > 0 or args.allow_empty) and not incomplete
    result["status"] = "passed" if ok else "failed"

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"ScanNet layout check: {result['status']}")
        print(f"scenes: {result['scene_count']}, complete: {result['complete_count']}, incomplete: {result['incomplete_count']}")
        if len(scenes) == 0:
            print("No scene directories found.")
        for report in incomplete:
            print(f"{report['scene']}: missing {', '.join(report['missing_required'])}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
