#!/usr/bin/env python3
"""Validate a CSV before using TFLearn's data_utils.load_csv.

This script performs no downloads and does not train a model. It mirrors the
column semantics that matter for tflearn.data_utils.load_csv: target_column is
selected from the original CSV row, then columns_to_ignore are interpreted as
original CSV indices and adjusted after target removal.
"""
from __future__ import print_function

import argparse
import csv
import os
import sys
from collections import Counter, defaultdict


def parse_int_list(value):
    if value is None or value == "":
        return []
    parts = []
    for chunk in value.replace(";", ",").split(","):
        chunk = chunk.strip()
        if chunk:
            try:
                parts.append(int(chunk))
            except ValueError:
                raise argparse.ArgumentTypeError(
                    "ignore columns must be comma-separated integers")
    return parts


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Validate a tabular CSV for TFLearn load_csv-style workflows. "
            "Reports target handling, inferred feature columns, label classes, "
            "row counts, and common numeric conversion issues. Performs no downloads."
        )
    )
    parser.add_argument("--csv", required=True, help="Path to the CSV file to validate.")
    parser.add_argument(
        "--target-column",
        type=int,
        default=-1,
        help="Original CSV column index to use as target. Negative indices are allowed; default -1.",
    )
    parser.add_argument(
        "--ignore-columns",
        type=parse_int_list,
        default=[],
        help="Comma-separated original CSV column indices to ignore as features, e.g. 2,7.",
    )
    header_group = parser.add_mutually_exclusive_group()
    header_group.add_argument(
        "--has-header",
        dest="has_header",
        action="store_true",
        default=True,
        help="Treat the first CSV row as a header row (default).",
    )
    header_group.add_argument(
        "--no-header",
        dest="has_header",
        action="store_false",
        help="Treat the first CSV row as data.",
    )
    parser.add_argument(
        "--categorical-labels",
        action="store_true",
        help="Validate labels for TFLearn categorical one-hot conversion.",
    )
    parser.add_argument(
        "--n-classes",
        type=int,
        default=None,
        help="Expected number of classes when --categorical-labels is set.",
    )
    return parser


def require_tflearn_data_utils():
    """Import tflearn.data_utils after argparse so --help works everywhere."""
    try:
        from tflearn import data_utils  # noqa: F401
        return data_utils
    except Exception as exc:
        print(
            "ERROR: TFLearn could not be imported. Run this validator in the "
            "same legacy TFLearn/TensorFlow 1.x environment that will run the "
            "data workflow. Import error: {}: {}".format(type(exc).__name__, exc),
            file=sys.stderr,
        )
        return None


def normalize_index(index, width, field_name):
    original = index
    if index < 0:
        index = width + index
    if index < 0 or index >= width:
        raise ValueError(
            "{} {} resolves to {}, outside row width {}".format(
                field_name, original, index, width
            )
        )
    return index


def adjusted_ignore_indices(ignore_columns, target_column, width):
    """Return feature-row ignore indices using TFLearn load_csv semantics."""
    adjusted = []
    original_to_adjusted = []
    for original in ignore_columns:
        idx = normalize_index(original, width, "ignore column")
        if idx == target_column:
            original_to_adjusted.append((idx, None, "target-column"))
            continue
        adj = idx - 1 if idx > target_column else idx
        adjusted.append(adj)
        original_to_adjusted.append((idx, adj, None))
    return adjusted, original_to_adjusted


def is_floatish(value):
    if value is None:
        return False
    text = value.strip()
    if text == "":
        return False
    try:
        float(text)
        return True
    except ValueError:
        return False


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.categorical_labels and args.n_classes is None:
        parser.error("--n-classes is required when --categorical-labels is set")
    if args.n_classes is not None and args.n_classes <= 0:
        parser.error("--n-classes must be a positive integer")

    if not os.path.exists(args.csv):
        print("ERROR: CSV file does not exist: {}".format(args.csv), file=sys.stderr)
        return 2
    if not os.path.isfile(args.csv):
        print("ERROR: CSV path is not a regular file: {}".format(args.csv), file=sys.stderr)
        return 2

    data_utils = require_tflearn_data_utils()
    if data_utils is None:
        return 2

    try:
        with open(args.csv, "r", newline="") as handle:
            rows = list(csv.reader(handle))
    except TypeError:
        # Python 2 fallback, harmless for legacy environments.
        with open(args.csv, "r") as handle:
            rows = list(csv.reader(handle))
    except Exception as exc:
        print("ERROR: Could not read CSV: {}".format(exc), file=sys.stderr)
        return 2

    if not rows:
        print("ERROR: CSV is empty: {}".format(args.csv), file=sys.stderr)
        return 1

    header = None
    data_rows = rows
    if args.has_header:
        header = rows[0]
        data_rows = rows[1:]
        if not header:
            print("ERROR: Header row is empty.", file=sys.stderr)
            return 1

    if not data_rows:
        print("ERROR: CSV has no data rows after header handling.", file=sys.stderr)
        return 1

    widths = Counter(len(row) for row in data_rows)
    expected_width = len(header) if header is not None else max(widths, key=widths.get)
    inconsistent = {width: count for width, count in widths.items() if width != expected_width}

    try:
        target_idx = normalize_index(args.target_column, expected_width, "target column")
        feature_ignore_adjusted, ignore_map = adjusted_ignore_indices(
            args.ignore_columns, target_idx, expected_width
        )
    except ValueError as exc:
        print("ERROR: {}".format(exc), file=sys.stderr)
        return 1

    original_names = header if header is not None else ["column_{}".format(i) for i in range(expected_width)]
    # Build the original-to-feature map by simulating pop(target), then ignore.
    post_target_originals = [i for i in range(expected_width) if i != target_idx]
    feature_columns = []
    ignored_originals = set()
    for orig, adj, reason in ignore_map:
        if reason == "target-column":
            ignored_originals.add(orig)
        elif adj is not None:
            ignored_originals.add(orig)
    for post_target_pos, original_idx in enumerate(post_target_originals):
        if post_target_pos not in feature_ignore_adjusted:
            name = original_names[original_idx] if original_idx < len(original_names) else "column_{}".format(original_idx)
            final_feature_pos = len(feature_columns)
            feature_columns.append((original_idx, post_target_pos, final_feature_pos, name))

    target_values = []
    conversion_issues = defaultdict(list)
    blank_counts = Counter()
    short_or_long_rows = []
    usable_rows = 0

    for row_number, row in enumerate(data_rows, start=2 if args.has_header else 1):
        if len(row) != expected_width:
            short_or_long_rows.append((row_number, len(row)))
            # Continue best-effort for rows wide enough to inspect.
        if len(row) <= target_idx:
            continue
        target_values.append(row[target_idx])
        usable_rows += 1
        for original_idx, post_target_pos, final_feature_pos, name in feature_columns:
            if original_idx >= len(row):
                conversion_issues[original_idx].append((row_number, "<missing>"))
                continue
            value = row[original_idx]
            if value.strip() == "":
                blank_counts[original_idx] += 1
                conversion_issues[original_idx].append((row_number, "<blank>"))
            elif not is_floatish(value):
                if len(conversion_issues[original_idx]) < 5:
                    conversion_issues[original_idx].append((row_number, value))
                else:
                    conversion_issues[original_idx].append((row_number, "..."))

    label_counts = Counter(target_values)
    exit_code = 0
    warning = False

    print("TFLearn tabular CSV validation")
    print("csv: {}".format(args.csv))
    print("has_header: {}".format(args.has_header))
    print("rows: {} data rows ({} usable target rows)".format(len(data_rows), usable_rows))
    print("columns: {}".format(expected_width))
    if inconsistent:
        exit_code = 1
        print("WARNING: inconsistent row widths: {}".format(dict(sorted(inconsistent.items()))))
    print(
        "target column: original index {} ({})".format(
            target_idx, original_names[target_idx] if target_idx < len(original_names) else "column_{}".format(target_idx)
        )
    )
    print("ignore columns: {}".format(
        ", ".join(str(i) for i in args.ignore_columns) if args.ignore_columns else "<none>"
    ))
    if ignore_map:
        print("ignore mapping after target removal:")
        for orig, adj, reason in ignore_map:
            name = original_names[orig] if orig < len(original_names) else "column_{}".format(orig)
            if reason == "target-column":
                print("  original {} ({}) is the target; not a feature".format(orig, name))
            else:
                print("  original {} ({}) -> post-target feature index {}".format(orig, name, adj))

    print("inferred feature columns (original_index -> final_feature_index; post-target_index: name):")
    for original_idx, post_target_pos, final_feature_pos, name in feature_columns:
        print("  {} -> {}; post-target {}: {}".format(original_idx, final_feature_pos, post_target_pos, name))
    print("feature_count: {}".format(len(feature_columns)))

    print("label classes (raw counts):")
    for label, count in sorted(label_counts.items(), key=lambda item: item[0]):
        print("  {!r}: {}".format(label, count))

    if args.categorical_labels:
        print("categorical_labels: true")
        print("n_classes: {}".format(args.n_classes))
        bad_labels = []
        y_ids = []
        for value in target_values:
            try:
                y_id = int(value)
            except Exception:
                bad_labels.append((value, "not an integer class id"))
                continue
            y_ids.append(y_id)
            if y_id < 0 or y_id >= args.n_classes:
                bad_labels.append((value, "outside [0, {}]".format(args.n_classes - 1)))
        if bad_labels:
            exit_code = 1
            print("ERROR: labels are not valid for requested one-hot width:")
            for value, reason in bad_labels[:10]:
                print("  {!r}: {}".format(value, reason))
            if len(bad_labels) > 10:
                print("  ... {} more".format(len(bad_labels) - 10))
        else:
            try:
                one_hot = data_utils.to_categorical(y_ids, args.n_classes)
                print("one_hot_shape: {}".format(tuple(one_hot.shape)))
            except Exception as exc:
                exit_code = 1
                print("ERROR: tflearn.data_utils.to_categorical failed: {}".format(exc))
    else:
        print("categorical_labels: false")

    if short_or_long_rows:
        exit_code = 1
        print("row width issues:")
        for row_number, width in short_or_long_rows[:10]:
            print("  row {} has {} columns (expected {})".format(row_number, width, expected_width))
        if len(short_or_long_rows) > 10:
            print("  ... {} more".format(len(short_or_long_rows) - 10))

    if conversion_issues:
        warning = True
        print("feature conversion issues (remaining features that are not directly float-compatible):")
        for original_idx in sorted(conversion_issues):
            name = original_names[original_idx] if original_idx < len(original_names) else "column_{}".format(original_idx)
            samples = conversion_issues[original_idx]
            # Count all stored issues except repeated ellipsis placeholders are still useful signals.
            unique_samples = []
            seen = set()
            for item in samples:
                if item not in seen:
                    unique_samples.append(item)
                    seen.add(item)
            print("  original {} ({}): {} issue(s); examples: {}".format(
                original_idx,
                name,
                len(samples),
                ", ".join("row {}={!r}".format(r, v) for r, v in unique_samples[:5]),
            ))
        print("ACTION: drop, fill, or encode these columns before np.asarray(..., dtype=np.float32).")
    else:
        print("feature conversion issues: none detected for inferred features")

    if blank_counts:
        warning = True
        print("blank feature values:")
        for original_idx, count in sorted(blank_counts.items()):
            name = original_names[original_idx] if original_idx < len(original_names) else "column_{}".format(original_idx)
            print("  original {} ({}): {} blank value(s)".format(original_idx, name, count))

    if len(feature_columns) == 0:
        exit_code = 1
        print("ERROR: no feature columns remain after target and ignore handling.")

    if exit_code == 0 and not warning:
        print("status: OK - CSV structure is compatible with the reported TFLearn load_csv-style plan.")
    elif exit_code == 0:
        print("status: CHECK - CSV can be loaded, but encode/drop/fill reported feature values before converting to numeric arrays.")
    else:
        print("status: CHECK - resolve the warnings/errors above before fitting a TFLearn model.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
