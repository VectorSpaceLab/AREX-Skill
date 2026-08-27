#!/usr/bin/env python3
"""Deterministic in-memory smoke checks for unsupervised clustering APIs."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from typing import Any

os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np
from mlfromscratch.unsupervised_learning import DBSCAN, KMeans, PCA


def _counts(labels: np.ndarray) -> dict[str, int]:
    return {str(int(label)): int(count) for label, count in sorted(Counter(labels.astype(int)).items())}


def build_dataset() -> np.ndarray:
    """Return two compact clusters with comparable feature scales."""
    return np.array(
        [
            [0.00, 0.00],
            [0.00, 0.10],
            [0.10, 0.00],
            [5.00, 5.00],
            [5.10, 5.00],
            [5.00, 5.10],
        ],
        dtype=float,
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    np.random.seed(args.seed)
    X = build_dataset()
    result: dict[str, Any] = {"n_samples": int(X.shape[0]), "seed": int(args.seed)}

    kmeans = KMeans(k=2, max_iterations=args.max_iterations)
    kmeans_labels = np.asarray(kmeans.predict(X))
    if kmeans_labels.shape != (X.shape[0],):
        raise RuntimeError(f"KMeans returned shape {kmeans_labels.shape}, expected {(X.shape[0],)}")
    if not np.all(np.isfinite(kmeans_labels)):
        raise RuntimeError("KMeans returned non-finite labels")
    result["kmeans_counts"] = _counts(kmeans_labels)

    if not args.skip_pca:
        projected = np.real_if_close(PCA().transform(X, args.pca_components))
        if projected.shape != (X.shape[0], args.pca_components):
            raise RuntimeError(f"PCA returned shape {projected.shape}")
        if not np.all(np.isfinite(projected)):
            raise RuntimeError("PCA returned non-finite values")
        result["pca_shape"] = list(projected.shape)
        result["pca_first_row"] = [round(float(v), 6) for v in projected[0]]

    if not args.skip_dbscan:
        dbscan = DBSCAN(eps=args.dbscan_eps, min_samples=args.dbscan_min_samples)
        dbscan_labels = np.asarray(dbscan.predict(X))
        if dbscan_labels.shape != (X.shape[0],):
            raise RuntimeError(f"DBSCAN returned shape {dbscan_labels.shape}, expected {(X.shape[0],)}")
        if not np.all(np.isfinite(dbscan_labels)):
            raise RuntimeError("DBSCAN returned non-finite labels")
        result["dbscan_counts"] = _counts(dbscan_labels)
        result["dbscan_note"] = "DBSCAN labels are implementation-specific; inspect counts, not sklearn-style -1 noise labels."

    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run tiny deterministic KMeans plus optional PCA/DBSCAN smoke checks without plotting."
    )
    parser.add_argument("--seed", type=int, default=7, help="NumPy seed used before randomized algorithms.")
    parser.add_argument("--max-iterations", type=int, default=25, help="KMeans iteration bound.")
    parser.add_argument("--skip-pca", action="store_true", help="Skip the PCA transform smoke.")
    parser.add_argument("--pca-components", type=int, default=1, choices=(1, 2), help="Number of PCA components to request.")
    parser.add_argument("--skip-dbscan", action="store_true", help="Skip the DBSCAN smoke.")
    parser.add_argument("--dbscan-eps", type=float, default=0.30, help="DBSCAN epsilon radius for the tiny dataset.")
    parser.add_argument("--dbscan-min-samples", type=int, default=2, help="DBSCAN core-point neighbor threshold.")
    args = parser.parse_args()
    if args.max_iterations < 1 or args.max_iterations > 500:
        parser.error("--max-iterations must be in [1, 500]")
    if args.dbscan_eps <= 0:
        parser.error("--dbscan-eps must be positive")
    if args.dbscan_min_samples < 1:
        parser.error("--dbscan-min-samples must be positive")
    return args


def main() -> int:
    print(json.dumps(run(parse_args()), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
