#!/usr/bin/env python3
"""Validate a Nerfstudio-style dataset without modifying it.

Examples:
    python validate_nerfstudio_dataset.py /path/to/dataset
    python validate_nerfstudio_dataset.py /path/to/dataset/transforms.json --strict-splits
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".exr"}


def _as_path(base: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else base / p


def _is_matrix_4x4(value: Any) -> bool:
    if not isinstance(value, list) or len(value) != 4:
        return False
    for row in value:
        if not isinstance(row, list) or len(row) != 4:
            return False
        if not all(isinstance(x, (int, float)) for x in row):
            return False
    return True


def _resolve_existing(base: Path, value: str) -> Path | None:
    candidate = _as_path(base, value)
    if candidate.exists():
        return candidate
    if candidate.suffix:
        return None
    for suffix in IMAGE_SUFFIXES:
        maybe = candidate.with_suffix(suffix)
        if maybe.exists():
            return maybe
    return None


def _transforms_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    explicit = path / "transforms.json"
    if explicit.exists():
        return [explicit]
    return sorted(path.glob("transforms*.json"))


def validate_one(transforms: Path, strict_splits: bool, allow_missing_files: bool) -> tuple[list[str], list[str]]:
    base = transforms.parent
    failures: list[str] = []
    warnings: list[str] = []

    try:
        data = json.loads(transforms.read_text(encoding="utf8"))
    except Exception as exc:
        return [f"{transforms}: invalid JSON: {exc}"], []

    frames = data.get("frames")
    if not isinstance(frames, list) or not frames:
        failures.append("`frames` must be a non-empty list")
        frames = []

    frame_paths: set[str] = set()
    per_frame_intrinsic_keys = {"fl_x", "fl_y", "cx", "cy", "w", "h", "k1", "k2", "k3", "k4", "p1", "p2"}
    seen_per_frame = {key: 0 for key in per_frame_intrinsic_keys}
    mask_count = 0
    depth_count = 0

    for idx, frame in enumerate(frames):
        if not isinstance(frame, dict):
            failures.append(f"{transforms}: frame {idx}: not an object")
            continue
        rel = frame.get("file_path")
        if not isinstance(rel, str) or not rel:
            failures.append(f"{transforms}: frame {idx}: missing string file_path")
        else:
            frame_paths.add(rel)
            image_path = _resolve_existing(base, rel)
            if image_path is None:
                msg = f"{transforms}: frame {idx}: image file not found: {rel}"
                (warnings if allow_missing_files else failures).append(msg)
            elif image_path.suffix.lower() and image_path.suffix.lower() not in IMAGE_SUFFIXES:
                warnings.append(f"{transforms}: frame {idx}: unusual image suffix {image_path.suffix}")
        if not _is_matrix_4x4(frame.get("transform_matrix")):
            failures.append(f"{transforms}: frame {idx}: transform_matrix must be numeric 4x4")
        for key in per_frame_intrinsic_keys:
            if key in frame:
                seen_per_frame[key] += 1
        for key in ["depth_file_path", "mask_path"]:
            if key in frame:
                rel_aux = frame[key]
                if not isinstance(rel_aux, str) or not rel_aux:
                    failures.append(f"{transforms}: frame {idx}: {key} must be a non-empty string")
                    continue
                if key == "depth_file_path":
                    depth_count += 1
                else:
                    mask_count += 1
                aux_path = _resolve_existing(base, rel_aux)
                if aux_path is None:
                    msg = f"{transforms}: frame {idx}: {key} file not found: {rel_aux}"
                    (warnings if allow_missing_files else failures).append(msg)

    for key, count in seen_per_frame.items():
        if 0 < count < len(frames):
            failures.append(f"{transforms}: per-frame intrinsic {key!r} is present in {count}/{len(frames)} frames; use consistently")

    if 0 < mask_count < len(frames):
        warnings.append(f"{transforms}: mask_path appears in {mask_count}/{len(frames)} frames; masks are usually all-or-none")
    if 0 < depth_count < len(frames):
        warnings.append(f"{transforms}: depth_file_path appears in {depth_count}/{len(frames)} frames; verify the selected method supports mixed depth")

    for split_key in ["train_filenames", "val_filenames", "test_filenames"]:
        if split_key not in data:
            continue
        values = data[split_key]
        if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
            failures.append(f"{transforms}: {split_key} must be a list of strings")
            continue
        missing = [v for v in values if v not in frame_paths]
        if missing:
            msg = f"{transforms}: {split_key} contains filenames not present in frames: {missing[:5]}"
            (failures if strict_splits else warnings).append(msg)

    print(f"transforms: {transforms}")
    print(f"frames: {len(frames)}")
    print(f"depth frames: {depth_count}; mask frames: {mask_count}")
    return failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Nerfstudio transforms*.json paths and schema.")
    parser.add_argument("path", type=Path, help="Dataset directory or transforms JSON file.")
    parser.add_argument("--strict-splits", action="store_true", help="Require split lists to reference existing frames.")
    parser.add_argument("--allow-missing-files", action="store_true", help="Report missing files as warnings instead of failures.")
    args = parser.parse_args()

    transforms_files = _transforms_files(args.path)
    if not transforms_files:
        print(f"No transforms JSON found under {args.path}", file=sys.stderr)
        return 1

    all_failures: list[str] = []
    all_warnings: list[str] = []
    for transforms in transforms_files:
        failures, warnings = validate_one(transforms, args.strict_splits, args.allow_missing_files)
        all_failures.extend(failures)
        all_warnings.extend(warnings)

    if all_warnings:
        print("Warnings:")
        for warning in all_warnings:
            print(f"- {warning}")
    if all_failures:
        print("Failures:", file=sys.stderr)
        for failure in all_failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("Dataset validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
