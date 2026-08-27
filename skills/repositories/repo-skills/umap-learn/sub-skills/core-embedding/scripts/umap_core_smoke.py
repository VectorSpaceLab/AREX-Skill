#!/usr/bin/env python3
"""Safe smoke checks for core umap.UMAP workflows.

The script uses only local sklearn toy datasets. It performs no plotting,
network access, large training, or destructive writes. Output is JSON by
default so agents can parse it during skill verification.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
import warnings
from typing import Any, Callable


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run safe local smoke checks for base umap.UMAP: fit, transform, "
            "inverse, sparse, precomputed distance, precomputed k-NN, and update."
        )
    )
    parser.add_argument(
        "--dataset",
        choices=("iris", "digits"),
        default="iris",
        help="Local sklearn toy dataset to use; no downloads are performed (default: iris).",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=90,
        help="Maximum number of rows to use after loading the toy dataset (default: 90).",
    )
    parser.add_argument(
        "--n-neighbors",
        type=int,
        default=10,
        help="UMAP n_neighbors for smoke fits; automatically capped below train size (default: 10).",
    )
    parser.add_argument(
        "--n-components",
        type=int,
        default=2,
        help="UMAP output dimensionality (default: 2).",
    )
    parser.add_argument(
        "--n-epochs",
        type=int,
        default=40,
        help="Small n_epochs value for quick smoke runs (default: 40).",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Seed for reproducible smoke fits; set negative with --no-random-state instead (default: 42).",
    )
    parser.add_argument(
        "--no-random-state",
        action="store_true",
        help="Use random_state=None to exercise speed-oriented non-deterministic mode.",
    )
    parser.add_argument(
        "--transform",
        action="store_true",
        help="Check transform on held-out rows (enabled by --all).",
    )
    parser.add_argument(
        "--inverse",
        action="store_true",
        help="Check inverse_transform on a few learned embedding points (enabled by --all).",
    )
    parser.add_argument(
        "--sparse",
        action="store_true",
        help="Check sparse CSR fit/transform on held-out rows (enabled by --all).",
    )
    parser.add_argument(
        "--precomputed",
        action="store_true",
        help="Check metric='precomputed' fit and new-to-train distance transform (enabled by --all).",
    )
    parser.add_argument(
        "--precomputed-knn",
        action="store_true",
        help="Check precomputed_knn using umap.umap_.nearest_neighbors (enabled by --all).",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Check update appends held-out rows to an unsupervised mapper (enabled by --all).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Enable transform, inverse, sparse, precomputed, precomputed-kNN, and update checks.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    parser.add_argument(
        "--verbose-errors",
        action="store_true",
        help="Include traceback strings for failed checks in the JSON output.",
    )
    # Kept for compatibility with prompts that request JSON explicitly.
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON output (default behavior).",
    )
    return parser


def import_runtime() -> tuple[Any, Any, Any, Any, Any, Any, Any, Any]:
    try:
        import numpy as np
        import scipy.sparse as sp
        import umap
        from sklearn.datasets import load_digits, load_iris
        from sklearn.metrics import pairwise_distances
        from sklearn.model_selection import train_test_split
        from umap.umap_ import nearest_neighbors
    except ImportError as exc:  # pragma: no cover - depends on caller env
        advice = (
            "Missing a core dependency for umap-learn smoke checks. Install the "
            "base package and required runtime dependencies, for example: "
            "python -m pip install umap-learn scikit-learn scipy numpy numba pynndescent tqdm. "
            "Plotting, ParametricUMAP, and TBB extras are optional and are not required by this script."
        )
        raise RuntimeError(f"{exc.__class__.__name__}: {exc}. {advice}") from exc
    return np, sp, umap, load_digits, load_iris, pairwise_distances, train_test_split, nearest_neighbors


def finite_summary(np: Any, array: Any) -> dict[str, Any]:
    arr = np.asarray(array)
    return {
        "shape": list(arr.shape),
        "dtype": str(arr.dtype),
        "finite": bool(np.isfinite(arr).all()),
        "nan_count": int(np.isnan(arr).sum()) if arr.size else 0,
    }


def run_check(name: str, func: Callable[[], dict[str, Any]], verbose_errors: bool) -> dict[str, Any]:
    start = time.time()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            result = func()
            status = "passed"
            error = None
        except Exception as exc:  # pragma: no cover - diagnostic path
            result = {}
            status = "failed"
            error = {
                "type": exc.__class__.__name__,
                "message": str(exc),
            }
            if verbose_errors:
                error["traceback"] = traceback.format_exc()
    return {
        "name": name,
        "status": status,
        "elapsed_seconds": round(time.time() - start, 4),
        "warnings": [str(item.message) for item in caught],
        "error": error,
        "result": result,
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        np, sp, umap, load_digits, load_iris, pairwise_distances, train_test_split, nearest_neighbors = import_runtime()
    except RuntimeError as exc:
        payload = {
            "status": "dependency_error",
            "error": str(exc),
            "checks": [],
        }
        print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
        return 2

    if args.sample_size < 20:
        parser.error("--sample-size must be at least 20 for stable train/test smoke checks")
    if args.n_neighbors < 2:
        parser.error("--n-neighbors must be at least 2")
    if args.n_components < 1:
        parser.error("--n-components must be at least 1")
    if args.n_epochs < 1:
        parser.error("--n-epochs must be positive")

    if args.all:
        args.transform = True
        args.inverse = True
        args.sparse = True
        args.precomputed = True
        args.precomputed_knn = True
        args.update = True

    dataset = load_iris() if args.dataset == "iris" else load_digits()
    X = dataset.data.astype(np.float32, copy=False)
    y = getattr(dataset, "target", None)
    if args.sample_size < X.shape[0]:
        X = X[: args.sample_size]
        if y is not None:
            y = y[: args.sample_size]

    stratify = y if y is not None and len(np.unique(y)) > 1 and min(np.bincount(y.astype(int))) >= 2 else None
    X_train, X_test = train_test_split(
        X,
        test_size=0.25,
        random_state=0,
        stratify=stratify,
    )
    n_neighbors = min(args.n_neighbors, max(2, X_train.shape[0] - 1))
    random_state = None if args.no_random_state else args.random_state

    def new_mapper(**kwargs: Any) -> Any:
        params = dict(
            n_neighbors=n_neighbors,
            n_components=args.n_components,
            n_epochs=args.n_epochs,
            random_state=random_state,
            n_jobs=1 if random_state is not None else -1,
        )
        params.update(kwargs)
        return umap.UMAP(**params)

    checks: list[dict[str, Any]] = []

    def fit_check() -> dict[str, Any]:
        mapper = new_mapper().fit(X_train)
        embedding = mapper.embedding_
        return {
            "embedding": finite_summary(np, embedding),
            "graph_shape": list(mapper.graph_.shape),
            "n_neighbors_requested": args.n_neighbors,
            "n_neighbors_effective": int(getattr(mapper, "_n_neighbors", n_neighbors)),
            "n_components": int(mapper.n_components),
            "random_state": mapper.random_state,
            "n_jobs_effective": mapper.n_jobs,
            "transform_mode": mapper.transform_mode,
        }

    checks.append(run_check("fit", fit_check, args.verbose_errors))

    if args.transform:
        def transform_check() -> dict[str, Any]:
            mapper = new_mapper().fit(X_train)
            transformed = mapper.transform(X_test)
            same = mapper.transform(X_train)
            return {
                "held_out_embedding": finite_summary(np, transformed),
                "training_shortcut_matches_embedding": bool(np.allclose(same, mapper.embedding_, equal_nan=True)),
            }

        checks.append(run_check("transform", transform_check, args.verbose_errors))

    if args.inverse:
        def inverse_check() -> dict[str, Any]:
            mapper = new_mapper(metric="euclidean", n_components=min(args.n_components, 3)).fit(X_train)
            low_dim = mapper.embedding_[: min(3, mapper.embedding_.shape[0])]
            reconstructed = mapper.inverse_transform(low_dim)
            return {
                "query_embedding": finite_summary(np, low_dim),
                "inverse_output": finite_summary(np, reconstructed),
                "original_feature_count": int(X_train.shape[1]),
            }

        checks.append(run_check("inverse_transform", inverse_check, args.verbose_errors))

    if args.sparse:
        def sparse_check() -> dict[str, Any]:
            X_train_sparse = sp.csr_matrix(X_train)
            X_test_sparse = sp.csr_matrix(X_test)
            mapper = new_mapper(metric="euclidean", low_memory=True).fit(X_train_sparse)
            transformed = mapper.transform(X_test_sparse)
            return {
                "train_sparse_format": X_train_sparse.getformat(),
                "train_nnz": int(X_train_sparse.nnz),
                "held_out_embedding": finite_summary(np, transformed),
                "inverse_transform_expected_unavailable": bool(getattr(mapper, "_sparse_data", False)),
            }

        checks.append(run_check("sparse_fit_transform", sparse_check, args.verbose_errors))

    if args.precomputed:
        def precomputed_check() -> dict[str, Any]:
            D_train = pairwise_distances(X_train).astype(np.float32)
            D_new_to_train = pairwise_distances(X_test, X_train).astype(np.float32)
            mapper = new_mapper(metric="precomputed").fit(D_train)
            transformed = mapper.transform(D_new_to_train)
            return {
                "fit_distance_shape": list(D_train.shape),
                "transform_distance_shape": list(D_new_to_train.shape),
                "held_out_embedding": finite_summary(np, transformed),
                "expected_transform_columns": int(D_train.shape[0]),
            }

        checks.append(run_check("precomputed_distance_transform", precomputed_check, args.verbose_errors))

    if args.precomputed_knn:
        def precomputed_knn_check() -> dict[str, Any]:
            k = min(max(n_neighbors + 2, n_neighbors), X_train.shape[0] - 1)
            knn = nearest_neighbors(
                X_train,
                n_neighbors=k,
                metric="euclidean",
                metric_kwds=None,
                angular=False,
                random_state=random_state,
                low_memory=True,
                n_jobs=1 if random_state is not None else -1,
            )
            mapper = new_mapper(precomputed_knn=knn).fit(X_train)
            transformed = mapper.transform(X_test)
            return {
                "knn_indices_shape": list(knn[0].shape),
                "knn_dists_shape": list(knn[1].shape),
                "has_search_index": knn[2] is not None,
                "held_out_embedding": finite_summary(np, transformed),
            }

        checks.append(run_check("precomputed_knn_transform", precomputed_knn_check, args.verbose_errors))

    if args.update:
        def update_check() -> dict[str, Any]:
            mapper = new_mapper().fit(X_train)
            before = mapper.embedding_.shape[0]
            result = mapper.update(X_test)
            after = mapper.embedding_.shape[0]
            return {
                "return_value_is_none": result is None,
                "before_rows": int(before),
                "added_rows": int(X_test.shape[0]),
                "after_rows": int(after),
                "embedding": finite_summary(np, mapper.embedding_),
            }

        checks.append(run_check("update", update_check, args.verbose_errors))

    status = "passed" if all(check["status"] == "passed" for check in checks) else "failed"
    payload = {
        "status": status,
        "package": {
            "umap_version": getattr(umap, "__version__", "unknown"),
        },
        "dataset": {
            "name": args.dataset,
            "rows_used": int(X.shape[0]),
            "features": int(X.shape[1]),
            "train_rows": int(X_train.shape[0]),
            "test_rows": int(X_test.shape[0]),
        },
        "parameters": {
            "n_neighbors_effective": int(n_neighbors),
            "n_components": int(args.n_components),
            "n_epochs": int(args.n_epochs),
            "random_state": random_state,
            "note": "When random_state is set, UMAP uses n_jobs=1 for reproducibility.",
        },
        "checks": checks,
    }
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if status == "passed" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
