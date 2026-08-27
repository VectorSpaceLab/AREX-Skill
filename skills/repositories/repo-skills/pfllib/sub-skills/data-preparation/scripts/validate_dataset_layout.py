#!/usr/bin/env python3
"""Validate a PFLlib dataset split tree.

Checks the common `config.json` + `train/` + `test/` layout, verifies that the
client files round-trip to a `data` dict, and compares the file counts against
any expected client or class counts supplied on the command line.

Examples:
  python validate_dataset_layout.py --dataset-root /path/to/PFLlib/dataset/MNIST --expect-clients 20 --expect-classes 10
  python validate_dataset_layout.py --dataset-root /path/to/PFLlib/dataset/HAR
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def load_npz_dict(path: Path) -> dict:
    with np.load(path, allow_pickle=True) as payload:
        if "data" not in payload.files:
            raise KeyError(f"{path.name} does not contain a 'data' entry")
        value = payload["data"].tolist()
    if not isinstance(value, dict):
        raise TypeError(f"{path.name} does not round-trip to a dict")
    missing = {"x", "y"} - set(value)
    if missing:
        raise KeyError(f"{path.name} is missing keys: {sorted(missing)}")
    return value


def summarize_sample(sample: dict) -> str:
    x = sample["x"]
    y = sample["y"]
    x_shape = getattr(x, "shape", None)
    y_shape = getattr(y, "shape", None)
    return f"x={x_shape!s} y={y_shape!s}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", required=True, help="Path to one generated dataset directory, such as dataset/MNIST.")
    parser.add_argument("--expect-clients", type=int, help="Expected number of client split files in each of train/ and test/.")
    parser.add_argument("--expect-classes", type=int, help="Expected number of classes recorded in config.json.")
    parser.add_argument("--expect-partition", help="Optional partition value that should appear in config.json.")
    parser.add_argument("--sample-index", type=int, default=0, help="Which client file index to inspect for the sample round-trip check.")
    args = parser.parse_args()

    dataset_root = Path(args.dataset_root).expanduser().resolve()
    config_path = dataset_root / "config.json"
    train_dir = dataset_root / "train"
    test_dir = dataset_root / "test"

    if not dataset_root.is_dir():
        return fail(f"dataset root not found: {dataset_root}")
    if not config_path.is_file():
        return fail(f"missing config.json: {config_path}")
    if not train_dir.is_dir():
        return fail(f"missing train/ directory: {train_dir}")
    if not test_dir.is_dir():
        return fail(f"missing test/ directory: {test_dir}")

    config = json.loads(config_path.read_text())
    train_files = sorted(train_dir.glob("*.npz"))
    test_files = sorted(test_dir.glob("*.npz"))

    if not train_files:
        return fail(f"no train split files found in {train_dir}")
    if not test_files:
        return fail(f"no test split files found in {test_dir}")

    if args.expect_clients is not None:
        if len(train_files) != args.expect_clients:
            return fail(f"expected {args.expect_clients} train files but found {len(train_files)}")
        if len(test_files) != args.expect_clients:
            return fail(f"expected {args.expect_clients} test files but found {len(test_files)}")
    elif "num_clients" in config:
        if len(train_files) != int(config["num_clients"]):
            return fail(f"train file count {len(train_files)} does not match config num_clients {config['num_clients']}")
        if len(test_files) != int(config["num_clients"]):
            return fail(f"test file count {len(test_files)} does not match config num_clients {config['num_clients']}")

    if args.expect_classes is not None and "num_classes" in config:
        if int(config["num_classes"]) != args.expect_classes:
            return fail(f"expected {args.expect_classes} classes but config records {config['num_classes']}")

    if args.expect_partition is not None and "partition" in config:
        if config["partition"] != args.expect_partition:
            return fail(f"expected partition {args.expect_partition!r} but config records {config['partition']!r}")

    if args.sample_index < 0 or args.sample_index >= len(train_files):
        return fail(f"sample index {args.sample_index} is out of range for {len(train_files)} client files")

    train_sample = load_npz_dict(train_files[args.sample_index])
    test_sample = load_npz_dict(test_files[args.sample_index])

    print(f"dataset_root: {dataset_root}")
    print(f"config_keys: {sorted(config.keys())}")
    if "num_clients" in config:
        print(f"num_clients: {config['num_clients']}")
    if "num_classes" in config:
        print(f"num_classes: {config['num_classes']}")
    if "partition" in config:
        print(f"partition: {config['partition']}")
    print(f"train_files: {len(train_files)}")
    print(f"test_files: {len(test_files)}")
    print(f"sample_train: {train_files[args.sample_index].name} -> {summarize_sample(train_sample)}")
    print(f"sample_test: {test_files[args.sample_index].name} -> {summarize_sample(test_sample)}")
    print("layout_ok: true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
