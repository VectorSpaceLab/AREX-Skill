#!/usr/bin/env python3
"""Validate a NeRFCapture dataset directory for SplaTAM.

This helper reads transforms.json and checks referenced RGB/depth files. It does
not import OpenCV, open images, stream network frames, or mutate data.

Example:
  python sub-skills/capture/scripts/validate_nerfcapture_dataset.py \
    --dataset-dir experiments/iPhone_Captures/offline_demo --require-depth
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_GLOBAL_FIELDS = ["fl_x", "fl_y", "cx", "cy", "w", "h", "frames"]
REQUIRED_FRAME_FIELDS = ["transform_matrix", "file_path", "fl_x", "fl_y", "cx", "cy", "w", "h"]


def is_4x4_matrix(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 4
        and all(isinstance(row, list) and len(row) == 4 for row in value)
    )


def validate_manifest(dataset_dir: Path, require_depth: bool) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    manifest_path = dataset_dir / "transforms.json"
    summary: dict[str, Any] = {"dataset_dir": str(dataset_dir), "frames": 0, "warnings": warnings}

    if not dataset_dir.exists() or not dataset_dir.is_dir():
        return [f"dataset directory does not exist or is not a directory: {dataset_dir}"], summary
    if not manifest_path.exists():
        return [f"missing transforms.json: {manifest_path}"], summary

    try:
        manifest = json.loads(manifest_path.read_text())
    except Exception as exc:
        return [f"could not parse transforms.json: {type(exc).__name__}: {exc}"], summary

    for field in REQUIRED_GLOBAL_FIELDS:
        if field not in manifest:
            errors.append(f"missing global manifest field: {field}")

    frames = manifest.get("frames", [])
    if not isinstance(frames, list) or not frames:
        errors.append("manifest frames must be a non-empty list")
        frames = []
    summary["frames"] = len(frames)

    if "integer_depth_scale" not in manifest:
        warnings.append("global integer_depth_scale missing; depth interpretation may be ambiguous")

    rgb_count = 0
    depth_count = 0
    for idx, frame in enumerate(frames):
        if not isinstance(frame, dict):
            errors.append(f"frame {idx} is not an object")
            continue
        for field in REQUIRED_FRAME_FIELDS:
            if field not in frame:
                errors.append(f"frame {idx} missing field: {field}")
        if "transform_matrix" in frame and not is_4x4_matrix(frame["transform_matrix"]):
            errors.append(f"frame {idx} transform_matrix is not 4x4")

        file_path = frame.get("file_path")
        if isinstance(file_path, str):
            if (dataset_dir / file_path).exists():
                rgb_count += 1
            else:
                errors.append(f"frame {idx} missing RGB file: {file_path}")
        else:
            errors.append(f"frame {idx} file_path is not a string")

        depth_path = frame.get("depth_path")
        if isinstance(depth_path, str):
            if (dataset_dir / depth_path).exists():
                depth_count += 1
            else:
                errors.append(f"frame {idx} missing depth file: {depth_path}")
        elif require_depth:
            errors.append(f"frame {idx} missing depth_path")
        else:
            warnings.append(f"frame {idx} has no depth_path")

    summary["rgb_files"] = rgb_count
    summary["depth_files"] = depth_count
    summary["has_rgb_dir"] = (dataset_dir / "rgb").is_dir()
    summary["has_depth_dir"] = (dataset_dir / "depth").is_dir()

    if require_depth and depth_count != len(frames):
        errors.append(f"require-depth requested but only {depth_count}/{len(frames)} frames have depth files")

    return errors, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SplaTAM NeRFCapture dataset manifest and files.")
    parser.add_argument("--dataset-dir", required=True, type=Path, help="Captured scene directory containing transforms.json.")
    parser.add_argument("--require-depth", action="store_true", help="Fail when any frame lacks a depth_path or depth file.")
    parser.add_argument("--json", action="store_true", help="Print JSON summary.")
    args = parser.parse_args()

    errors, summary = validate_manifest(args.dataset_dir, args.require_depth)

    if args.json:
        print(json.dumps({"ok": not errors, "errors": errors, "summary": summary}, indent=2))
    else:
        print(f"Dataset directory: {args.dataset_dir}")
        print(f"Frames: {summary.get('frames', 0)}")
        print(f"RGB files: {summary.get('rgb_files', 0)}")
        print(f"Depth files: {summary.get('depth_files', 0)}")
        for warning in summary.get("warnings", []):
            print(f"Warning: {warning}")
        if errors:
            print("Errors:")
            for error in errors:
                print(f"  - {error}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
