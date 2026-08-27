#!/usr/bin/env python3
"""Bounded CPU persistence and exact-vs-IVF evaluation smoke for Faiss.

The script creates all data in memory, uses a temporary directory for the file
round trip, and never downloads data or assumes a repository checkout.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

import numpy as np


def checked_search(index, xq: np.ndarray, k: int, metric: int):
    """Reject evaluation-contract mistakes before calling the Faiss wrapper."""
    xq = np.asarray(xq)
    if xq.ndim != 2 or xq.shape[1] != int(index.d):
        raise ValueError(
            f"query shape {xq.shape} does not match index dimension {index.d}"
        )
    if int(index.metric_type) != int(metric):
        raise ValueError(
            f"metric mismatch: index={index.metric_type}, expected={metric}"
        )
    xq = np.ascontiguousarray(xq, dtype="float32")
    return index.search(xq, int(k))


def intersection_count(result: np.ndarray, truth: np.ndarray) -> int:
    """Count per-query ID intersections, ignoring Faiss's -1 sentinel."""
    if result.shape != truth.shape:
        raise ValueError(f"result shape {result.shape} != truth {truth.shape}")
    hits = 0
    for row, gt_row in zip(result, truth):
        got = {int(v) for v in row if int(v) != -1}
        expected = {int(v) for v in gt_row if int(v) != -1}
        hits += len(got & expected)
    return hits


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic, download-free Faiss byte/file round trip "
            "and compare a tiny IVF index with exact ground truth."
        )
    )
    parser.add_argument("--dimension", type=int, default=8, help="vector dimension")
    parser.add_argument("--train-size", type=int, default=320, help="training rows")
    parser.add_argument("--database-size", type=int, default=96, help="database rows")
    parser.add_argument("--query-size", type=int, default=16, help="query rows")
    parser.add_argument("--nlist", type=int, default=8, help="IVF list count")
    parser.add_argument("--nprobe", type=int, default=2, help="IVF lists searched")
    parser.add_argument("--k", type=int, default=5, help="neighbors per query")
    parser.add_argument("--seed", type=int, default=123, help="NumPy RNG seed")
    parser.add_argument(
        "--metric",
        choices=("l2", "ip"),
        default="l2",
        help="distance metric; IP uses normalized vectors",
    )
    parser.add_argument(
        "--min-recall",
        type=float,
        default=0.0,
        help="optional recall@k gate in [0, 1] (default: report only)",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    for name in (
        "dimension",
        "train_size",
        "database_size",
        "query_size",
        "nlist",
        "nprobe",
        "k",
    ):
        if getattr(args, name) <= 0:
            raise ValueError(f"--{name.replace('_', '-')} must be positive")
    if args.nlist > args.train_size or args.nlist > args.database_size:
        raise ValueError("nlist must not exceed training or database rows")
    if args.k > args.database_size:
        raise ValueError("k must not exceed database rows")
    if not 0.0 <= args.min_recall <= 1.0:
        raise ValueError("--min-recall must be between 0 and 1")


def main() -> int:
    args = parse_args()
    validate_args(args)

    # Import only after argument validation so --help remains useful even when
    # the optional package is not installed.
    import faiss

    metric = faiss.METRIC_L2 if args.metric == "l2" else faiss.METRIC_INNER_PRODUCT
    rng = np.random.default_rng(args.seed)
    xt = rng.standard_normal((args.train_size, args.dimension)).astype("float32")
    xb = rng.standard_normal((args.database_size, args.dimension)).astype("float32")
    xq = rng.standard_normal((args.query_size, args.dimension)).astype("float32")
    if metric == faiss.METRIC_INNER_PRODUCT:
        faiss.normalize_L2(xt)
        faiss.normalize_L2(xb)
        faiss.normalize_L2(xq)
    xt = np.ascontiguousarray(xt, dtype="float32")
    xb = np.ascontiguousarray(xb, dtype="float32")
    xq = np.ascontiguousarray(xq, dtype="float32")

    exact = faiss.IndexFlat(args.dimension, metric)
    exact.add(xb)
    gt_D, gt_I = checked_search(exact, xq, args.k, metric)

    quantizer = faiss.IndexFlat(args.dimension, metric)
    approximate = faiss.IndexIVFFlat(
        quantizer, args.dimension, args.nlist, metric
    )
    approximate.train(xt)
    approximate.add(xb)
    approximate.nprobe = min(args.nprobe, args.nlist)
    approx_D, approx_I = checked_search(approximate, xq, args.k, metric)

    hits = intersection_count(approx_I, gt_I)
    denominator = float(args.query_size * args.k)
    recall = hits / denominator
    returned = int(np.count_nonzero(approx_I != -1))
    precision = hits / float(returned) if returned else 1.0
    if recall < args.min_recall:
        raise AssertionError(
            f"recall@{args.k}={recall:.6f} is below --min-recall={args.min_recall:.6f}"
        )

    # Bytes and clone must preserve the tiny candidate's observable result.
    payload = np.asarray(faiss.serialize_index(approximate), dtype=np.uint8)
    if payload.ndim != 1 or payload.size == 0:
        raise AssertionError("serialize_index did not return a non-empty uint8 vector")
    from_bytes = faiss.deserialize_index(payload)
    bytes_D, bytes_I = checked_search(from_bytes, xq, args.k, metric)
    np.testing.assert_array_equal(approx_I, bytes_I)
    np.testing.assert_array_equal(approx_D, bytes_D)

    cloned = faiss.clone_index(approximate)
    clone_D, clone_I = checked_search(cloned, xq, args.k, metric)
    np.testing.assert_array_equal(approx_I, clone_I)
    np.testing.assert_array_equal(approx_D, clone_D)

    with tempfile.TemporaryDirectory(prefix="faiss-persistence-smoke-") as temp_dir:
        target = Path(temp_dir) / "candidate.index"
        temporary = Path(temp_dir) / "candidate.index.tmp"
        faiss.write_index(approximate, str(temporary))
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise AssertionError("write_index did not create a non-empty file")
        os.replace(temporary, target)
        from_file = faiss.read_index(str(target))
        file_D, file_I = checked_search(from_file, xq, args.k, metric)
        np.testing.assert_array_equal(approx_I, file_I)
        np.testing.assert_array_equal(approx_D, file_D)
        file_bytes = target.stat().st_size

    # These expected failures make metric and shape mismatches reproducible
    # without depending on the wrapper's platform-specific exception text.
    wrong_metric = (
        faiss.METRIC_INNER_PRODUCT
        if metric == faiss.METRIC_L2
        else faiss.METRIC_L2
    )
    metric_rejected = False
    try:
        checked_search(exact, xq, args.k, wrong_metric)
    except ValueError:
        metric_rejected = True
    shape_rejected = False
    try:
        checked_search(exact, xq[:, :-1], args.k, metric)
    except ValueError:
        shape_rejected = True
    if not metric_rejected or not shape_rejected:
        raise AssertionError("contract checks failed to reject bad metric/shape")

    result = {
        "status": "ok",
        "faiss_version": getattr(faiss, "__version__", "unknown"),
        "metric": args.metric,
        "dimension": args.dimension,
        "train_size": args.train_size,
        "database_size": args.database_size,
        "query_size": args.query_size,
        "k": args.k,
        "nlist": args.nlist,
        "nprobe": approximate.nprobe,
        "serialized_bytes": int(payload.nbytes),
        "file_bytes": int(file_bytes),
        "recall_at_k": recall,
        "precision_at_k": precision,
        "metric_mismatch_rejected": metric_rejected,
        "shape_mismatch_rejected": shape_rejected,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
