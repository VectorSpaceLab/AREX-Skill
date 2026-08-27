#!/usr/bin/env python
"""Smoke-load a tiny ModelNet40 classification batch without importing repo loaders.

The goal is to verify data shape assumptions before running TensorFlow training
or evaluation. This script supports the two classification layouts distilled in
this sub-skill: HDF5 XYZ and normal-resampled text files.
"""
from __future__ import print_function

import argparse
import io
import json
import os
import sys

try:
    import numpy as np
except Exception as exc:  # pragma: no cover - runtime dependency check
    np = None
    NP_IMPORT_ERROR = exc
else:
    NP_IMPORT_ERROR = None

try:
    import h5py
except Exception as exc:  # pragma: no cover - optional h5 mode dependency
    h5py = None
    H5PY_IMPORT_ERROR = exc
else:
    H5PY_IMPORT_ERROR = None


H5_DIR = os.path.join("data", "modelnet40_ply_hdf5_2048")
NORMAL_DIR = os.path.join("data", "modelnet40_normal_resampled")


def read_lines(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


def resolve_h5_entry(entry, repo_root, dataset_root):
    if os.path.isabs(entry):
        candidates = [entry]
    else:
        candidates = [
            os.path.join(repo_root, entry),
            os.path.join(dataset_root, entry),
            os.path.join(dataset_root, os.path.basename(entry)),
        ]
    for path in candidates:
        if os.path.exists(path):
            return os.path.abspath(path)
    raise IOError("Could not resolve HDF5 path listed as %r" % entry)


def shape_name_from_id(shape_id):
    pieces = shape_id.split("_")
    if len(pieces) < 2:
        raise ValueError("shape id does not contain class prefix and numeric suffix: %s" % shape_id)
    return "_".join(pieces[:-1])


def normalize_xyz(points):
    xyz = points[:, 0:3].astype("float32")
    centroid = xyz.mean(axis=0)
    xyz = xyz - centroid
    radius = np.sqrt((xyz ** 2).sum(axis=1)).max()
    if radius > 0:
        xyz = xyz / radius
    points = points.copy()
    points[:, 0:3] = xyz
    return points


def smoke_h5(repo_root, dataset_root, split, num_point, batch_size):
    if h5py is None:
        raise RuntimeError("h5py is required for HDF5 smoke loading: %s" % H5PY_IMPORT_ERROR)
    if num_point > 2048:
        raise ValueError("HDF5 mode supports num_point <= 2048, got %d" % num_point)
    list_name = "train_files.txt" if split == "train" else "test_files.txt"
    list_path = os.path.join(dataset_root, list_name)
    entries = read_lines(list_path)
    if not entries:
        raise ValueError("%s is empty" % list_path)
    h5_path = resolve_h5_entry(entries[0], repo_root, dataset_root)
    with h5py.File(h5_path, "r") as handle:
        if "data" not in handle or "label" not in handle:
            raise ValueError("%s must contain HDF5 datasets named 'data' and 'label'" % h5_path)
        data = handle["data"][:batch_size, :num_point, :3]
        labels = handle["label"][:batch_size]
    labels = np.asarray(labels).reshape((-1,))
    if data.shape[0] == 0:
        raise ValueError("No examples loaded from %s" % h5_path)
    if data.shape[1] < num_point:
        raise ValueError("Loaded data has only %d points, requested %d" % (data.shape[1], num_point))
    if labels.shape[0] != data.shape[0]:
        raise ValueError("Label count %d does not match data count %d" % (labels.shape[0], data.shape[0]))
    return {
        "mode": "h5",
        "split": split,
        "source": h5_path,
        "dataShape": list(data.shape),
        "labelShape": list(labels.shape),
        "dtype": str(data.dtype),
        "labelPreview": [int(x) for x in labels[:min(5, labels.shape[0])]],
        "numChannel": int(data.shape[2]),
    }


def load_text_sample(path, num_point, normal_channel):
    raw = np.loadtxt(path, delimiter=",")
    if len(raw.shape) == 1:
        raw = raw.reshape((1, raw.shape[0]))
    min_cols = 6 if normal_channel else 3
    if raw.shape[0] < num_point:
        raise ValueError("%s has only %d rows, requested %d" % (path, raw.shape[0], num_point))
    if raw.shape[1] < min_cols:
        raise ValueError("%s has %d columns, expected at least %d" % (path, raw.shape[1], min_cols))
    points = raw[:num_point, :min_cols].astype("float32")
    points = normalize_xyz(points)
    return points


def smoke_normal(dataset_root, split, num_point, batch_size, normal_channel):
    if num_point > 10000:
        raise ValueError("normal-resampled mode supports num_point <= 10000, got %d" % num_point)
    split_file = "modelnet40_train.txt" if split == "train" else "modelnet40_test.txt"
    split_path = os.path.join(dataset_root, split_file)
    shape_ids = read_lines(split_path)
    if not shape_ids:
        raise ValueError("%s is empty" % split_path)
    shape_names_path = os.path.join(dataset_root, "shape_names.txt")
    shape_names = read_lines(shape_names_path)
    class_to_idx = dict((name, idx) for idx, name in enumerate(shape_names))

    points = []
    labels = []
    sources = []
    for shape_id in shape_ids:
        if len(points) >= batch_size:
            break
        class_name = shape_name_from_id(shape_id)
        sample_path = os.path.join(dataset_root, class_name, shape_id + ".txt")
        arr = load_text_sample(sample_path, num_point, normal_channel)
        if class_name not in class_to_idx:
            raise ValueError("class %s from %s is not present in shape_names.txt" % (class_name, shape_id))
        points.append(arr)
        labels.append(class_to_idx[class_name])
        sources.append(sample_path)
    if not points:
        raise ValueError("No normal-resampled samples loaded from %s" % split_path)
    data = np.stack(points, axis=0)
    label_array = np.asarray(labels, dtype="int32")
    return {
        "mode": "normal",
        "split": split,
        "sources": sources,
        "dataShape": list(data.shape),
        "labelShape": list(label_array.shape),
        "dtype": str(data.dtype),
        "labelPreview": [int(x) for x in label_array[:min(5, label_array.shape[0])]],
        "numChannel": int(data.shape[2]),
        "normalChannel": bool(normal_channel),
    }


def build_parser():
    parser = argparse.ArgumentParser(description="Smoke-load a small ModelNet40 batch without TensorFlow or repo loader imports.")
    parser.add_argument("--mode", choices=["h5", "normal"], default="h5", help="Dataset layout to smoke-load [default: h5].")
    parser.add_argument("--repo-root", default=".", help="PointNet2 checkout root for default data paths and HDF5 list resolution.")
    parser.add_argument("--root", default=None, help="Dataset root override.")
    parser.add_argument("--split", choices=["train", "test"], default="test", help="Split to load [default: test].")
    parser.add_argument("--num-point", type=int, default=16, help="Points per shape to load [default: 16].")
    parser.add_argument("--batch-size", type=int, default=2, help="Examples to load [default: 2].")
    parser.add_argument("--normal-channel", action="store_true", help="In normal mode, load XYZ+normal columns instead of XYZ only.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if np is None:
        parser.error("numpy is required: %s" % NP_IMPORT_ERROR)
    if args.num_point <= 0:
        parser.error("--num-point must be positive")
    if args.batch_size <= 0:
        parser.error("--batch-size must be positive")

    repo_root = os.path.abspath(args.repo_root)
    if args.root:
        dataset_root = os.path.abspath(args.root)
    else:
        dataset_root = os.path.join(repo_root, H5_DIR if args.mode == "h5" else NORMAL_DIR)

    try:
        if args.mode == "h5":
            result = smoke_h5(repo_root, dataset_root, args.split, args.num_point, args.batch_size)
        else:
            result = smoke_normal(dataset_root, args.split, args.num_point, args.batch_size, args.normal_channel)
    except Exception as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True))
        else:
            print("ModelNet loader smoke: FAILED")
            print("ERROR: " + str(exc))
        return 1

    result["ok"] = True
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("ModelNet loader smoke: OK")
        print("mode: %s" % result["mode"])
        print("split: %s" % result["split"])
        print("data shape: %s" % result["dataShape"])
        print("label shape: %s" % result["labelShape"])
        print("channels: %s" % result["numChannel"])
        if result["mode"] == "h5":
            print("source: %s" % result["source"])
        else:
            print("sources checked: %d" % len(result["sources"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
