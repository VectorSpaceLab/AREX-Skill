#!/usr/bin/env python3
"""Inspect a stitching verbose output directory and summarize missing stages.

This helper is safe and read-only. It looks for the files written by
`stitch_verbose(...)` / `stitch --verbose` and reports which stages are present,
which are missing, and which stage is most likely responsible when the
pipeline stopped early.

Example:
  python scripts/inspect_verbose_dir.py --verbose-dir ./stitch-debug
  python scripts/inspect_verbose_dir.py --verbose-dir ./stitch-debug --json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED_PREFIXES = [
    "00_stitcher.txt",
    "01_features_",
    "02_matches_",
    "03_matches_graph.txt",
    "04_warped_",
    "05_timelapse_",
    "06_estimated_mask_to_crop.jpg",
    "06_lir.jpg",
    "07_timelapse_cropped_",
    "08_seam_mask",
    "08_compensated",
    "09_result.jpg",
    "09_result_with_seam_lines.jpg",
    "09_result_with_seam_polygons.jpg",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verbose-dir",
        type=Path,
        required=True,
        help="Directory produced by stitch --verbose or stitcher.stitch_verbose(...).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON instead of human-readable output.",
    )
    return parser.parse_args()


def summarize(verbose_dir: Path) -> dict:
    verbose_dir = verbose_dir.resolve()
    if not verbose_dir.exists():
        return {
            "ok": False,
            "error": "directory does not exist",
            "verbose_dir": str(verbose_dir),
        }
    if not verbose_dir.is_dir():
        return {
            "ok": False,
            "error": "path is not a directory",
            "verbose_dir": str(verbose_dir),
        }

    names = sorted(child.name for child in verbose_dir.iterdir() if child.is_file())
    present = []
    missing = []
    for prefix in EXPECTED_PREFIXES:
        matches = [name for name in names if name == prefix or name.startswith(prefix)]
        if matches:
            present.append({"prefix": prefix, "matches": matches})
        else:
            missing.append(prefix)

    likely_missing_stage = None
    for prefix in EXPECTED_PREFIXES:
        if prefix in missing:
            likely_missing_stage = prefix
            break

    return {
        "ok": True,
        "verbose_dir": str(verbose_dir),
        "files": names,
        "present": present,
        "missing": missing,
        "likely_missing_stage": likely_missing_stage,
    }


def main() -> int:
    args = parse_args()
    report = summarize(args.verbose_dir)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        if not report.get("ok"):
            print(f"ERROR: {report['error']}: {report['verbose_dir']}")
            return 1
        print(f"Verbose directory: {report['verbose_dir']}")
        print("Present stages:")
        for entry in report["present"]:
            print(f"- {entry['prefix']}: {', '.join(entry['matches'])}")
        if report["missing"]:
            print("Missing stages:")
            for prefix in report["missing"]:
                print(f"- {prefix}")
            print(f"Likely next missing stage: {report['likely_missing_stage']}")
        else:
            print("All expected verbose stages are present.")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
