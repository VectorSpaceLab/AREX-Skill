#!/usr/bin/env python3
"""Offline validator for Ultralytics dataset YAML files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

DETECTION_LIKE_TASKS = {"detect", "segment", "pose", "obb", "semantic"}
IMAGE_SUFFIXES = {
    ".avif", ".bmp", ".dng", ".heic", ".heif", ".jp2", ".jpeg", ".jpeg2000", ".jpg", ".mpo",
    ".png", ".tif", ".tiff", ".webp",
}
DEPRECATED_SPLIT = {"validation": "val"}


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"PyYAML is required to read dataset YAML files: {exc}") from exc
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("dataset YAML must contain a mapping at the top level")
    return data


def names_count(names: Any) -> int | None:
    if isinstance(names, dict):
        return len(names)
    if isinstance(names, list):
        return len(names)
    return None


def normalize_split_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (str, Path)):
        return [str(value)]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def resolve_dataset_path(yaml_path: Path, data: dict[str, Any]) -> Path:
    raw_path = data.get("path")
    if raw_path in (None, ""):
        return yaml_path.parent
    path = Path(str(raw_path)).expanduser()
    return path if path.is_absolute() else (yaml_path.parent / path)


def split_target_exists(root: Path, target: str) -> bool:
    target_path = Path(target).expanduser()
    if not target_path.is_absolute():
        target_path = root / target_path
    return target_path.exists()


def check_classification(root: Path, check_paths: bool) -> list[str]:
    issues: list[str] = []
    train_dir = root / "train"
    if not train_dir.is_dir():
        issues.append("classification datasets should contain a train/ directory with one subdirectory per class")
    elif not [p for p in train_dir.iterdir() if p.is_dir()]:
        issues.append("classification train/ exists but has no class subdirectories")
    val_candidates = [root / "val", root / "validation", root / "valid"]
    if check_paths and not any(path.is_dir() for path in val_candidates):
        issues.append("classification validation split not found; expected val/, validation/, or valid/")
    if check_paths:
        image_count = sum(1 for item in root.rglob("*.*") if item.suffix.lower() in IMAGE_SUFFIXES)
        if image_count == 0:
            issues.append("no supported image files found under classification root")
    return issues


def validate(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    yaml_path = Path(args.yaml).expanduser()
    if not yaml_path.is_file():
        return [f"YAML file not found: {yaml_path}"], []

    data = load_yaml(yaml_path)
    issues: list[str] = []
    warnings: list[str] = []

    if args.task == "classify":
        root = Path(str(data.get("path") or yaml_path.parent)).expanduser()
        if not root.is_absolute():
            root = yaml_path.parent / root
        issues.extend(check_classification(root, args.check_paths))
        return issues, warnings

    for old_key, new_key in DEPRECATED_SPLIT.items():
        if old_key in data and new_key not in data:
            warnings.append(f"'{old_key}' is accepted by Ultralytics but should be renamed to '{new_key}'")

    for key in ("train", "val"):
        if key not in data:
            issues.append(f"missing required key '{key}'")

    if "names" not in data and "nc" not in data:
        issues.append("missing class definition: add 'names' or 'nc'")

    count = names_count(data.get("names"))
    if "names" in data and count is None:
        issues.append("'names' must be a list or an index-to-name mapping")
    if "names" in data and "nc" in data and count is not None:
        try:
            nc = int(data["nc"])
        except Exception:
            issues.append("'nc' must be an integer")
        else:
            if count != nc:
                issues.append(f"'names' length {count} does not match nc={nc}")

    if args.task == "pose":
        kpt_shape = data.get("kpt_shape")
        if not (isinstance(kpt_shape, list) and len(kpt_shape) == 2 and all(isinstance(x, int) for x in kpt_shape)):
            issues.append("pose datasets should define kpt_shape: [num_keypoints, 2_or_3]")
        if "flip_idx" in data and isinstance(kpt_shape, list) and len(data.get("flip_idx") or []) != kpt_shape[0]:
            issues.append("flip_idx length should match kpt_shape[0]")

    if args.task == "semantic" and "masks_dir" not in data:
        warnings.append("semantic datasets usually define masks_dir, such as masks")

    if "download" in data:
        warnings.append("download key present; review network or code execution risk before enabling autodownload")

    if args.check_paths:
        root = resolve_dataset_path(yaml_path, data)
        if data.get("path") and not root.exists():
            warnings.append(f"dataset path does not exist relative to YAML: {data.get('path')}")
        for key in ("train", "val", "test", "minival"):
            for value in normalize_split_values(data.get(key)):
                if value and not split_target_exists(root, value):
                    issues.append(f"split '{key}' path does not exist: {value}")

    return issues, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline lint an Ultralytics dataset YAML file.")
    parser.add_argument("yaml", help="Path to dataset YAML to inspect")
    parser.add_argument(
        "--task",
        choices=sorted(DETECTION_LIKE_TASKS | {"classify"}),
        default="detect",
        help="Dataset task schema to apply",
    )
    parser.add_argument("--check-paths", action="store_true", help="Also require referenced local split paths to exist")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    try:
        issues, warnings = validate(args)
    except Exception as exc:
        issues, warnings = [str(exc)], []

    if args.json:
        import json

        print(json.dumps({"ok": not issues, "issues": issues, "warnings": warnings}, indent=2))
    else:
        status = "PASS" if not issues else "FAIL"
        print(f"{status}: {args.yaml}")
        for warning in warnings:
            print(f"WARNING: {warning}")
        for issue in issues:
            print(f"ERROR: {issue}")
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
