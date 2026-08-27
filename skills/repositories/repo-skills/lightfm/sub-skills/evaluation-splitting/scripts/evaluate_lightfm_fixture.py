#!/usr/bin/env python3
"""Tiny deterministic LightFM evaluation fixture.

The script trains a small CPU LightFM model, computes ranking metrics against a
held-out sparse test matrix, validates a random split, and can intentionally
show the train/test intersection error. It performs no network access and does
not read repository files.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any, Iterable


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Train a tiny LightFM model and compute leakage-safe ranking "
            "metrics on an in-memory sparse fixture."
        )
    )
    parser.add_argument("--seed", type=int, default=7, help="Random seed for model and split fixture.")
    parser.add_argument("--epochs", type=int, default=20, help="Training epochs for the tiny model.")
    parser.add_argument("--k", type=int, default=3, help="Top-k cutoff for precision and recall.")
    parser.add_argument(
        "--loss",
        choices=("logistic", "bpr", "warp", "warp-kos"),
        default="warp",
        help="LightFM loss used for the tiny model.",
    )
    parser.add_argument(
        "--no-components",
        type=int,
        default=4,
        help="Latent components for the tiny model.",
    )
    parser.add_argument(
        "--num-threads",
        type=int,
        default=1,
        help="CPU threads for fit/evaluation; must be at least 1.",
    )
    parser.add_argument(
        "--test-percentage",
        type=float,
        default=0.25,
        help="Fraction used when demonstrating random_train_test_split.",
    )
    parser.add_argument(
        "--preserve-rows",
        action="store_true",
        help="Return metric arrays aligned to all fixture users.",
    )
    parser.add_argument(
        "--demonstrate-intersection",
        action="store_true",
        help="Intentionally score overlapping train/test matrices and report the expected ValueError.",
    )
    return parser


def _json_float(value: Any) -> Any:
    value = float(value)
    if math.isfinite(value):
        return value
    if math.isnan(value):
        return "nan"
    return "inf" if value > 0 else "-inf"


def _summary(values: Iterable[Any], np: Any) -> dict[str, Any]:
    arr = np.asarray(values, dtype=np.float64)
    finite_mask = np.isfinite(arr)
    return {
        "shape": list(arr.shape),
        "values": [_json_float(x) for x in arr.tolist()],
        "mean": None if arr.size == 0 else _json_float(np.nanmean(arr)),
        "all_finite": bool(finite_mask.all()),
    }


def _build_fixture(np: Any, sp: Any) -> tuple[Any, Any, Any]:
    """Return deterministic train, test, and combined sparse matrices."""
    shape = (6, 8)

    train_rows = np.array([0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5], dtype=np.int32)
    train_cols = np.array([0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6], dtype=np.int32)
    test_rows = np.array([0, 1, 2, 3, 4, 5], dtype=np.int32)
    test_cols = np.array([2, 3, 4, 5, 6, 7], dtype=np.int32)

    train = sp.coo_matrix(
        (np.ones(train_rows.size, dtype=np.float32), (train_rows, train_cols)),
        shape=shape,
        dtype=np.float32,
    )
    test = sp.coo_matrix(
        (np.ones(test_rows.size, dtype=np.float32), (test_rows, test_cols)),
        shape=shape,
        dtype=np.float32,
    )
    combined = (train + test).tocoo()
    combined.sum_duplicates()
    return train, test, combined


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.epochs < 0:
        parser.error("--epochs must be non-negative")
    if args.k < 1:
        parser.error("--k must be at least 1")
    if args.no_components < 1:
        parser.error("--no-components must be at least 1")
    if args.num_threads < 1:
        parser.error("--num-threads must be at least 1")
    if not 0.0 <= args.test_percentage <= 1.0:
        parser.error("--test-percentage must be between 0.0 and 1.0")

    try:
        import numpy as np
        import scipy.sparse as sp
        import lightfm as lightfm_package
        from lightfm import LightFM
        from lightfm.cross_validation import random_train_test_split
        from lightfm.evaluation import auc_score, precision_at_k, recall_at_k, reciprocal_rank
    except Exception as exc:  # pragma: no cover - exercised by missing installs.
        print(
            "Could not import LightFM and its runtime dependencies. "
            "Install a working lightfm package before running the fixture. "
            f"Original error: {exc}",
            file=sys.stderr,
        )
        return 2

    train, test, combined = _build_fixture(np, sp)
    train_csr = train.tocsr()
    test_csr = test.tocsr()
    overlap = int(train_csr.multiply(test_csr).nnz)
    if overlap:
        print(f"Fixture bug: train/test overlap contains {overlap} entries", file=sys.stderr)
        return 2

    random_train, random_test = random_train_test_split(
        combined,
        test_percentage=args.test_percentage,
        random_state=args.seed,
    )
    random_overlap = int(random_train.tocsr().multiply(random_test.tocsr()).nnz)

    model = LightFM(
        no_components=args.no_components,
        loss=args.loss,
        random_state=args.seed,
    )
    model.fit(train, epochs=args.epochs, num_threads=args.num_threads)

    metric_kwargs = dict(
        train_interactions=train,
        preserve_rows=args.preserve_rows,
        num_threads=args.num_threads,
        check_intersections=True,
    )
    metrics = {
        f"precision@{args.k}": precision_at_k(model, test, k=args.k, **metric_kwargs),
        f"recall@{args.k}": recall_at_k(model, test, k=args.k, **metric_kwargs),
        "auc": auc_score(model, test, **metric_kwargs),
        "reciprocal_rank": reciprocal_rank(model, test, **metric_kwargs),
    }
    ranks = model.predict_rank(
        test,
        train_interactions=train,
        num_threads=args.num_threads,
        check_intersections=True,
    )

    metric_summaries = {name: _summary(values, np) for name, values in metrics.items()}
    nonfinite_metrics = [
        name for name, summary in metric_summaries.items() if not summary["all_finite"]
    ]

    report: dict[str, Any] = {
        "lightfm_version": getattr(lightfm_package, "__version__", "unknown"),
        "fixture": {
            "shape": list(train.shape),
            "train_nnz": int(train.nnz),
            "test_nnz": int(test.nnz),
            "fixed_split_overlap_nnz": overlap,
            "users_with_test_positives": int((test_csr.getnnz(axis=1) > 0).sum()),
        },
        "random_split_demo": {
            "source_nnz": int(combined.nnz),
            "train_nnz": int(random_train.nnz),
            "test_nnz": int(random_test.nnz),
            "overlap_nnz": random_overlap,
            "test_percentage_requested": args.test_percentage,
        },
        "metric_options": {
            "k": args.k,
            "preserve_rows": args.preserve_rows,
            "num_threads": args.num_threads,
            "check_intersections": True,
        },
        "metrics": metric_summaries,
        "predict_rank": {
            "shape": list(ranks.shape),
            "nnz": int(ranks.nnz),
            "rank_values_for_test_entries": [_json_float(x) for x in ranks.data.tolist()],
            "top_k_hits": int((ranks.data < args.k).sum()),
        },
        "checks": {
            "fixed_split_disjoint": overlap == 0,
            "random_split_disjoint": random_overlap == 0,
            "metrics_all_finite": not nonfinite_metrics,
            "nonfinite_metrics": nonfinite_metrics,
        },
    }

    if args.demonstrate_intersection:
        try:
            precision_at_k(
                model,
                train,
                train_interactions=train,
                k=args.k,
                num_threads=args.num_threads,
                check_intersections=True,
            )
        except ValueError as exc:
            report["intersection_demo"] = {
                "expected_error_raised": True,
                "message": str(exc),
            }
        else:
            report["intersection_demo"] = {
                "expected_error_raised": False,
                "message": "Expected an intersection ValueError, but no error was raised.",
            }

    print(json.dumps(report, indent=2, sort_keys=True))

    if nonfinite_metrics:
        return 1
    if args.demonstrate_intersection and not report["intersection_demo"]["expected_error_raised"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
