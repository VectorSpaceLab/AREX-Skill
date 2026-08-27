#!/usr/bin/env python3
"""Inspect PointCNN flat/nested file lists without rewriting them."""
from __future__ import print_function

import argparse
import os
import sys
import tempfile

try:
    # Both files are bundled in this directory; no repository import is needed.
    from validate_pointcnn_h5 import _load_dependencies, _read_list_entries, _resolve_list, validate_files
except ImportError as exc:  # pragma: no cover - only a bad installation
    raise SystemExit("validator script is missing beside inspect_filelists.py: {}".format(exc))


class ListInspectionError(Exception):
    """Raised when a list cannot be inspected safely."""


def _write_fixture(directory):
    h5py, np = _load_dependencies()
    data_dir = os.path.join(directory, "data")
    list_dir = os.path.join(directory, "filelists")
    os.makedirs(data_dir)
    os.makedirs(list_dir)
    h5_path = os.path.join(data_dir, "tiny.h5")
    with h5py.File(h5_path, "w") as handle:
        handle.create_dataset("data", data=np.zeros((2, 3, 3), dtype=np.float32))
        handle.create_dataset("label", data=np.array([0, 1], dtype=np.int32))
    child = os.path.join(list_dir, "group.txt")
    with open(child, "w", encoding="utf-8") as handle:
        handle.write("../data/tiny.h5\n")
    top = os.path.join(directory, "train.txt")
    with open(top, "w", encoding="utf-8") as handle:
        handle.write("./filelists/group.txt\n")
    return top, h5_path


def self_test():
    with tempfile.TemporaryDirectory(prefix="pointcnn-list-check-") as directory:
        top, h5_path = _write_fixture(directory)
        paths, errors = _resolve_list(top, "segmentation")
        if errors or len(paths) != 1 or paths[0][0] != os.path.abspath(h5_path):
            raise AssertionError("nested relative HDF5 path was not resolved: {} {}".format(paths, errors))
        results, errors, _ = validate_files([h5_path], "classification")
        if errors or results[0]["errors"]:
            raise AssertionError("tiny HDF5 validation failed: {} {}".format(errors, results))
        print("self-test: PASS (temporary fixture removed)")


def _top_mode(list_path, kind):
    entries = _read_list_entries(list_path)
    nonempty = [value.strip() for _, value in entries if value.strip()]
    if not nonempty:
        return "empty"
    if kind == "classification":
        return "flat-classification"
    if all(value.lower().endswith(".h5") for value in nonempty):
        return "flat-segmentation" if kind == "segmentation" else "flat-auto"
    return "nested-segmentation"


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", dest="lists", action="append",
                        help="List file to inspect; repeatable")
    parser.add_argument("--kind", choices=("auto", "classification", "segmentation"), default="auto")
    parser.add_argument("--check-h5", action="store_true", help="Validate each resolved HDF5")
    parser.add_argument("--class-count", "--num-class", dest="class_count", type=int, metavar="K",
                        help="require active labels to be in [0,K)")
    parser.add_argument("--data-dim", type=int, metavar="C",
                        help="with --check-h5, expected effective feature width")
    parser.add_argument("--label-count", type=int, metavar="K",
                        help="with --check-h5, optional range for per-sample labels")
    bounds = parser.add_mutually_exclusive_group()
    bounds.add_argument("--index-size", "--full-point-count", dest="index_size", type=int, metavar="M",
                        help="upper bound for one-dimensional source indices")
    bounds.add_argument("--room-sizes", metavar="FILE",
                        help="one positive source point count per ScanNet room")
    parser.add_argument("--index-group-count", type=int, metavar="G",
                        help="with --check-h5, upper bound for room/group ids in pairs")
    parser.add_argument("--require-indices", action="store_true")
    parser.add_argument("--show-resolved", action="store_true", help="Print every resolved HDF5 path")
    parser.add_argument("--self-test", action="store_true", help="Run a disposable nested-list check")
    args = parser.parse_args(argv)
    if not args.self_test and not args.lists:
        parser.error("--list or --self-test is required")
    if args.class_count is not None and args.class_count <= 0:
        parser.error("--class-count must be positive")
    for value, option in ((args.data_dim, "--data-dim"),
                          (args.label_count, "--label-count"),
                          (args.index_size, "--index-size"),
                          (args.index_group_count, "--index-group-count")):
        if value is not None and value <= 0:
            parser.error("{} must be positive".format(option))
    return args


def inspect_one(list_path, args):
    mode = _top_mode(list_path, args.kind)
    resolved, list_errors = _resolve_list(list_path, args.kind)
    paths = [item[0] for item in resolved]
    print("LIST {} mode={} entries={}".format(
        os.path.abspath(list_path), mode, len(paths)))
    for error in list_errors:
        print("  ERROR {}".format(error))
    if not paths:
        raise ListInspectionError("{}: no HDF5 files resolved".format(list_path))

    duplicates = sorted(path for path in set(paths) if paths.count(path) > 1)
    missing = sorted(set(path for path in paths if not os.path.isfile(path)))
    print("  resolved_h5={} unique_h5={} duplicates={} missing={}".format(
        len(paths), len(set(paths)), len(duplicates), len(missing)))
    if duplicates:
        print("  duplicate paths:")
        for path in duplicates:
            print("    {}".format(path))
    if missing:
        print("  missing paths:")
        for path in missing:
            print("    {}".format(path))
    if args.show_resolved:
        print("  resolved paths:")
        for item in resolved:
            print("    {}:{}: {} -> {}".format(item[1], item[2], item[3], item[0]))
    if list_errors or missing:
        raise ListInspectionError("{}: list/path errors must be repaired".format(list_path))

    if args.check_h5:
        room_sizes = None
        if args.room_sizes:
            # validate_files accepts the parsed list; keep parsing in the
            # validator so both bundled tools use one format and error policy.
            from validate_pointcnn_h5 import _read_room_sizes
            room_sizes = _read_room_sizes(args.room_sizes)
        results, errors, warnings = validate_files(
            sorted(set(paths)), args.kind, args.class_count, args.index_size,
            room_sizes, args.require_indices, args.data_dim,
            args.label_count, args.index_group_count)
        for warning in warnings:
            print("  WARNING {}".format(warning))
        for result in results:
            state = "PASS" if not result["errors"] else "FAIL"
            print("  H5 {} {} kind={} data=[B={},N={},C={}] effective_features={} index_rank={}".format(
                state, os.path.basename(result["file"]), result["kind"],
                result["samples"], result["points"], result["features"],
                result["effective_features"], result["index_rank"]))
            for error in result["errors"]:
                print("    ERROR {}".format(error))
        if errors:
            for error in errors:
                print("  ERROR {}".format(error))
            raise ListInspectionError("{}: HDF5 validation failed".format(list_path))


def main(argv=None):
    args = parse_args(argv)
    if args.self_test:
        self_test()
        return 0
    try:
        for list_path in args.lists:
            inspect_one(list_path, args)
    except (ListInspectionError, OSError, IOError, ValueError, RuntimeError) as exc:
        print("ERROR: {}".format(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
