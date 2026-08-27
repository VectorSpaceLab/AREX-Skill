#!/usr/bin/env python3
"""Read-only validator for PointCNN classification and segmentation HDF5.

This module intentionally imports h5py and NumPy only after argument parsing so
that ``--help`` remains available in an environment without those packages.
It never writes to an input HDF5 or list.
"""

from __future__ import print_function

import argparse
import os
import sys


H5PY = None
NP = None


def _load_dependencies():
    global H5PY, NP
    if H5PY is None or NP is None:
        try:
            import h5py  # pylint: disable=import-outside-toplevel
            import numpy as np  # pylint: disable=import-outside-toplevel
        except ImportError as exc:
            raise RuntimeError("validate_pointcnn_h5.py needs h5py and numpy: %s" % exc)
        H5PY, NP = h5py, np
    return H5PY, NP


def _integer_dtype(dtype):
    _, np = _load_dependencies()
    return np.issubdtype(dtype, np.integer) and not np.issubdtype(dtype, np.bool_)


def _floating_dtype(dtype):
    _, np = _load_dependencies()
    return np.issubdtype(dtype, np.floating)


def _check_shape(errors, name, shape, expected, description):
    if expected is not None and not expected(shape):
        errors.append("%s has shape %s; expected %s" % (name, shape, description))


def _check_finite(dataset, errors, name):
    """Check a dataset in bounded slices rather than loading it all at once."""
    _, np = _load_dependencies()
    if dataset.ndim == 0:
        values = dataset[()]
        if not np.isfinite(values):
            errors.append("%s contains NaN or Inf" % name)
        return
    first = dataset.shape[0]
    for start in range(0, first, 32):
        values = dataset[start:min(start + 32, first), ...]
        if not np.all(np.isfinite(values)):
            errors.append("%s contains NaN or Inf" % name)
            return


def _check_nonnegative(values, errors, name):
    _, np = _load_dependencies()
    if np.any(values < 0):
        errors.append("%s contains a negative active value" % name)


def _check_bounded(values, errors, name, upper):
    _, np = _load_dependencies()
    if np.any(values >= upper):
        errors.append("%s contains a value outside [0, %d)" % (name, upper))


def _label_shape(dataset, b, name, errors):
    shape = tuple(dataset.shape)
    if shape == (b,):
        return True
    if shape == (b, 1):
        return True
    errors.append("%s has shape %s; expected [%d] or [%d, 1]" % (name, shape, b, b))
    return False


def _row_values(dataset, row, count=None):
    values = dataset[row, ...]
    if count is not None:
        values = values[:count]
    return values


def _read_room_sizes(filename):
    _, np = _load_dependencies()
    sizes = []
    with open(filename, "r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            text = raw.strip()
            if not text or text.startswith("#"):
                continue
            fields = text.split()
            if len(fields) != 1:
                raise ValueError("%s:%d must contain one positive integer" % (filename, line_number))
            try:
                value = int(fields[0])
            except ValueError:
                raise ValueError("%s:%d is not an integer" % (filename, line_number))
            if value <= 0:
                raise ValueError("%s:%d must be positive" % (filename, line_number))
            sizes.append(value)
    if not sizes:
        raise ValueError("room-size file is empty: %s" % filename)
    return np.asarray(sizes, dtype=np.int64)


def _infer_kind(keys):
    if "data_num" in keys or "label_seg" in keys or "indices_split_to_full" in keys:
        return "segmentation"
    return "classification"


def validate_h5(filename, requested_kind="auto", class_count=None,
                index_size=None, room_sizes=None, require_indices=False,
                data_dim=None, label_count=None, index_group_count=None):
    """Return a dict with ``errors``, ``warnings`` and structural metadata."""
    h5py, np = _load_dependencies()
    result = {
        "file": os.path.abspath(filename),
        "kind": requested_kind,
        "errors": [],
        "warnings": [],
        "samples": None,
        "points": None,
        "features": None,
        "effective_features": None,
        "index_rank": None,
        "has_indices": False,
    }
    errors = result["errors"]
    warnings = result["warnings"]

    if not os.path.isfile(filename):
        errors.append("file does not exist: %s" % filename)
        return result

    try:
        handle = h5py.File(filename, "r")
    except (OSError, IOError, ValueError) as exc:
        errors.append("cannot open HDF5: %s" % exc)
        return result

    with handle:
        keys = set(handle.keys())
        kind = _infer_kind(keys) if requested_kind == "auto" else requested_kind
        result["kind"] = kind
        required = (set(("data", "label")) if kind == "classification" else
                    set(("data", "data_num", "label", "label_seg")))
        missing = sorted(required - keys)
        for key in missing:
            errors.append("missing required key: %s" % key)
        known = required | set(("normal", "indices_split_to_full"))
        extra = sorted(keys - known)
        if extra:
            warnings.append("unrecognized HDF5 keys: %s" % ", ".join(extra))
        if "data" not in handle:
            return result

        data = handle["data"]
        data_shape = tuple(data.shape)
        result["features"] = data_shape[2] if len(data_shape) == 3 else None
        _check_shape(errors, "data", data_shape,
                     lambda s: len(s) == 3 and s[0] > 0 and s[1] > 0 and s[2] >= 3,
                     "[B,N,C] with B,N>0 and C>=3")
        if not _floating_dtype(data.dtype):
            errors.append("data dtype %s is not floating point" % data.dtype)
        if len(data_shape) == 3 and data_shape[0] > 0:
            result["samples"], result["points"] = data_shape[:2]
            _check_finite(data, errors, "data")
        b = data_shape[0] if len(data_shape) >= 1 else None
        n = data_shape[1] if len(data_shape) >= 2 else None

        if "label" in handle and b is not None:
            label = handle["label"]
            if not _integer_dtype(label.dtype):
                errors.append("label dtype %s is not an integer dtype" % label.dtype)
            label_ok = _label_shape(label, b, "label", errors)
            if label_ok:
                values = label[...]
                values = values.reshape((b,))
                _check_nonnegative(values, errors, "label")
                if label_count is not None:
                    _check_bounded(values, errors, "label", label_count)
                if kind == "classification" and class_count is not None:
                    _check_bounded(values, errors, "label", class_count)

        if kind == "classification":
            if "normal" in handle:
                normal = handle["normal"]
                normal_shape = tuple(normal.shape)
                _check_shape(errors, "normal", normal_shape,
                             lambda s: len(s) == 3 and b is not None and n is not None and
                             s == (b, n, 3),
                             "[B,N,3] parallel to data")
                if not _floating_dtype(normal.dtype):
                    errors.append("normal dtype %s is not floating point" % normal.dtype)
                if len(normal_shape) == 3:
                    _check_finite(normal, errors, "normal")
                if len(data_shape) == 3 and normal_shape == (b, n, 3):
                    result["effective_features"] = data_shape[2] + 3
            else:
                result["effective_features"] = data_shape[2] if len(data_shape) == 3 else None
        else:
            result["effective_features"] = data_shape[2] if len(data_shape) == 3 else None
        if data_dim is not None and result["effective_features"] is not None and \
                result["effective_features"] != data_dim:
            errors.append("effective feature width %s does not equal --data-dim %s" %
                          (result["effective_features"], data_dim))

        if kind == "segmentation" and b is not None and n is not None:
            if "data_num" in handle:
                counts = handle["data_num"]
                count_shape = tuple(counts.shape)
                if count_shape != (b,):
                    errors.append("data_num has shape %s; expected [%d]" % (count_shape, b))
                if not _integer_dtype(counts.dtype):
                    errors.append("data_num dtype %s is not an integer dtype" % counts.dtype)
                if count_shape == (b,):
                    counts_values = counts[...]
                    if np.any(counts_values < 1) or np.any(counts_values > n):
                        errors.append("data_num must satisfy 1 <= data_num[i] <= %d" % n)
                else:
                    counts_values = None
            else:
                counts_values = None

            if "label_seg" in handle:
                label_seg = handle["label_seg"]
                label_seg_shape = tuple(label_seg.shape)
                if label_seg_shape != (b, n):
                    errors.append("label_seg has shape %s; expected [%d,%d]" %
                                  (label_seg_shape, b, n))
                if not _integer_dtype(label_seg.dtype):
                    errors.append("label_seg dtype %s is not an integer dtype" % label_seg.dtype)
                if label_seg_shape == (b, n) and counts_values is not None:
                    for row, count in enumerate(counts_values):
                        active = _row_values(label_seg, row, int(count))
                        _check_nonnegative(active, errors, "label_seg[%d]" % row)
                        if class_count is not None:
                            _check_bounded(active, errors, "label_seg[%d]" % row, class_count)

            if "indices_split_to_full" in handle:
                result["has_indices"] = True
                indices = handle["indices_split_to_full"]
                index_shape = tuple(indices.shape)
                if index_shape == (b, n):
                    result["index_rank"] = 1
                elif len(index_shape) == 3 and index_shape == (b, n, 2):
                    result["index_rank"] = 2
                else:
                    errors.append("indices_split_to_full has shape %s; expected [%d,%d] or [%d,%d,2]" %
                                  (index_shape, b, n, b, n))
                if not _integer_dtype(indices.dtype):
                    errors.append("indices_split_to_full dtype %s is not an integer dtype" % indices.dtype)
                if result["index_rank"] is not None and counts_values is not None:
                    for row, count in enumerate(counts_values):
                        active = _row_values(indices, row, int(count))
                        _check_nonnegative(active, errors, "indices_split_to_full[%d]" % row)
                        if result["index_rank"] == 1 and index_size is not None:
                            _check_bounded(active, errors, "indices_split_to_full[%d]" % row, index_size)
                        elif result["index_rank"] == 2:
                            rooms = active[:, 0]
                            points = active[:, 1]
                            if index_group_count is not None:
                                _check_bounded(rooms, errors, "indices_split_to_full[%d].room" % row,
                                               index_group_count)
                            if index_size is not None:
                                _check_bounded(points, errors, "indices_split_to_full[%d].point" % row,
                                               index_size)
                            if room_sizes is not None:
                                if np.any(rooms >= len(room_sizes)):
                                    errors.append("indices_split_to_full[%d] contains an unknown room" % row)
                                valid_rooms = rooms < len(room_sizes)
                                if np.any(points[valid_rooms] >= room_sizes[rooms[valid_rooms]]):
                                    errors.append("indices_split_to_full[%d] contains a point outside room bounds" % row)
                if result["index_rank"] == 1 and (room_sizes is not None or index_group_count is not None):
                    errors.append("room-sizes/index-group-count apply only to [B,N,2] ScanNet-style indices")
                if result["index_rank"] is not None and index_size is None and room_sizes is None and \
                        index_group_count is None:
                    warnings.append("active source indices are nonnegative, but no source bound was supplied")
            elif require_indices:
                errors.append("indices_split_to_full is required but missing")
        elif kind == "segmentation" and require_indices:
            errors.append("indices_split_to_full is required but data shape is invalid")

    return result


def _read_list_entries(filename):
    try:
        with open(filename, "r", encoding="utf-8") as handle:
            return [(line_number, line.rstrip("\r\n")) for line_number, line in enumerate(handle, 1)]
    except (OSError, IOError) as exc:
        return [(0, "__READ_ERROR__:%s" % exc)]


def _resolve_list(filename, kind, seen=None):
    """Resolve files with the same basename/nested-list rules as the loaders."""
    if seen is None:
        seen = []
    absolute = os.path.abspath(filename)
    errors = []
    paths = []
    if absolute in seen:
        return paths, ["cyclic child list: %s" % filename]
    entries = _read_list_entries(filename)
    if entries and entries[0][1].startswith("__READ_ERROR__:"):
        return paths, [entries[0][1][len("__READ_ERROR__:"):]]
    if not entries:
        return paths, ["list is empty: %s" % filename]
    raw_lines = [text for _, text in entries]
    if any(not text.strip() for text in raw_lines):
        errors.append("blank list entry in %s" % filename)
    if kind == "classification":
        for line_number, text in entries:
            entry = text.strip()
            if not entry:
                continue
            paths.append((os.path.join(os.path.dirname(absolute), os.path.basename(entry)),
                          filename, line_number, entry))
        return paths, errors

    flat = all(text.strip().lower().endswith(".h5") for text in raw_lines if text.strip())
    if kind == "segmentation" and flat:
        for line_number, text in entries:
            entry = text.strip()
            if not entry:
                continue
            paths.append((os.path.abspath(os.path.join(os.path.dirname(absolute), entry)),
                          filename, line_number, entry))
        return paths, errors

    if kind == "auto" and flat:
        for line_number, text in entries:
            entry = text.strip()
            if not entry:
                continue
            paths.append((os.path.abspath(os.path.join(os.path.dirname(absolute), entry)),
                          filename, line_number, entry))
        return paths, errors

    for line_number, text in entries:
        entry = text.strip()
        if not entry:
            continue
        child = os.path.abspath(os.path.join(os.path.dirname(absolute), entry))
        child_paths, child_errors = _resolve_list(child, "segmentation", seen + [absolute])
        paths.extend(child_paths)
        errors.extend("%s:%d: %s" % (filename, line_number, message) for message in child_errors)
    return paths, errors


def validate_files(files, kind="auto", class_count=None, index_size=None,
                   room_sizes=None, require_indices=False, data_dim=None,
                   label_count=None, index_group_count=None):
    results = []
    errors = []
    warnings = []
    for filename in files:
        result = validate_h5(filename, kind, class_count, index_size, room_sizes,
                             require_indices, data_dim, label_count, index_group_count)
        results.append(result)
        errors.extend("%s: %s" % (filename, message) for message in result["errors"])
        warnings.extend("%s: %s" % (filename, message) for message in result["warnings"])

    valid_results = [r for r in results if not r["errors"] and r["samples"] is not None]
    if valid_results:
        first = valid_results[0]
        for result in valid_results[1:]:
            for field in ("kind", "points", "effective_features"):
                if result[field] != first[field]:
                    errors.append("list mismatch: %s=%s but %s=%s in %s" %
                                  (field, first[field], field, result[field], result["file"]))
            if result["kind"] == "segmentation":
                if result["has_indices"] != first["has_indices"]:
                    errors.append("list mismatch: indices_split_to_full presence differs in %s" % result["file"])
                if result["has_indices"] and result["index_rank"] != first["index_rank"]:
                    errors.append("list mismatch: index rank differs in %s" % result["file"])
    return results, errors, warnings


def _make_self_test():
    import tempfile
    import shutil
    h5py, np = _load_dependencies()
    root = tempfile.mkdtemp(prefix="pointcnn-data-validation-")
    try:
        class_file = os.path.join(root, "class.h5")
        with h5py.File(class_file, "w") as handle:
            handle["data"] = np.zeros((2, 4, 3), dtype=np.float32)
            handle["normal"] = np.zeros((2, 4, 3), dtype=np.float32)
            handle["label"] = np.asarray([0, 1], dtype=np.int32)
        seg_dir = os.path.join(root, "seg")
        child_dir = os.path.join(root, "lists")
        os.makedirs(seg_dir)
        os.makedirs(child_dir)
        seg_file = os.path.join(seg_dir, "room.h5")
        with h5py.File(seg_file, "w") as handle:
            handle["data"] = np.zeros((1, 4, 3), dtype=np.float32)
            handle["data_num"] = np.asarray([2], dtype=np.int32)
            handle["label"] = np.asarray([0], dtype=np.int32)
            handle["label_seg"] = np.asarray([[1, 2, -7, -7]], dtype=np.int32)
            handle["indices_split_to_full"] = np.asarray([[4, 3, 99, 99]], dtype=np.int32)
        good, _, _ = validate_files([class_file], "classification", class_count=2)
        if good[0]["errors"]:
            raise AssertionError("classification self-test failed: %s" % good[0]["errors"])
        bad, _, _ = validate_files([seg_file], "segmentation", class_count=2, index_size=4)
        if not bad[0]["errors"]:
            raise AssertionError("segmentation self-test did not reject bad index/label")
        child = os.path.join(child_dir, "group.txt")
        with open(child, "w", encoding="utf-8") as handle:
            handle.write("../seg/room.h5\n")
        paths, list_errors = _resolve_list(child, "segmentation")
        if list_errors or len(paths) != 1 or paths[0][0] != os.path.abspath(seg_file):
            raise AssertionError("nested-list self-test failed: %s %s" % (paths, list_errors))
        print("self-test: PASS (temporary fixtures removed)")
        return 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Read-only validation of PointCNN classification/segmentation HDF5 contracts.")
    parser.add_argument("--h5", action="append", dest="h5_files", metavar="FILE",
                        help="HDF5 file to validate; may be repeated")
    parser.add_argument("--filelist", action="append", metavar="LIST",
                        help="flat or nested list to resolve and validate; may be repeated")
    parser.add_argument("--kind", choices=("auto", "classification", "segmentation"), default="auto",
                        help="input contract (default: auto per HDF5; file lists need explicit kind for classification)")
    parser.add_argument("--class-count", "--num-class", dest="class_count", type=int, metavar="K",
                        help="require active target labels to be in [0,K)")
    parser.add_argument("--data-dim", type=int, metavar="C",
                        help="expected effective feature width (including optional classification normals)")
    parser.add_argument("--label-count", type=int, metavar="K",
                        help="optional range for the per-sample label field")
    bounds = parser.add_mutually_exclusive_group()
    bounds.add_argument("--index-size", "--full-point-count", dest="index_size", type=int, metavar="M",
                        help="upper bound for active one-dimensional source indices, or point ids in a pair")
    bounds.add_argument("--room-sizes", metavar="FILE",
                        help="one positive source point count per room for [B,N,2] indices")
    parser.add_argument("--index-group-count", type=int, metavar="G",
                        help="upper bound for room/group ids in [B,N,2] indices")
    parser.add_argument("--require-indices", action="store_true",
                        help="fail segmentation files without indices_split_to_full")
    parser.add_argument("--self-test", action="store_true",
                        help="validate disposable HDF5 and nested-list fixtures, then remove them")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        try:
            return _make_self_test()
        except (AssertionError, RuntimeError, OSError, IOError, ValueError) as exc:
            print("self-test: FAIL: %s" % exc, file=sys.stderr)
            return 1
    if not args.h5_files and not args.filelist:
        parser.error("provide --h5, --filelist, or --self-test")
    for value, option in ((args.class_count, "--class-count"),
                          (args.data_dim, "--data-dim"),
                          (args.label_count, "--label-count"),
                          (args.index_size, "--index-size"),
                          (args.index_group_count, "--index-group-count")):
        if value is not None and value <= 0:
            parser.error("%s must be positive" % option)

    try:
        room_sizes = _read_room_sizes(args.room_sizes) if args.room_sizes else None
        files = []
        list_errors = []
        for filename in args.filelist or []:
            resolved, errors = _resolve_list(filename, args.kind)
            files.extend(path[0] for path in resolved)
            list_errors.extend(errors)
        files.extend(os.path.abspath(filename) for filename in args.h5_files or [])
        if not files:
            list_errors.append("no HDF5 entries resolved")
        results, errors, warnings = validate_files(
            files, args.kind, args.class_count, args.index_size, room_sizes,
            args.require_indices, args.data_dim, args.label_count,
            args.index_group_count)
    except (RuntimeError, OSError, IOError, ValueError) as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return 1

    for message in list_errors:
        print("ERROR: %s" % message, file=sys.stderr)
    for message in warnings:
        print("WARNING: %s" % message)
    for result in results:
        state = "PASS" if not result["errors"] else "FAIL"
        print("[%s] %s kind=%s samples=%s points=%s effective_features=%s index_rank=%s" %
              (state, result["file"], result["kind"], result["samples"], result["points"],
               result["effective_features"], result["index_rank"]))
        for message in result["errors"]:
            print("ERROR: %s: %s" % (result["file"], message), file=sys.stderr)
    for message in errors:
        print("ERROR: %s" % message, file=sys.stderr)
    return 1 if list_errors or errors else 0


if __name__ == "__main__":
    sys.exit(main())
