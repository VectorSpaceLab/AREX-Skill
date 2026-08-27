#!/usr/bin/env python3
"""Validate a small Open3D-ML-style custom dataset layout.

The checker is intentionally conservative: it inspects files and array shapes
only. It does not download data, preprocess full datasets, build caches, import
Open3D, or run training.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_shape(path: Path):
    try:
        import numpy as np
    except Exception as exc:
        return None, f"NumPy is required to inspect .npy files: {type(exc).__name__}: {exc}"
    try:
        arr = np.load(path, mmap_mode="r")
        return tuple(int(x) for x in arr.shape), None
    except Exception as exc:
        return None, f"failed to load {path.name}: {type(exc).__name__}: {exc}"


def inspect_split(root: Path, split_name: str, require_labels: bool, min_columns: int, max_files: int):
    split_dir = root / split_name
    result = {"split": split_name, "path": str(split_dir), "exists": split_dir.is_dir(), "files_checked": [], "errors": [], "warnings": []}
    if not split_dir.is_dir():
        result["errors"].append(f"missing split directory: {split_name}")
        return result
    files = sorted(split_dir.glob("*.npy"))
    if not files:
        result["errors"].append(f"no .npy files found in split: {split_name}")
        return result
    for file_path in files[:max_files]:
        shape, error = load_shape(file_path)
        entry = {"file": file_path.name, "shape": shape}
        if error:
            result["errors"].append(error)
            entry["error"] = error
        elif len(shape) != 2:
            result["errors"].append(f"{file_path.name}: expected 2D array, got shape {shape}")
        else:
            cols = shape[1]
            needed = max(min_columns, 4 if require_labels else 3)
            if cols < needed:
                result["errors"].append(f"{file_path.name}: expected at least {needed} columns, got {cols}")
            if require_labels and cols == 3:
                result["errors"].append(f"{file_path.name}: labels required but no label column present")
            if cols == 4 and require_labels:
                result["warnings"].append(f"{file_path.name}: has XYZ + label but no extra feature columns")
        result["files_checked"].append(entry)
    if len(files) > max_files:
        result["warnings"].append(f"only checked first {max_files} of {len(files)} .npy files")
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check an Open3D-ML Custom3D-style dataset layout.")
    parser.add_argument("root", help="Dataset root containing split subdirectories such as train, val, and test.")
    parser.add_argument("--splits", nargs="+", default=["train", "val", "test"], help="Split directories to inspect.")
    parser.add_argument("--label-splits", nargs="+", default=["train", "val"], help="Splits that must include a label column after XYZ.")
    parser.add_argument("--min-columns", type=int, default=3, help="Minimum columns per point array. Custom3D expects XYZ plus optional label/features.")
    parser.add_argument("--max-files", type=int, default=3, help="Maximum .npy files to inspect per split.")
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    args = parser.parse_args(argv)

    root = Path(args.root)
    report = {"root": str(root), "exists": root.is_dir(), "splits": [], "errors": [], "warnings": []}
    if not root.is_dir():
        report["errors"].append("dataset root does not exist or is not a directory")
    else:
        label_splits = set(args.label_splits)
        for split in args.splits:
            result = inspect_split(root, split, split in label_splits, args.min_columns, args.max_files)
            report["splits"].append(result)
            report["errors"].extend(result["errors"])
            report["warnings"].extend(result["warnings"])

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
        if report["errors"]:
            print("\nLayout check failed. Fix errors before constructing an Open3D-ML dataset.", file=sys.stderr)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
