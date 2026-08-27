#!/usr/bin/env python3
"""Safe smoke checks for supervised UMAP and densMAP.

The script uses tiny sklearn fixtures, prints a JSON summary, and avoids
plotting, downloads, destructive writes, and large training runs. Optional
HDBSCAN clustering is imported only when explicitly requested.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def parse_json_dict(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(
            f"--target-metric-kwds must be valid JSON: {exc.msg}"
        ) from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("--target-metric-kwds must decode to a JSON object")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny supervised UMAP smoke check, optionally enabling densMAP, "
            "density outputs, KMeans/HDBSCAN validation, and LOF outlier scoring."
        )
    )
    parser.add_argument("--dataset", choices=("iris", "blobs"), default="iris")
    parser.add_argument("--n-neighbors", type=int, default=10)
    parser.add_argument("--n-components", type=int, default=2)
    parser.add_argument("--n-epochs", type=int, default=50)
    parser.add_argument("--min-dist", type=float, default=0.05)
    parser.add_argument("--target-weight", type=float, default=0.5)
    parser.add_argument("--target-metric", default="categorical")
    parser.add_argument("--target-metric-kwds", type=parse_json_dict, default=None)
    parser.add_argument("--target-n-neighbors", type=int, default=-1)
    parser.add_argument(
        "--partial-label-fraction",
        type=float,
        default=0.0,
        help="Fraction of labels to replace with -1 before fitting.",
    )
    parser.add_argument("--densmap", action="store_true")
    parser.add_argument("--output-dens", action="store_true")
    parser.add_argument("--dens-lambda", type=float, default=2.0)
    parser.add_argument("--dens-frac", type=float, default=0.3)
    parser.add_argument("--dens-var-shift", type=float, default=0.1)
    parser.add_argument(
        "--cluster-method",
        choices=("none", "kmeans", "hdbscan"),
        default="none",
        help="Optional downstream clustering validation.",
    )
    parser.add_argument("--outlier-check", action="store_true")
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument(
        "--semi-supervised",
        action="store_true",
        help="Convenience alias: replace 30% of labels with -1 unless --partial-label-fraction is also set.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Accepted for consistency; this helper always prints JSON.",
    )
    return parser


def load_runtime_dependencies() -> dict[str, Any]:
    try:
        import numpy as np
        from sklearn.cluster import KMeans
        from sklearn.datasets import load_iris, make_blobs
        from sklearn.metrics import adjusted_mutual_info_score, adjusted_rand_score
        from sklearn.neighbors import LocalOutlierFactor

        try:
            from sklearn.manifold import trustworthiness
        except ImportError:  # pragma: no cover - older sklearn fallback
            from sklearn.manifold.t_sne import trustworthiness

        from umap import UMAP
    except ImportError as exc:
        print(
            "ImportError while loading required runtime dependencies. Install the "
            "base package stack, for example `pip install umap-learn scikit-learn`.",
            file=sys.stderr,
        )
        print(f"ImportError: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    return {
        "np": np,
        "KMeans": KMeans,
        "load_iris": load_iris,
        "make_blobs": make_blobs,
        "adjusted_mutual_info_score": adjusted_mutual_info_score,
        "adjusted_rand_score": adjusted_rand_score,
        "LocalOutlierFactor": LocalOutlierFactor,
        "trustworthiness": trustworthiness,
        "UMAP": UMAP,
    }


def make_dataset(name: str, seed: int, deps: dict[str, Any]) -> tuple[Any, Any]:
    np = deps["np"]
    if name == "iris":
        data = deps["load_iris"]()
        return data.data.astype(np.float32), data.target.astype(np.int64)
    if name == "blobs":
        X, y = deps["make_blobs"](
            n_samples=120,
            centers=3,
            cluster_std=0.75,
            random_state=seed,
        )
        return X.astype(np.float32), y.astype(np.int64)
    raise ValueError(f"Unsupported dataset: {name}")


def mask_labels(y: Any, fraction: float, seed: int, deps: dict[str, Any]) -> tuple[Any, int]:
    if fraction <= 0.0:
        return y.copy(), 0
    np = deps["np"]
    rng = np.random.default_rng(seed)
    count = max(1, int(round(len(y) * fraction)))
    indices = rng.choice(len(y), size=count, replace=False)
    masked = y.copy()
    masked[indices] = -1
    return masked, int(count)


def as_float(value: Any, deps: dict[str, Any]) -> float:
    return float(deps["np"].asarray(value).item())


def run_clustering(method: str, embedding: Any, y_true: Any, seed: int, deps: dict[str, Any]) -> dict[str, Any]:
    np = deps["np"]
    summary: dict[str, Any] = {"method": method, "status": "skipped"}
    if method == "none":
        return summary
    if method == "kmeans":
        labels = deps["KMeans"](
            n_clusters=int(np.unique(y_true).size),
            n_init=10,
            random_state=seed,
        ).fit_predict(embedding)
        summary.update(
            {
                "status": "ok",
                "ari": as_float(deps["adjusted_rand_score"](y_true, labels), deps),
                "ami": as_float(deps["adjusted_mutual_info_score"](y_true, labels), deps),
            }
        )
        return summary

    try:
        import hdbscan  # type: ignore
    except ImportError as exc:
        summary.update(
            {
                "status": "missing_optional_dependency",
                "recovery": "Install the optional `hdbscan` package or use --cluster-method kmeans.",
                "error": str(exc),
            }
        )
        return summary

    labels = hdbscan.HDBSCAN(min_cluster_size=10, min_samples=5).fit_predict(embedding)
    clustered = labels >= 0
    summary.update(
        {
            "status": "ok",
            "ari": as_float(deps["adjusted_rand_score"](y_true, labels), deps),
            "ami": as_float(deps["adjusted_mutual_info_score"](y_true, labels), deps),
            "noise_fraction": as_float(1.0 - float(np.mean(clustered)), deps),
        }
    )
    return summary


def run_outlier_check(embedding: Any, deps: dict[str, Any]) -> dict[str, Any]:
    np = deps["np"]
    n_samples = embedding.shape[0]
    lof_neighbors = min(20, max(2, n_samples - 1))
    contamination = min(0.1, max(0.01, 3.0 / float(n_samples)))
    flags = deps["LocalOutlierFactor"](
        n_neighbors=lof_neighbors,
        contamination=contamination,
    ).fit_predict(embedding)
    return {
        "enabled": True,
        "method": "lof",
        "n_neighbors": int(lof_neighbors),
        "contamination": float(contamination),
        "outlier_count": int(np.sum(flags == -1)),
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.semi_supervised and args.partial_label_fraction == 0.0:
        args.partial_label_fraction = 0.3
    if args.n_neighbors < 2:
        parser.error("--n-neighbors must be greater than 1")
    if args.target_n_neighbors != -1 and args.target_n_neighbors < 2:
        parser.error("--target-n-neighbors must be -1 or greater than 1")
    if args.dens_lambda < 0.0:
        parser.error("--dens-lambda must be non-negative")
    if not 0.0 <= args.dens_frac <= 1.0:
        parser.error("--dens-frac must be between 0.0 and 1.0")
    if args.dens_var_shift < 0.0:
        parser.error("--dens-var-shift must be non-negative")
    if not 0.0 <= args.partial_label_fraction <= 1.0:
        parser.error("--partial-label-fraction must be between 0.0 and 1.0")

    deps = load_runtime_dependencies()
    np = deps["np"]
    X, y_true = make_dataset(args.dataset, args.random_state, deps)
    y_train, masked_count = mask_labels(y_true, args.partial_label_fraction, args.random_state, deps)

    model = deps["UMAP"](
        n_neighbors=args.n_neighbors,
        n_components=args.n_components,
        min_dist=args.min_dist,
        random_state=args.random_state,
        n_epochs=args.n_epochs,
        n_jobs=1,
        target_weight=args.target_weight,
        target_metric=args.target_metric,
        target_metric_kwds=args.target_metric_kwds,
        target_n_neighbors=args.target_n_neighbors,
        densmap=args.densmap,
        dens_lambda=args.dens_lambda,
        dens_frac=args.dens_frac,
        dens_var_shift=args.dens_var_shift,
        output_dens=args.output_dens,
    )
    fitted = model.fit_transform(X, y_train)

    if args.output_dens:
        embedding, rad_orig, rad_emb = fitted
    else:
        embedding, rad_orig, rad_emb = fitted, None, None

    embedding = np.asarray(embedding)
    n_trust = max(1, min(args.n_neighbors, max(1, (embedding.shape[0] - 1) // 2)))
    summary: dict[str, Any] = {
        "dataset": args.dataset,
        "n_samples": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "embedding_shape": [int(v) for v in embedding.shape],
        "embedding_finite": bool(np.isfinite(embedding).all()),
        "n_neighbors": int(args.n_neighbors),
        "n_epochs": int(args.n_epochs),
        "target_metric": args.target_metric,
        "target_metric_kwds": args.target_metric_kwds or {},
        "target_weight": float(args.target_weight),
        "target_n_neighbors": int(args.target_n_neighbors),
        "partial_label_fraction": float(args.partial_label_fraction),
        "masked_label_count": int(masked_count),
        "densmap": bool(args.densmap),
        "output_dens": bool(args.output_dens),
        "trustworthiness": as_float(deps["trustworthiness"](X, embedding, n_neighbors=n_trust), deps),
        "warnings": [],
    }

    if args.partial_label_fraction > 0.0 and args.target_metric != "categorical":
        summary["warnings"].append(
            "The -1 unlabeled convention is intended for target_metric='categorical'."
        )

    if args.output_dens and rad_orig is not None and rad_emb is not None:
        rad_orig = np.asarray(rad_orig)
        rad_emb = np.asarray(rad_emb)
        summary.update(
            {
                "rad_orig_mean": as_float(np.mean(rad_orig), deps),
                "rad_emb_mean": as_float(np.mean(rad_emb), deps),
                "rad_correlation": as_float(np.corrcoef(rad_orig, rad_emb)[0, 1], deps),
            }
        )

    cluster = run_clustering(args.cluster_method, embedding, y_true, args.random_state, deps)
    summary["cluster"] = cluster
    summary["outlier"] = run_outlier_check(embedding, deps) if args.outlier_check else {"enabled": False}

    print(json.dumps(summary, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
