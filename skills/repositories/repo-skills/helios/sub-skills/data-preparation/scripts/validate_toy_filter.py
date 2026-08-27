#!/usr/bin/env python3
"""Validate Helios toy-style video metadata JSON.

The check is read-only. Use it before launching GPU-heavy data extraction jobs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_KEYS = {"cut", "crop", "fps", "num_frames", "resolution", "cap", "path"}


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_item(item: dict[str, Any], index: int, video_root: Path | None) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_KEYS - set(item)
    if missing:
        errors.append(f"item {index}: missing keys {sorted(missing)}")
        return errors

    if not (isinstance(item["cut"], list) and len(item["cut"]) == 2 and all(isinstance(x, int) for x in item["cut"])):
        errors.append(f"item {index}: cut must be a list of two integers")
    if not (isinstance(item["crop"], list) and len(item["crop"]) == 4 and all(isinstance(x, int) for x in item["crop"])):
        errors.append(f"item {index}: crop must be a list of four integers")
    if not is_number(item["fps"]):
        errors.append(f"item {index}: fps must be numeric")
    if not (isinstance(item["num_frames"], int) and item["num_frames"] > 0):
        errors.append(f"item {index}: num_frames must be a positive integer")

    resolution = item["resolution"]
    if not isinstance(resolution, dict):
        errors.append(f"item {index}: resolution must be an object")
    else:
        for key in ["height", "width"]:
            if not (isinstance(resolution.get(key), int) and resolution[key] > 0):
                errors.append(f"item {index}: resolution.{key} must be a positive integer")

    cap = item["cap"]
    if not (isinstance(cap, list) and cap and all(isinstance(x, str) and x.strip() for x in cap)):
        errors.append(f"item {index}: cap must be a non-empty list of non-empty strings")

    rel_path = item["path"]
    if not (isinstance(rel_path, str) and rel_path.strip()):
        errors.append(f"item {index}: path must be a non-empty string")
    elif video_root is not None:
        candidate = video_root / rel_path
        if not candidate.exists():
            errors.append(f"item {index}: video file not found: {candidate}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Helios toy-style metadata JSON")
    parser.add_argument("json_file", type=Path, help="Metadata JSON file")
    parser.add_argument(
        "--video-root",
        type=Path,
        default=None,
        help="Optional directory used to verify relative video paths",
    )
    args = parser.parse_args()

    data = json.loads(args.json_file.read_text())
    if not isinstance(data, list):
        print("metadata root must be a list")
        return 1

    errors: list[str] = []
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"item {index}: expected object, got {type(item).__name__}")
            continue
        errors.extend(validate_item(item, index, args.video_root))

    if errors:
        print("Metadata validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print(f"Metadata validation OK: {len(data)} items")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
