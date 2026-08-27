#!/usr/bin/env python3
"""Read-only validation for PointCNN segmentation HDF5 inputs.

The checker accepts a flat text file containing HDF5 paths or one or more
explicit HDF5 paths. It checks the datasets consumed by ``data_utils.load_seg``
without importing TensorFlow and never writes to the input tree.
"""

from __future__ import print_function

import argparse
import sys
from pathlib import Path

try:
    import h5py
    import numpy as np
except ImportError as exc:  # pragma: no cover - depends on caller environment
    print("ERROR: h5py and numpy are required: {}".format(exc), file=sys.stderr)
    raise SystemExit(2)


REQUIRED_DATASETS = ("data", "data_num", "label", "label_seg")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument(
        "--filelist",
        help="Flat UTF-8 list of HDF5 paths; entries are resolved relative to the list.",
    )
    sources.add_argument(
        "--h5",
        dest="h5_files",
        action="append",
        help="Explicit HDF5 path; repeat this option to check several files.",
    )
    parser.add_argument(
        "--data-dim",
        type=int,
        help="Expected data width (the selected setting's data_dim).",
    )
    parser.add_argument(
        "--num-class",
        type=int,
        help="Expected active label_seg range: 0 <= label_seg < NUM_CLASS.",
    )
    parser.add_argument(
        "--label-count",
        type=int,
        help="Optional range for per-item label: 0 <= label < LABEL_COUNT.",
    )
    parser.add_argument(
        "--full-point-count",
        type=int,
        help=(
            "Optional exclusive upper bound for active indices. For rank-3 "
            "indices_split_to_full, this checks the point-id column."
        ),
    )
    parser.add_argument(
        "--index-group-count",
        type=int,
        help=(
            "Optional exclusive upper bound for the group/room column of a "
            "rank-3 indices_split_to_full dataset."
        ),
    )
    parser.add_argument(
        "--max-files",
        type=int,
        help="Check at most this many paths after reading the source list.",
    )
    return parser


def is_integer_dtype(dtype):
    return np.issubdtype(dtype, np.integer) and not np.issubdtype(dtype, np.bool_)


def is_float_dtype(dtype):
    return np.issubdtype(dtype, np.floating)


def resolve_entries(filelist):
    """Resolve entries using the same parent-relative convention as load_seg."""
    path = Path(filelist).expanduser()
    if not path.is_file():
        raise ValueError("file list does not exist: {}".format(path))

    entries = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            value = raw.strip()
            if not value:
                raise ValueError("{} line {} is blank; legacy segmentation lists must contain only HDF5 paths".format(path, line_number))
            if value.startswith("#"):
                raise ValueError("{} line {} is a comment; legacy segmentation lists must contain only HDF5 paths".format(path, line_number))
            candidate = Path(value).expanduser()
            if not candidate.is_absolute():
                candidate = path.parent / candidate
            entries.append((candidate.resolve(), line_number))
    return entries


def explicit_entries(values):
    return [(Path(value).expanduser().resolve(), None) for value in values or []]


def add_error(errors, path, message):
    errors.append("{}: {}".format(path, message))


def check_finite_data(dataset, path, errors):
    """Check finite values in bounded slices, avoiding a second full copy."""
    rows = int(dataset.shape[0])
    chunk_rows = max(1, min(rows, 64))
    for start in range(0, rows, chunk_rows):
        stop = min(rows, start + chunk_rows)
        values = dataset[start:stop, ...]
        if not np.all(np.isfinite(values)):
            add_error(errors, path, "data contains NaN or infinite values")
            return


def active_rows(dataset, counts, row_count):
    """Yield active values without reading padded points into one large array."""
    for row in range(row_count):
        count = int(counts[row])
        yield row, dataset[row, :count, ...]


def validate_file(path, args, reference):
    errors = []
    try:
        handle = h5py.File(str(path), "r")
    except (OSError, IOError) as exc:
        return ["{}: cannot open HDF5 file: {}".format(path, exc)], None

    with handle:
        missing = [name for name in REQUIRED_DATASETS if name not in handle]
        if missing:
            add_error(errors, path, "missing required dataset(s): {}".format(", ".join(missing)))
            return errors, None

        data = handle["data"]
        data_num = handle["data_num"]
        label = handle["label"]
        label_seg = handle["label_seg"]

        if data.ndim != 3:
            add_error(errors, path, "data must have rank 3 [items, padded_points, data_dim], found rank {}".format(data.ndim))
            return errors, None
        items, padded_points, data_dim = (int(value) for value in data.shape)
        if items < 1 or padded_points < 1 or data_dim < 3:
            add_error(errors, path, "data shape {} requires items>0, padded_points>0, and data_dim>=3".format(data.shape))
        if not is_float_dtype(data.dtype):
            add_error(errors, path, "data must have a floating dtype, found {}".format(data.dtype))
        else:
            check_finite_data(data, path, errors)
        if args.data_dim is not None and data_dim != args.data_dim:
            add_error(errors, path, "data width {} does not equal --data-dim {}".format(data_dim, args.data_dim))

        shape_contract = (padded_points, data_dim)
        if reference["data_shape"] is None:
            reference["data_shape"] = shape_contract
        elif reference["data_shape"] != shape_contract:
            add_error(
                errors,
                path,
                "padded point/data width {} disagrees with earlier files {}".format(
                    shape_contract, reference["data_shape"]
                ),
            )

        counts = None
        counts_valid = False
        if data_num.ndim != 1 or tuple(data_num.shape) != (items,):
            add_error(
                errors,
                path,
                "data_num must be integer rank-1 shape [{}], found shape {} dtype {}".format(
                    items, data_num.shape, data_num.dtype
                ),
            )
        elif not is_integer_dtype(data_num.dtype):
            add_error(errors, path, "data_num must have an integer dtype, found {}".format(data_num.dtype))
        else:
            counts = np.asarray(data_num[...], dtype=np.int64)
            invalid = np.where((counts < 1) | (counts > padded_points))[0]
            if invalid.size:
                add_error(
                    errors,
                    path,
                    "data_num must satisfy 1 <= data_num[i] <= {}; invalid rows {}".format(
                        padded_points, invalid[:10].tolist()
                    ),
                )
            else:
                counts_valid = True

        label_values = None
        if not is_integer_dtype(label.dtype):
            add_error(errors, path, "label must have an integer dtype, found {}".format(label.dtype))
        elif label.ndim == 1 and tuple(label.shape) == (items,):
            label_values = np.asarray(label[...], dtype=np.int64)
        elif label.ndim == 2 and tuple(label.shape) == (items, 1):
            label_values = np.asarray(label[..., 0], dtype=np.int64)
        else:
            add_error(
                errors,
                path,
                "label must be integer rank 1 [items] or rank 2 [items, 1]; found shape {}".format(label.shape),
            )
        if label_values is not None and label_values.size:
            if int(label_values.min()) < 0:
                add_error(errors, path, "label contains a negative item/category id")
            if args.label_count is not None and int(label_values.max()) >= args.label_count:
                add_error(
                    errors,
                    path,
                    "label contains {} but --label-count is {}".format(int(label_values.max()), args.label_count),
                )

        if not is_integer_dtype(label_seg.dtype):
            add_error(errors, path, "label_seg must have an integer dtype, found {}".format(label_seg.dtype))
        elif label_seg.ndim != 2 or tuple(label_seg.shape) != (items, padded_points):
            add_error(
                errors,
                path,
                "label_seg must be integer rank 2 shape [{}, {}], found shape {}".format(
                    items, padded_points, label_seg.shape
                ),
            )
        elif counts_valid:
            for row, values in active_rows(label_seg, counts, items):
                if values.size == 0:
                    add_error(errors, path, "internal error: empty active label_seg row {}".format(row))
                    continue
                values = np.asarray(values)
                if int(values.min()) < 0:
                    add_error(errors, path, "label_seg row {} contains a negative active label".format(row))
                if args.num_class is not None and int(values.max()) >= args.num_class:
                    add_error(
                        errors,
                        path,
                        "label_seg row {} contains {} but --num-class is {}".format(
                            row, int(values.max()), args.num_class
                        ),
                    )

        index_contract = None
        if "indices_split_to_full" in handle:
            mapped = handle["indices_split_to_full"]
            if not is_integer_dtype(mapped.dtype):
                add_error(errors, path, "indices_split_to_full must have an integer dtype, found {}".format(mapped.dtype))
            elif mapped.ndim == 2 and tuple(mapped.shape) == (items, padded_points):
                index_contract = (2, 1)
            elif mapped.ndim == 3 and tuple(mapped.shape[:2]) == (items, padded_points) and mapped.shape[2] == 2:
                index_contract = (3, 2)
            else:
                add_error(
                    errors,
                    path,
                    "indices_split_to_full must be rank 2 [items, padded_points] or rank 3 "
                    "[items, padded_points, 2]; found shape {}".format(mapped.shape),
                )

            if index_contract is not None:
                if reference["index_contract"] is None:
                    reference["index_contract"] = index_contract
                elif reference["index_contract"] != index_contract:
                    add_error(
                        errors,
                        path,
                        "indices_split_to_full contract {} disagrees with earlier files {}".format(
                            index_contract, reference["index_contract"]
                        ),
                    )
                if counts_valid:
                    for row, values in active_rows(mapped, counts, items):
                        values = np.asarray(values)
                        if index_contract[0] == 2:
                            if np.any(values < 0):
                                add_error(errors, path, "indices_split_to_full row {} contains a negative active index".format(row))
                            if args.full_point_count is not None and np.any(values >= args.full_point_count):
                                add_error(
                                    errors,
                                    path,
                                    "indices_split_to_full row {} exceeds --full-point-count {}".format(
                                        row, args.full_point_count
                                    ),
                                )
                        else:
                            if np.any(values < 0):
                                add_error(errors, path, "indices_split_to_full row {} contains a negative active pair".format(row))
                            if args.index_group_count is not None and np.any(values[:, 0] >= args.index_group_count):
                                add_error(
                                    errors,
                                    path,
                                    "indices_split_to_full row {} exceeds --index-group-count {}".format(
                                        row, args.index_group_count
                                    ),
                                )
                            if args.full_point_count is not None and np.any(values[:, 1] >= args.full_point_count):
                                add_error(
                                    errors,
                                    path,
                                    "indices_split_to_full row {} exceeds --full-point-count {} in point-id column".format(
                                        row, args.full_point_count
                                    ),
                                )
        elif reference["index_contract"] is not None:
            add_error(errors, path, "indices_split_to_full is missing but earlier files contain it; do not mix mapping contracts")

        if "indices_split_to_full" in handle and reference["saw_file_without_indices"]:
            add_error(errors, path, "indices_split_to_full is present after a file without it; do not mix mapping contracts")
        if "indices_split_to_full" not in handle:
            reference["saw_file_without_indices"] = True

        return errors, (items, padded_points, data_dim, index_contract)


def validate_args(parser, args):
    checks = (
        (args.data_dim, "--data-dim", 3),
        (args.num_class, "--num-class", 1),
        (args.label_count, "--label-count", 1),
        (args.full_point_count, "--full-point-count", 1),
        (args.index_group_count, "--index-group-count", 1),
        (args.max_files, "--max-files", 1),
    )
    for value, name, minimum in checks:
        if value is not None and value < minimum:
            parser.error("{} must be at least {}".format(name, minimum))
    if args.h5_files is not None and not args.h5_files:
        parser.error("--h5 must be supplied at least once")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(parser, args)

    try:
        entries = resolve_entries(args.filelist) if args.filelist else explicit_entries(args.h5_files)
    except (OSError, ValueError) as exc:
        print("ERROR: {}".format(exc), file=sys.stderr)
        return 2

    if args.max_files is not None:
        entries = entries[: args.max_files]
    if not entries:
        print("ERROR: no HDF5 paths were supplied", file=sys.stderr)
        return 2

    reference = {
        "data_shape": None,
        "index_contract": None,
        "saw_file_without_indices": False,
    }
    errors = []
    checked = 0
    samples = 0
    for path, line_number in entries:
        checked += 1
        if line_number is not None and not path.is_file():
            errors.append("{} line {}: HDF5 path does not exist: {}".format(args.filelist, line_number, path))
            continue
        file_errors, summary = validate_file(path, args, reference)
        if line_number is not None and file_errors:
            file_errors = ["{} line {}: {}".format(args.filelist, line_number, message) for message in file_errors]
        errors.extend(file_errors)
        if summary is not None:
            samples += summary[0]

    if errors:
        for error in errors:
            print("ERROR: {}".format(error), file=sys.stderr)
        print("FAILED: {} HDF5 file(s) checked, {} error(s)".format(checked, len(errors)), file=sys.stderr)
        return 2

    index_text = "none" if reference["index_contract"] is None else "rank {}".format(reference["index_contract"][0])
    print(
        "OK: {} HDF5 file(s), {} samples; padded_points/data_dim={} / {}; indices_split_to_full={}".format(
            checked,
            samples,
            reference["data_shape"][0],
            reference["data_shape"][1],
            index_text,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
