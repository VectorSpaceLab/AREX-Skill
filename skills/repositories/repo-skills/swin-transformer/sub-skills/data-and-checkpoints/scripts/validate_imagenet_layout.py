#!/usr/bin/env python3
"""Validate Swin-Transformer ImageNet-style data layouts without downloading data."""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def fail(msg: str) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return 1


def validate_folder(root: Path) -> int:
    for split in ["train", "val"]:
        split_dir = root / split
        if not split_dir.is_dir():
            return fail(f"missing {split}/ directory under {root}")
        classes = [p for p in split_dir.iterdir() if p.is_dir()]
        if not classes:
            return fail(f"{split}/ has no class subdirectories")
        sample = None
        for cls in classes[:20]:
            sample = next((p for p in cls.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES), None)
            if sample:
                break
        if sample is None:
            return fail(f"{split}/ class subdirectories contain no sample image files")
    print("folder layout looks usable for ImageFolder")
    return 0


def validate_map(path: Path) -> str | None:
    if not path.is_file():
        return f"missing map file: {path.name}"
    for idx, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2:
            return f"{path.name}:{idx}: expected '<relative-path> <label>'"
        try:
            int(parts[1])
        except ValueError:
            return f"{path.name}:{idx}: label is not an integer"
        return None
    return f"{path.name} is empty"


def validate_zip(root: Path) -> int:
    for name in ["train.zip", "val.zip"]:
        zp = root / name
        if not zp.is_file():
            return fail(f"missing {name}")
        try:
            with zipfile.ZipFile(zp) as zf:
                if not zf.namelist():
                    return fail(f"{name} is empty")
        except zipfile.BadZipFile:
            return fail(f"{name} is not a valid zip file")
    for name in ["train_map.txt", "val_map.txt"]:
        err = validate_map(root / name)
        if err:
            return fail(err)
    print("zip layout and first map entries look usable")
    return 0


def validate_22k(root: Path) -> int:
    candidates = ["ILSVRC2011fall_whole_map_train.txt", "ILSVRC2011fall_whole_map_val.txt"]
    for name in candidates:
        path = root / name
        if not path.is_file():
            return fail(f"missing {name}")
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            return fail(f"{name} is not valid JSON: {exc}")
        if not isinstance(data, list) or not data:
            return fail(f"{name} must be a non-empty JSON list")
        item = data[0]
        if not (isinstance(item, (list, tuple)) and len(item) >= 2):
            return fail(f"{name} first item should be [relative_path, label]")
    if not (root / "fall11_whole").exists():
        print("WARNING: fall11_whole/ image directory was not found next to map files")
    print("ImageNet-22K JSON maps look usable")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Swin-Transformer data layout schemas.")
    ap.add_argument("--mode", required=True, choices=["folder", "zip", "imagenet22k-json"])
    ap.add_argument("--data-path", type=Path, required=True)
    args = ap.parse_args()
    root = args.data_path.resolve()
    if not root.exists():
        return fail(f"data path does not exist: {root}")
    if args.mode == "folder":
        return validate_folder(root)
    if args.mode == "zip":
        return validate_zip(root)
    return validate_22k(root)


if __name__ == "__main__":
    raise SystemExit(main())
