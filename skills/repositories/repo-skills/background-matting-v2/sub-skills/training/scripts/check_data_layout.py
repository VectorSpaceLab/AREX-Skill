#!/usr/bin/env python3
"""Validate a BackgroundMattingV2 training data layout.

Safe by default:
- only reads directories or a data_path.py file
- does not download data or touch checkpoints
- reports placeholder paths and pair mismatches clearly

Two modes are supported:
1. `--data-path-py` to validate the repo's DATA_PATH mapping.
2. explicit `--fgr-root`, `--pha-root`, and optional `--background-root`.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Iterable


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate BackgroundMattingV2 data layout")
    p.add_argument("--data-path-py", help="Path to data_path.py to inspect")
    p.add_argument("--dataset-name", help="Validate only one dataset key from DATA_PATH")
    p.add_argument("--fgr-root", help="Foreground image root for explicit pair mode")
    p.add_argument("--pha-root", help="Alpha image root for explicit pair mode")
    p.add_argument("--background-root", help="Background image root for explicit pair mode")
    return p.parse_args()


def load_data_path_module(path: Path):
    spec = importlib.util.spec_from_file_location("background_matting_v2_data_path", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load data_path.py from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def image_stems(root: Path) -> set[str]:
    stems: set[str] = set()
    for file in root.rglob("*"):
        if file.is_file() and file.suffix.lower() in IMAGE_SUFFIXES:
            stems.add(str(file.relative_to(root).with_suffix("")))
    return stems


def check_dir(root: Path, label: str) -> list[str]:
    errors: list[str] = []
    if not root.exists():
        errors.append(f"{label} missing: {root}")
        return errors
    if not root.is_dir():
        errors.append(f"{label} is not a directory: {root}")
        return errors
    if not image_stems(root):
        errors.append(f"{label} has no jpg/png images: {root}")
    return errors


def compare_pair(fgr_root: Path, pha_root: Path, label: str) -> list[str]:
    errors = check_dir(fgr_root, f"{label}.fgr") + check_dir(pha_root, f"{label}.pha")
    if errors:
        return errors
    fgr_stems = image_stems(fgr_root)
    pha_stems = image_stems(pha_root)
    if fgr_stems != pha_stems:
        missing_fgr = sorted(pha_stems - fgr_stems)[:5]
        missing_pha = sorted(fgr_stems - pha_stems)[:5]
        if missing_fgr:
            errors.append(f"{label}: missing foreground matches for {missing_fgr}")
        if missing_pha:
            errors.append(f"{label}: missing alpha matches for {missing_pha}")
        if len(fgr_stems) != len(pha_stems):
            errors.append(f"{label}: foreground/alpha counts differ ({len(fgr_stems)} vs {len(pha_stems)})")
    return errors


def validate_data_path(data: dict, dataset_name: str | None) -> list[str]:
    errors: list[str] = []
    keys = [dataset_name] if dataset_name else list(data.keys())
    for key in keys:
        if key not in data:
            errors.append(f"unknown dataset key: {key}")
            continue
        entry = data[key]
        if key == "backgrounds":
            for split in ["train", "valid"]:
                value = entry.get(split)
                if not isinstance(value, str):
                    errors.append(f"backgrounds.{split} is not a string path")
                    continue
                if value.startswith("PATH_TO_"):
                    errors.append(f"backgrounds.{split} still uses placeholder: {value}")
                    continue
                errors.extend(check_dir(Path(value), f"backgrounds.{split}"))
            continue

        for split in ["train", "valid"]:
            split_entry = entry.get(split, {})
            for kind in ["fgr", "pha"]:
                value = split_entry.get(kind)
                if not isinstance(value, str):
                    errors.append(f"{key}.{split}.{kind} is not a string path")
                    continue
                if value.startswith("PATH_TO_"):
                    errors.append(f"{key}.{split}.{kind} still uses placeholder: {value}")
            if isinstance(split_entry.get("fgr"), str) and isinstance(split_entry.get("pha"), str):
                fgr = Path(split_entry["fgr"])
                pha = Path(split_entry["pha"])
                errors.extend(compare_pair(fgr, pha, f"{key}.{split}"))
    return errors


def main() -> int:
    args = parse_args()
    errors: list[str] = []

    if args.data_path_py:
        module_path = Path(args.data_path_py).resolve()
        if not module_path.exists():
            print(f"data-path file missing: {module_path}", file=sys.stderr)
            return 2
        module = load_data_path_module(module_path)
        data = getattr(module, "DATA_PATH", None)
        if not isinstance(data, dict):
            print("DATA_PATH is missing or not a dict", file=sys.stderr)
            return 3
        errors.extend(validate_data_path(data, args.dataset_name))
    else:
        if not args.fgr_root or not args.pha_root:
            print("explicit mode requires --fgr-root and --pha-root", file=sys.stderr)
            return 4
        errors.extend(compare_pair(Path(args.fgr_root).resolve(), Path(args.pha_root).resolve(), "explicit-pair"))
        if args.background_root:
            errors.extend(check_dir(Path(args.background_root).resolve(), "background-root"))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("data layout looks consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
