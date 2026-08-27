#!/usr/bin/env python
"""Validate PointNet2 ModelNet40 classification dataset layouts.

This script avoids importing modelnet_h5_dataset.py because that source module
can download data as a top-level import side effect when the HDF5 directory is
missing. It checks the file layouts encoded by modelnet_dataset.py and
modelnet_h5_dataset.py using only filesystem, numpy, and optionally h5py.
"""
from __future__ import print_function

import argparse
import io
import json
import os
import sys

try:
    import numpy as np
except Exception:  # pragma: no cover - handled at runtime
    np = None

try:
    import h5py
except Exception:  # pragma: no cover - optional dependency
    h5py = None


H5_DIR = os.path.join("data", "modelnet40_ply_hdf5_2048")
NORMAL_DIR = os.path.join("data", "modelnet40_normal_resampled")


class Report(object):
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        self.checked = []

    def error(self, message):
        self.errors.append(message)

    def warn(self, message):
        self.warnings.append(message)

    def add(self, message):
        self.info.append(message)

    def mark(self, item):
        self.checked.append(item)

    def as_dict(self):
        return {
            "ok": not self.errors,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "checked": self.checked,
        }


def read_lines(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


def is_file(path):
    return os.path.isfile(path)


def existing_path(candidates):
    for path in candidates:
        if path and os.path.exists(path):
            return os.path.abspath(path)
    return None


def resolve_h5_entry(entry, repo_root, dataset_root):
    if os.path.isabs(entry):
        candidates = [entry]
    else:
        candidates = [
            os.path.join(repo_root, entry),
            os.path.join(dataset_root, entry),
            os.path.join(dataset_root, os.path.basename(entry)),
        ]
    return existing_path(candidates)


def shape_name_from_id(shape_id):
    pieces = shape_id.split("_")
    if len(pieces) < 2:
        return None
    return "_".join(pieces[:-1])


def require_file(report, path, label):
    if os.path.isfile(path):
        report.mark(label + ": " + path)
        return True
    report.error("Missing %s: %s" % (label, path))
    return False


def validate_num_point(report, mode, num_point):
    if num_point <= 0:
        report.error("--num-point must be positive")
    if mode == "h5" and num_point > 2048:
        report.error("HDF5 mode supports --num-point <= 2048; requested %d" % num_point)
    if mode == "normal" and num_point > 10000:
        report.error("normal-resampled mode supports --num-point <= 10000; requested %d" % num_point)


def validate_shape_names(report, path):
    if not require_file(report, path, "shape_names.txt"):
        return []
    try:
        names = read_lines(path)
    except Exception as exc:
        report.error("Could not read shape_names.txt %s: %s" % (path, exc))
        return []
    if not names:
        report.error("shape_names.txt is empty: %s" % path)
    elif len(names) != 40:
        report.warn("Expected 40 ModelNet40 class names, found %d in %s" % (len(names), path))
    else:
        report.add("Found 40 shape names")
    return names


def validate_h5_file(report, h5_path, num_point, class_count):
    if h5py is None:
        report.warn("h5py is not available; skipped HDF5 key/shape inspection for %s" % h5_path)
        return
    try:
        with h5py.File(h5_path, "r") as handle:
            if "data" not in handle:
                report.error("HDF5 file missing 'data' dataset: %s" % h5_path)
                return
            if "label" not in handle:
                report.error("HDF5 file missing 'label' dataset: %s" % h5_path)
                return
            data_shape = tuple(handle["data"].shape)
            label_shape = tuple(handle["label"].shape)
            if len(data_shape) < 3:
                report.error("HDF5 data dataset must be at least 3-D [examples, points, channels], got %s in %s" % (data_shape, h5_path))
            else:
                if data_shape[1] < num_point:
                    report.error("HDF5 data in %s has only %d points, requested %d" % (h5_path, data_shape[1], num_point))
                if data_shape[2] < 3:
                    report.error("HDF5 data in %s has only %d channels, expected at least 3 XYZ channels" % (h5_path, data_shape[2]))
            if not label_shape:
                report.error("HDF5 label dataset is scalar, expected one label per example: %s" % h5_path)
            elif len(data_shape) >= 1 and label_shape[0] != data_shape[0]:
                report.error("HDF5 label count %d does not match data example count %d in %s" % (label_shape[0], data_shape[0], h5_path))
            if class_count and "label" in handle and label_shape and label_shape[0] > 0:
                labels = handle["label"][:]
                try:
                    label_min = int(labels.min())
                    label_max = int(labels.max())
                    if label_min < 0 or label_max >= class_count:
                        report.warn("Labels in %s span [%d, %d], outside shape_names range 0..%d" % (h5_path, label_min, label_max, class_count - 1))
                except Exception as exc:
                    report.warn("Could not inspect label range for %s: %s" % (h5_path, exc))
            report.mark("h5 data/label shapes: %s data=%s label=%s" % (h5_path, data_shape, label_shape))
    except Exception as exc:
        report.error("Could not open HDF5 file %s: %s" % (h5_path, exc))


def validate_h5_layout(report, repo_root, dataset_root, num_point, max_files_per_split):
    validate_num_point(report, "h5", num_point)
    if not os.path.isdir(dataset_root):
        report.error("Missing HDF5 dataset root: %s. Avoid importing modelnet_h5_dataset.py for this check because it may try to download data." % dataset_root)
        return
    report.mark("h5 root: " + dataset_root)

    names = validate_shape_names(report, os.path.join(dataset_root, "shape_names.txt"))
    class_count = len(names)

    for split_name, filename in [("train", "train_files.txt"), ("test", "test_files.txt")]:
        list_path = os.path.join(dataset_root, filename)
        if not require_file(report, list_path, filename):
            continue
        try:
            entries = read_lines(list_path)
        except Exception as exc:
            report.error("Could not read %s: %s" % (list_path, exc))
            continue
        if not entries:
            report.error("%s is empty" % list_path)
            continue
        report.add("%s lists %d HDF5 file(s)" % (filename, len(entries)))
        missing = []
        resolved = []
        for entry in entries:
            path = resolve_h5_entry(entry, repo_root, dataset_root)
            if path is None:
                missing.append(entry)
            else:
                resolved.append(path)
        if missing:
            preview = ", ".join(missing[:5])
            report.error("%s contains %d missing HDF5 path(s); first missing: %s" % (filename, len(missing), preview))
        for h5_path in resolved[:max_files_per_split]:
            validate_h5_file(report, h5_path, num_point, class_count)
        if resolved:
            report.add("Checked %d %s HDF5 file(s)" % (min(len(resolved), max_files_per_split), split_name))


def load_text_points(path):
    if np is None:
        raise RuntimeError("numpy is required to inspect normal-resampled text files")
    data = np.loadtxt(path, delimiter=",")
    if len(getattr(data, "shape", ())) == 1:
        data = data.reshape((1, data.shape[0]))
    return data


def validate_normal_sample(report, path, num_point, require_normal_channel):
    if not os.path.isfile(path):
        report.error("Missing normal-resampled sample file: %s" % path)
        return
    try:
        data = load_text_points(path)
    except Exception as exc:
        report.error("Could not parse comma-delimited numeric sample %s: %s" % (path, exc))
        return
    if data.shape[0] < num_point:
        report.error("Sample %s has only %d rows, requested --num-point %d" % (path, data.shape[0], num_point))
    min_cols = 6 if require_normal_channel else 3
    if data.shape[1] < min_cols:
        report.error("Sample %s has %d column(s), expected at least %d" % (path, data.shape[1], min_cols))
    if np is not None:
        try:
            if not np.isfinite(data[:, :min(data.shape[1], min_cols)]).all():
                report.error("Sample %s contains NaN or infinite values" % path)
        except Exception as exc:
            report.warn("Could not check finite values for %s: %s" % (path, exc))
    report.mark("normal sample: %s shape=%s" % (path, tuple(data.shape)))


def validate_normal_layout(report, dataset_root, num_point, max_samples_per_split, require_normal_channel):
    validate_num_point(report, "normal", num_point)
    if not os.path.isdir(dataset_root):
        report.error("Missing normal-resampled dataset root: %s" % dataset_root)
        return
    report.mark("normal root: " + dataset_root)

    validate_shape_names(report, os.path.join(dataset_root, "shape_names.txt"))
    for split_name, filename in [("train", "modelnet40_train.txt"), ("test", "modelnet40_test.txt")]:
        split_path = os.path.join(dataset_root, filename)
        if not require_file(report, split_path, filename):
            continue
        try:
            shape_ids = read_lines(split_path)
        except Exception as exc:
            report.error("Could not read %s: %s" % (split_path, exc))
            continue
        if not shape_ids:
            report.error("%s is empty" % split_path)
            continue
        report.add("%s lists %d shape id(s)" % (filename, len(shape_ids)))
        for shape_id in shape_ids[:max_samples_per_split]:
            class_name = shape_name_from_id(shape_id)
            if class_name is None:
                report.error("Shape id does not contain a class prefix and numeric suffix: %s" % shape_id)
                continue
            class_dir = os.path.join(dataset_root, class_name)
            if not os.path.isdir(class_dir):
                report.error("Missing class directory for shape id %s: %s" % (shape_id, class_dir))
                continue
            sample_path = os.path.join(class_dir, shape_id + ".txt")
            validate_normal_sample(report, sample_path, num_point, require_normal_channel)
        report.add("Checked up to %d %s normal sample(s)" % (max_samples_per_split, split_name))


def infer_mode_for_root(root):
    if os.path.isfile(os.path.join(root, "train_files.txt")) or os.path.isfile(os.path.join(root, "test_files.txt")):
        return "h5"
    if os.path.isfile(os.path.join(root, "modelnet40_train.txt")) or os.path.isfile(os.path.join(root, "modelnet40_test.txt")):
        return "normal"
    return None


def build_parser():
    parser = argparse.ArgumentParser(description="Validate ModelNet40 HDF5 or normal-resampled layout for PointNet2 classification.")
    parser.add_argument("--mode", choices=["auto", "h5", "normal"], default="auto",
                        help="Layout mode to validate. auto checks existing default roots or infers from --root.")
    parser.add_argument("--repo-root", default=".", help="PointNet2 checkout root used to resolve default data paths and HDF5 list entries.")
    parser.add_argument("--root", default=None, help="Dataset root. Defaults to data/modelnet40_ply_hdf5_2048 or data/modelnet40_normal_resampled under --repo-root.")
    parser.add_argument("--num-point", type=int, default=1024, help="Requested point count to validate [default: 1024].")
    parser.add_argument("--max-files-per-split", type=int, default=1, help="HDF5 files per split to inspect deeply [default: 1].")
    parser.add_argument("--max-samples-per-split", type=int, default=3, help="Normal text samples per split to inspect [default: 3].")
    parser.add_argument("--xyz-only-ok", action="store_true", help="For normal-resampled text, require only XYZ columns instead of XYZ+normal columns.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = os.path.abspath(args.repo_root)
    report = Report()

    if args.max_files_per_split < 0 or args.max_samples_per_split < 0:
        parser.error("max inspection counts must be non-negative")

    modes = []
    roots = {}
    if args.root:
        root = os.path.abspath(args.root)
        if args.mode == "auto":
            inferred = infer_mode_for_root(root)
            if inferred is None:
                report.error("Could not infer dataset mode from --root %s; pass --mode h5 or --mode normal" % root)
            else:
                modes = [inferred]
                roots[inferred] = root
        else:
            modes = [args.mode]
            roots[args.mode] = root
    elif args.mode == "auto":
        h5_root = os.path.join(repo_root, H5_DIR)
        normal_root = os.path.join(repo_root, NORMAL_DIR)
        if os.path.isdir(h5_root):
            modes.append("h5")
            roots["h5"] = h5_root
        if os.path.isdir(normal_root):
            modes.append("normal")
            roots["normal"] = normal_root
        if not modes:
            report.error("No default ModelNet40 dataset root found under %s; expected %s or %s" % (repo_root, H5_DIR, NORMAL_DIR))
    else:
        modes = [args.mode]
        roots[args.mode] = os.path.join(repo_root, H5_DIR if args.mode == "h5" else NORMAL_DIR)

    for mode in modes:
        if mode == "h5":
            validate_h5_layout(report, repo_root, roots[mode], args.num_point, args.max_files_per_split)
        elif mode == "normal":
            validate_normal_layout(report, roots[mode], args.num_point, args.max_samples_per_split, not args.xyz_only_ok)

    if args.json:
        print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    else:
        if report.errors:
            print("ModelNet layout validation: FAILED")
        else:
            print("ModelNet layout validation: OK")
        for item in report.info:
            print("INFO: " + item)
        for item in report.checked:
            print("CHECKED: " + item)
        for item in report.warnings:
            print("WARNING: " + item)
        for item in report.errors:
            print("ERROR: " + item)

    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
