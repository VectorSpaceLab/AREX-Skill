#!/usr/bin/env python3
"""Deterministic, offline CPU smoke checks for Faiss dense search indexes."""

from __future__ import annotations

import argparse
import sys
from typing import Iterable

import numpy as np


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build tiny deterministic Flat, IVF-Flat, and HNSW cases; "
            "validate input/result contracts without downloads."
        )
    )
    parser.add_argument(
        "--case",
        choices=("all", "flat", "ivf", "hnsw"),
        default="all",
        help="case to run (default: all)",
    )
    parser.add_argument("--dim", type=int, default=8, help="vector dimension")
    parser.add_argument(
        "--database-size", type=int, default=384, dest="database_size",
        help="number of database vectors",
    )
    parser.add_argument(
        "--queries", type=int, default=8,
        help="number of query vectors (at most database-size)",
    )
    parser.add_argument("--k", type=int, default=4, help="top-k result count")
    parser.add_argument(
        "--nlist", type=int, default=8,
        help="IVF coarse-list count (must not exceed database-size)",
    )
    parser.add_argument(
        "--nprobe", type=int, default=2,
        help="IVF lists to probe (1 through nlist)",
    )
    parser.add_argument("--hnsw-m", type=int, default=16, dest="hnsw_m")
    parser.add_argument(
        "--ef-search", type=int, default=32, dest="ef_search",
        help="HNSW search expansion (at least k)",
    )
    parser.add_argument(
        "--threads", type=int, default=1,
        help="temporary Faiss OpenMP thread count (positive)",
    )
    return parser


def _validate_args(args: argparse.Namespace) -> None:
    positive = {
        "dim": args.dim,
        "database-size": args.database_size,
        "queries": args.queries,
        "k": args.k,
        "nlist": args.nlist,
        "nprobe": args.nprobe,
        "hnsw-m": args.hnsw_m,
        "ef-search": args.ef_search,
        "threads": args.threads,
    }
    for name, value in positive.items():
        if value <= 0:
            raise ValueError(f"--{name} must be positive (got {value})")
    if args.queries > args.database_size:
        raise ValueError("--queries must not exceed --database-size")
    if args.nlist > args.database_size:
        raise ValueError("--nlist must not exceed --database-size")
    if args.nprobe > args.nlist:
        raise ValueError("--nprobe must be no greater than --nlist")
    if args.ef_search < args.k:
        raise ValueError("--ef-search must be at least --k")


def _data(args: argparse.Namespace) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.RandomState(1234)
    xb = np.ascontiguousarray(
        rng.random_sample((args.database_size, args.dim)).astype("float32")
    )
    xq = np.ascontiguousarray(xb[: args.queries].copy())
    if xb.ndim != 2 or xq.ndim != 2 or xb.shape[1] != xq.shape[1]:
        raise AssertionError("generated arrays violate the (n, d) contract")
    if xb.dtype != np.float32 or not xb.flags.c_contiguous:
        raise AssertionError("generated database is not contiguous float32")
    return xb, xq


def _check_results(
    name: str,
    distances: np.ndarray,
    labels: np.ndarray,
    nq: int,
    k: int,
) -> None:
    if distances.shape != (nq, k) or labels.shape != (nq, k):
        raise AssertionError(
            f"{name}: expected result shapes {(nq, k)}, "
            f"got {distances.shape} and {labels.shape}"
        )
    if distances.dtype != np.float32 or labels.dtype != np.int64:
        raise AssertionError(
            f"{name}: expected float32/int64 results, "
            f"got {distances.dtype}/{labels.dtype}"
        )
    if np.any(labels[:, 0] < 0):
        raise AssertionError(f"{name}: a present query has no nearest label")


def _check_sentinels(faiss: object, xb: np.ndarray, xq: np.ndarray) -> None:
    index = faiss.IndexFlatL2(xb.shape[1])
    index.add(xb[: max(1, min(3, xb.shape[0]))])
    requested = index.ntotal + 2
    distances, labels = index.search(xq[:1], requested)
    if labels.shape != (1, requested) or not np.all(labels[0, -2:] == -1):
        raise AssertionError("Flat search did not return -1 missing-result labels")
    if not np.all(distances[0, -2:] >= np.finfo("float32").max):
        raise AssertionError("Flat search missing-result distance sentinel changed")


def _run_flat(faiss: object, xb: np.ndarray, xq: np.ndarray, k: int) -> None:
    index = faiss.IndexFlatL2(xb.shape[1])
    if not index.is_trained:
        raise AssertionError("Flat index should be trained immediately")
    index.add(xb)
    if index.ntotal != xb.shape[0]:
        raise AssertionError("Flat ntotal does not match added vectors")
    distances, labels = index.search(xq, k)
    _check_results("Flat", distances, labels, xq.shape[0], k)
    if not np.array_equal(labels[:, 0], np.arange(xq.shape[0])):
        raise AssertionError("Flat self-neighbor sanity check failed")


def _run_ivf(
    faiss: object,
    xb: np.ndarray,
    xq: np.ndarray,
    k: int,
    nlist: int,
    nprobe: int,
) -> None:
    quantizer = faiss.IndexFlatL2(xb.shape[1])
    index = faiss.IndexIVFFlat(
        quantizer, xb.shape[1], nlist, faiss.METRIC_L2
    )
    if index.is_trained:
        raise AssertionError("IVF-Flat should require training")
    index.train(xb)
    if not index.is_trained:
        raise AssertionError("IVF-Flat did not become trained")
    index.add(xb)
    index.nprobe = nprobe
    distances, labels = index.search(xq, k)
    _check_results("IVF-Flat", distances, labels, xq.shape[0], k)
    if index.ntotal != xb.shape[0]:
        raise AssertionError("IVF-Flat ntotal does not match added vectors")


def _run_hnsw(
    faiss: object,
    xb: np.ndarray,
    xq: np.ndarray,
    k: int,
    m: int,
    ef_search: int,
) -> None:
    index = faiss.IndexHNSWFlat(xb.shape[1], m)
    if not index.is_trained:
        raise AssertionError("HNSW Flat should be ready without training")
    index.hnsw.efConstruction = max(2 * m, 40)
    index.add(xb)
    index.hnsw.efSearch = ef_search
    distances, labels = index.search(xq, k)
    _check_results("HNSW", distances, labels, xq.shape[0], k)
    if index.ntotal != xb.shape[0]:
        raise AssertionError("HNSW ntotal does not match added vectors")


def main(argv: Iterable[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        _validate_args(args)
        import faiss

        old_threads = faiss.omp_get_max_threads()
        faiss.omp_set_num_threads(args.threads)
        try:
            xb, xq = _data(args)
            _check_sentinels(faiss, xb, xq)
            if args.case in ("all", "flat"):
                _run_flat(faiss, xb, xq, args.k)
                print("flat: ok")
            if args.case in ("all", "ivf"):
                _run_ivf(faiss, xb, xq, args.k, args.nlist, args.nprobe)
                print("ivf: ok")
            if args.case in ("all", "hnsw"):
                _run_hnsw(faiss, xb, xq, args.k, args.hnsw_m, args.ef_search)
                print("hnsw: ok")
        finally:
            faiss.omp_set_num_threads(old_threads)
    except (AssertionError, ImportError, RuntimeError, ValueError) as exc:
        print(f"smoke_search: error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
