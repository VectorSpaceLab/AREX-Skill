#!/usr/bin/env python3
"""Read-only checks for PointCNN classification file-list and HDF5 contracts.

This helper intentionally does not import the legacy trainer or write to the
input tree. It mirrors the important data_utils.load_cls path rule: each file
list line is reduced to its basename and resolved beside the list.
"""
from __future__ import print_function

import argparse
import os
import sys
from pathlib import Path

try:
    import h5py
    import numpy as np
except ImportError as exc:  # pragma: no cover - exercised in minimal envs
    print("ERROR: h5py and numpy are required: {}".format(exc), file=sys.stderr)
    sys.exit(2)


SETTING_CONTRACTS = {
    "modelnet_x3_l4": (40, 6),
    "modelnet_x3_l4_aligned": (40, 6),
    "modelnet_x3_l4_aligned_w_fts": (40, 6),
    "modelnet_x3_l4_no_X": (40, 6),
    "modelnet_x3_l4_no_X_wider": (40, 6),
    "modelnet_x3_l4_w_fts": (40, 6),
    "modelnet_x3_l4_yxz": (40, 6),
    "modelnet_x3_l5_no_X": (40, 6),
    "scannet_x2_l4": (17, 6),
    "tu_berlin_x3_l4": (250, 6),
    "mnist_x2_l4": (10, 4),
    "cifar10_x3_l4": (10, 6),
    "quick_draw_full_x2_l6": (345, 6),
}


def fail(message):
    raise ValueError(message)


def resolve_list_entry(list_path, raw_line):
    """Resolve a list line as data_utils.load_cls does."""
    name = os.path.basename(raw_line.strip())
    if not name:
        fail("{} contains a blank entry".format(list_path))
    return Path(list_path).resolve().parent / name


def read_file_list(list_path):
    path = Path(list_path)
    if not path.is_file():
        fail("file list does not exist: {}".format(path))
    entries = []
    for line_no, raw in enumerate(path.read_text().splitlines(), 1):
        if not raw.strip():
            continue
        resolved = resolve_list_entry(path, raw)
        if not resolved.is_file():
            fail("{} line {} resolves to missing HDF5: {}".format(path, line_no, resolved))
        entries.append(resolved)
    if not entries:
        fail("file list is empty: {}".format(path))
    return entries


def validate_h5(path, expected_dim, expected_classes, reference):
    with h5py.File(str(path), "r") as handle:
        if "data" not in handle or "label" not in handle:
            fail("{} must contain datasets 'data' and 'label'".format(path))
        data_ds = handle["data"]
        label_ds = handle["label"]
        if len(data_ds.shape) != 3:
            fail("{} data must be rank 3 (samples, points, channels), got {}".format(path, data_ds.shape))
        samples, points, channels = data_ds.shape
        if samples < 1 or points < 3 or channels < 3:
            fail("{} data has unusable shape {}; need samples>0, points>=3, channels>=3".format(path, data_ds.shape))
        effective_dim = channels
        if "normal" in handle:
            normal_ds = handle["normal"]
            if len(normal_ds.shape) != 3 or normal_ds.shape[:2] != data_ds.shape[:2]:
                fail("{} normal must match data sample/point axes; data={}, normal={}".format(
                    path, data_ds.shape, normal_ds.shape))
            if normal_ds.shape[2] != 3:
                fail("{} normal must have three channels, got {}".format(path, normal_ds.shape))
            effective_dim += normal_ds.shape[2]
        if expected_dim is not None and effective_dim != expected_dim:
            fail("{} effective data_dim={} but setting expects {}".format(path, effective_dim, expected_dim))
        if not np.issubdtype(label_ds.dtype, np.integer):
            fail("{} label dtype must be integer, got {}".format(path, label_ds.dtype))
        labels = np.asarray(label_ds[...]).squeeze()
        if labels.ndim != 1 or labels.shape[0] != samples:
            fail("{} label must squeeze to ({},), got {}".format(path, samples, labels.shape))
        if labels.size and (int(labels.min()) < 0 or
                            (expected_classes is not None and int(labels.max()) >= expected_classes)):
            fail("{} labels range {}..{} is outside [0, {})".format(
                path, int(labels.min()), int(labels.max()), expected_classes if expected_classes is not None else "class-count"))
        shape = (points, effective_dim)
        if reference["shape"] is None:
            reference["shape"] = shape
        elif reference["shape"] != shape:
            fail("{} shape {} disagrees with earlier classification data shape {}".format(
                path, shape, reference["shape"]))
        reference["samples"] += samples
        reference["files"] += 1


def validate_file_list(list_path, expected_dim, expected_classes, reference):
    entries = read_file_list(list_path)
    for entry in entries:
        validate_h5(entry, expected_dim, expected_classes, reference)
    return len(entries)


def validate_quick_draw(folder):
    root = Path(folder)
    categories_path = root / "categories.txt"
    if not root.is_dir():
        fail("Quick Draw directory does not exist: {}".format(root))
    if not categories_path.is_file():
        fail("Quick Draw directory is missing categories.txt: {}".format(categories_path))
    categories = [line.strip() for line in categories_path.read_text().splitlines() if line.strip()]
    if not categories:
        fail("Quick Draw categories.txt is empty")
    missing = [name for name in categories if not (root / (name + ".npz")).is_file()]
    if missing:
        fail("Quick Draw category NPZ files are missing (first): {}".format(missing[0]))
    print("OK: Quick Draw directory has {} categories and matching NPZ files".format(len(categories)))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only validation of PointCNN classification inputs")
    parser.add_argument("--train-files", help="training HDF5 file list")
    parser.add_argument("--val-files", help="validation HDF5 file list")
    parser.add_argument("--quick-draw-dir", help="Quick Draw NPZ directory (checks categories.txt and category NPZ files)")
    parser.add_argument("--model", default="pointcnn_cls", help="model identifier; standard contract is pointcnn_cls")
    parser.add_argument("--setting", help="standard pointcnn_cls setting name")
    parser.add_argument("--num-class", type=int, help="override expected class count for a custom setting")
    parser.add_argument("--data-dim", type=int, help="override expected effective data width for a custom setting")
    args = parser.parse_args(argv)

    if args.model != "pointcnn_cls":
        fail("only the checked-in classification model identifier pointcnn_cls is known")
    if args.quick_draw_dir:
        if args.train_files or args.val_files:
            fail("use --quick-draw-dir instead of HDF5 file-list arguments")
        validate_quick_draw(args.quick_draw_dir)
        return 0
    if not args.train_files or not args.val_files:
        parser.error("--train-files and --val-files are required unless --quick-draw-dir is used")
    if args.setting and args.setting in SETTING_CONTRACTS:
        expected_classes, expected_dim = SETTING_CONTRACTS[args.setting]
    elif args.setting:
        expected_classes, expected_dim = None, None
        print("WARNING: custom/unknown setting {}; use --num-class and --data-dim for strict checks".format(args.setting))
    else:
        expected_classes, expected_dim = None, None
    if args.num_class is not None:
        expected_classes = args.num_class
    if args.data_dim is not None:
        expected_dim = args.data_dim
    if expected_classes is not None and expected_classes <= 0:
        fail("--num-class must be positive")
    if expected_dim is not None and expected_dim < 3:
        fail("--data-dim must be at least 3")

    train_ref = {"shape": None, "samples": 0, "files": 0}
    val_ref = {"shape": None, "samples": 0, "files": 0}
    train_count = validate_file_list(args.train_files, expected_dim, expected_classes, train_ref)
    val_count = validate_file_list(args.val_files, expected_dim, expected_classes, val_ref)
    if train_ref["shape"] != val_ref["shape"]:
        fail("training shape {} disagrees with validation shape {}".format(train_ref["shape"], val_ref["shape"]))
    print("OK: {} train files / {} samples; {} validation files / {} samples; shape points={}, data_dim={}".format(
        train_count, train_ref["samples"], val_count, val_ref["samples"],
        train_ref["shape"][0], train_ref["shape"][1]))
    if expected_classes is not None:
        print("OK: labels fit class range [0, {})".format(expected_classes))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as exc:
        print("ERROR: {}".format(exc), file=sys.stderr)
        sys.exit(1)
