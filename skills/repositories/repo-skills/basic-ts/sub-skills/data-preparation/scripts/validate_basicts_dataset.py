#!/usr/bin/env python3
"""Validate a BasicTS dataset folder without mutating it.

This helper checks the common BasicTS file layouts for forecasting, imputation,
classification, and BLAST data. It is read-only by default and can be run from
any working directory.

Examples:
    python scripts/validate_basicts_dataset.py --root /path/to/dataset --format auto
    python scripts/validate_basicts_dataset.py --root /path/to/UEA/ArticularyWordRecognition_mini --format classification
    python scripts/validate_basicts_dataset.py --root /path/to/BLAST --format blast
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class CheckResult:
    ok: bool
    messages: list[str]


def load_npy(path: Path):
    return np.load(path, mmap_mode="r")


def read_meta(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def add_message(messages: list[str], text: str) -> None:
    messages.append(text)


def validate_split_layout(root: Path, expect_timestamps: bool) -> CheckResult:
    messages: list[str] = []
    ok = True
    required = ["train_data.npy", "val_data.npy", "test_data.npy"]
    timestamp_files = ["train_timestamps.npy", "val_timestamps.npy", "test_timestamps.npy"]

    for name in required:
        file_path = root / name
        if not file_path.exists():
            ok = False
            add_message(messages, f"missing file: {name}")
            continue
        arr = load_npy(file_path)
        add_message(messages, f"{name}: shape={tuple(arr.shape)} dtype={arr.dtype}")
        if arr.shape[0] == 0:
            ok = False
            add_message(messages, f"{name}: empty first dimension")

    if expect_timestamps:
        for name in timestamp_files:
            file_path = root / name
            if not file_path.exists():
                ok = False
                add_message(messages, f"missing timestamp file: {name}")
                continue
            arr = load_npy(file_path)
            add_message(messages, f"{name}: shape={tuple(arr.shape)} dtype={arr.dtype}")
            if arr.shape[0] == 0:
                ok = False
                add_message(messages, f"{name}: empty first dimension")

    meta = read_meta(root / "meta.json")
    if meta is not None:
        add_message(messages, f"meta.json keys: {sorted(meta.keys())}")
        if "shape" in meta:
            add_message(messages, f"meta.shape={meta['shape']}")
        if "timestamps_shape" in meta:
            add_message(messages, f"meta.timestamps_shape={meta['timestamps_shape']}")
        if expect_timestamps and "timestamps_shape" not in meta:
            add_message(messages, "meta.json does not record timestamps_shape")

    return CheckResult(ok=ok, messages=messages)


def validate_classification_layout(root: Path) -> CheckResult:
    messages: list[str] = []
    ok = True
    required = ["train_inputs.npy", "train_labels.npy", "test_inputs.npy", "test_labels.npy"]
    for name in required:
        file_path = root / name
        if not file_path.exists():
            ok = False
            add_message(messages, f"missing file: {name}")
            continue
        arr = load_npy(file_path)
        add_message(messages, f"{name}: shape={tuple(arr.shape)} dtype={arr.dtype}")
        if arr.shape[0] == 0:
            ok = False
            add_message(messages, f"{name}: empty first dimension")

    try:
        train_inputs = load_npy(root / "train_inputs.npy")
        train_labels = load_npy(root / "train_labels.npy")
        test_inputs = load_npy(root / "test_inputs.npy")
        test_labels = load_npy(root / "test_labels.npy")
        if train_inputs.shape[0] != train_labels.shape[0]:
            ok = False
            add_message(messages, "train input/label count mismatch")
        if test_inputs.shape[0] != test_labels.shape[0]:
            ok = False
            add_message(messages, "test input/label count mismatch")
    except FileNotFoundError:
        pass

    meta = read_meta(root / "meta.json") or read_meta(root / "desc.json")
    if meta is not None:
        add_message(messages, f"metadata keys: {sorted(meta.keys())}")
        if "num_classes" in meta:
            add_message(messages, f"num_classes={meta['num_classes']}")
        if "shape" in meta:
            add_message(messages, f"shape={meta['shape']}")

    return CheckResult(ok=ok, messages=messages)


def validate_blast_layout(root: Path) -> CheckResult:
    messages: list[str] = []
    ok = True
    for mode in ["train", "val", "test"]:
        mode_dir = root / mode
        shape_file = mode_dir / "shape.npy"
        data_file = mode_dir / "data.dat"
        if not shape_file.exists():
            ok = False
            add_message(messages, f"missing file: {mode}/shape.npy")
            continue
        if not data_file.exists():
            ok = False
            add_message(messages, f"missing file: {mode}/data.dat")
            continue

        shape = tuple(np.load(shape_file))
        expected_bytes = int(np.prod(shape)) * np.dtype(np.float32).itemsize
        actual_bytes = data_file.stat().st_size
        add_message(messages, f"{mode}: shape={shape} expected_bytes={expected_bytes} actual_bytes={actual_bytes}")
        if actual_bytes != expected_bytes:
            ok = False
            add_message(messages, f"{mode}: size mismatch between shape.npy and data.dat")

    return CheckResult(ok=ok, messages=messages)


def detect_format(root: Path) -> str:
    if (root / "train_inputs.npy").exists() or (root / "train_labels.npy").exists():
        return "classification"
    if (root / "train").is_dir() and ((root / "train" / "shape.npy").exists() or (root / "train" / "data.dat").exists()):
        return "blast"
    return "split"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a BasicTS dataset folder.")
    parser.add_argument("--root", required=True, type=Path, help="Dataset root to validate.")
    parser.add_argument(
        "--format",
        default="auto",
        choices=["auto", "forecasting", "imputation", "classification", "blast", "split"],
        help="Dataset family to validate. forecasting/imputation share the split-file layout.",
    )
    parser.add_argument("--expect-timestamps", action="store_true", help="Require timestamp arrays for split layouts.")
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    if not root.exists():
        print(f"ERROR: root does not exist: {root}", file=sys.stderr)
        return 1
    if not root.is_dir():
        print(f"ERROR: root is not a directory: {root}", file=sys.stderr)
        return 1

    family = args.format
    if family == "auto":
        family = detect_format(root)

    if family in {"forecasting", "imputation", "split"}:
        result = validate_split_layout(root, args.expect_timestamps)
    elif family == "classification" or family == "auto" and detect_format(root) == "classification":
        result = validate_classification_layout(root)
    elif family == "blast":
        result = validate_blast_layout(root)
    else:
        print(f"ERROR: unsupported dataset format: {family}", file=sys.stderr)
        return 1

    print(f"format={family}")
    for msg in result.messages:
        print(msg)
    print("status=ok" if result.ok else "status=failed")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
