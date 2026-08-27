#!/usr/bin/env python3
"""Smoke test geemap's local scikit-learn tree-to-EE-string conversion.

The help path intentionally imports only the Python standard library. The smoke
run imports scikit-learn lazily; if scikit-learn is unavailable, the script
reports a clear optional-dependency skip instead of failing obscurely.
"""

from __future__ import annotations

import argparse
import importlib.util
import multiprocessing
from pathlib import Path
import sys
from typing import Sequence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Train a tiny RandomForestClassifier and convert it to geemap "
            "Earth Engine decision-tree strings when scikit-learn is installed."
        )
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help="Optional file path for ml.trees_to_csv output.",
    )
    parser.add_argument(
        "--output-mode",
        default="CLASSIFICATION",
        choices=["INFER", "CLASSIFICATION", "PROBABILITY"],
        help="Output mode passed to rf_to_strings/tree conversion.",
    )
    parser.add_argument(
        "--processes",
        type=int,
        default=1,
        help="Worker process count for rf_to_strings when the host has more than one CPU.",
    )
    parser.add_argument(
        "--require-sklearn",
        action="store_true",
        help="Exit non-zero instead of reporting SKIP when scikit-learn is missing.",
    )
    parser.add_argument(
        "--preview-lines",
        type=int,
        default=4,
        help="Number of lines from the first converted tree to print.",
    )
    return parser


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _safe_process_count(requested: int) -> int:
    """Avoid geemap's multiprocessing edge case on single-core hosts."""
    requested = max(1, requested)
    try:
        cpu_count = multiprocessing.cpu_count()
    except NotImplementedError:
        cpu_count = 2
    if cpu_count <= 1:
        return 1
    return min(requested, cpu_count - 1)


def run_smoke(args: argparse.Namespace) -> int:
    if not _module_available("sklearn"):
        msg = (
            "SKIP: scikit-learn is not installed. Install scikit-learn to run "
            "the local RandomForestClassifier conversion smoke."
        )
        print(msg, file=sys.stderr)
        return 2 if args.require_sklearn else 0

    try:
        from sklearn.ensemble import RandomForestClassifier
        import geemap.ml as ml
    except Exception as exc:  # pragma: no cover - environment diagnostic path.
        print(f"ERROR: failed to import smoke dependencies: {exc}", file=sys.stderr)
        return 1

    X = [
        [0.05, 0.10],
        [0.10, 0.80],
        [0.80, 0.15],
        [0.90, 0.85],
        [0.15, 0.25],
        [0.75, 0.70],
    ]
    y = [0, 1, 0, 1, 0, 1]
    feature_names = ["red", "nir"]

    rf = RandomForestClassifier(n_estimators=3, max_depth=2, random_state=42)
    rf.fit(X, y)

    processes = _safe_process_count(args.processes)
    try:
        if multiprocessing.cpu_count() <= 1:
            # geemap.rf_to_strings currently caps processes to cpu_count - 1 when the
            # request is >= cpu_count, which would be zero on a single-core host.
            trees = [
                ml.tree_to_string(
                    estimator,
                    feature_names=feature_names,
                    labels=rf.classes_,
                    output_mode=args.output_mode,
                )
                for estimator in rf.estimators_
            ]
            conversion_path = "tree_to_string sequential fallback"
        else:
            trees = ml.rf_to_strings(
                rf,
                feature_names=feature_names,
                processes=processes,
                output_mode=args.output_mode,
            )
            conversion_path = f"rf_to_strings processes={processes}"
    except Exception as exc:
        print(f"ERROR: geemap ML conversion failed: {exc}", file=sys.stderr)
        return 1

    if not trees or not all(isinstance(tree, str) and tree.startswith("1) root") for tree in trees):
        print("ERROR: conversion did not return valid Earth Engine tree strings.", file=sys.stderr)
        return 1

    print(f"OK: converted {len(trees)} trees using {conversion_path}.")
    preview = "\n".join(trees[0].splitlines()[: max(0, args.preview_lines)])
    if preview:
        print("First tree preview:")
        print(preview)

    if args.output_csv is not None:
        try:
            args.output_csv.parent.mkdir(parents=True, exist_ok=True)
            ml.trees_to_csv(trees, str(args.output_csv))
            if not args.output_csv.exists():
                print(f"ERROR: expected CSV was not created: {args.output_csv}", file=sys.stderr)
                return 1
            print(f"OK: wrote tree CSV to {args.output_csv}")
        except Exception as exc:
            print(f"ERROR: writing tree CSV failed: {exc}", file=sys.stderr)
            return 1

    print(
        "NOTE: This smoke does not contact Earth Engine. Use strings_to_classifier, "
        "csv_to_classifier, or fc_to_classifier in an initialized Earth Engine session "
        "when a real classifier object is needed."
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_smoke(args)


if __name__ == "__main__":
    raise SystemExit(main())
