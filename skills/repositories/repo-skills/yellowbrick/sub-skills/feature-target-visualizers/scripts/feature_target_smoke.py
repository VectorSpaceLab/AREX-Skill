#!/usr/bin/env python3
"""No-network smoke check for Yellowbrick feature and target visualizers.

The helper creates small synthetic arrays, renders several feature/target
visualizers with a non-interactive Matplotlib backend, and verifies that PNG
files were written. It is intended for quick skill usability checks, not image
similarity testing or benchmarking.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import matplotlib

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import make_classification

from yellowbrick.features import PCA, Rank2D
from yellowbrick.target import (
    BalancedBinningReference,
    ClassBalance,
    FeatureCorrelation,
)


def make_synthetic_data(random_state: int = 42):
    """Create bounded synthetic feature, class-target, and numeric-target data."""
    X, y_class = make_classification(
        n_samples=96,
        n_features=5,
        n_informative=4,
        n_redundant=0,
        n_repeated=0,
        n_classes=2,
        class_sep=1.2,
        weights=[0.35, 0.65],
        random_state=random_state,
    )
    rng = np.random.RandomState(random_state)
    y_numeric = 1.5 * X[:, 0] - 0.8 * X[:, 2] + rng.normal(scale=0.25, size=X.shape[0])
    feature_names = ["signal_a", "signal_b", "signal_c", "signal_d", "signal_e"]
    class_names = ["minority", "majority"]
    return X, y_class, y_numeric, feature_names, class_names


def save_visualizer(viz, outpath: Path, fig) -> Dict[str, object]:
    """Save a fitted/drawn Yellowbrick visualizer and validate the result."""
    outpath.parent.mkdir(parents=True, exist_ok=True)
    viz.show(outpath=str(outpath), clear_figure=True)
    plt.close(fig)

    if not outpath.exists():
        raise RuntimeError(f"expected output file was not created: {outpath}")
    size = outpath.stat().st_size
    if size <= 0:
        raise RuntimeError(f"output file is empty: {outpath}")
    return {"path": str(outpath), "bytes": size}


def run_smoke(outdir: Path) -> Dict[str, object]:
    X, y_class, y_numeric, feature_names, class_names = make_synthetic_data()
    outputs: List[Dict[str, object]] = []

    # Feature visualizer: Rank2D pairwise feature ranking.
    fig, ax = plt.subplots(figsize=(7, 6))
    rank = Rank2D(ax=ax, algorithm="pearson", features=feature_names)
    rank.fit(X, y_class)
    rank.transform(X)
    outputs.append(save_visualizer(rank, outdir / "rank2d.png", fig))

    # Feature projection visualizer: PCA with class-colored scatter.
    fig, ax = plt.subplots(figsize=(7, 6))
    pca = PCA(
        ax=ax,
        features=feature_names,
        classes=class_names,
        scale=True,
        projection=2,
        random_state=42,
    )
    embedding = pca.fit_transform(X, y_class)
    if embedding.shape != (X.shape[0], 2):
        raise RuntimeError(f"unexpected PCA embedding shape: {embedding.shape}")
    outputs.append(save_visualizer(pca, outdir / "pca.png", fig))

    # Target visualizer: class support balance.
    fig, ax = plt.subplots(figsize=(7, 5))
    balance = ClassBalance(ax=ax, labels=class_names)
    balance.fit(y_class)
    outputs.append(save_visualizer(balance, outdir / "class_balance.png", fig))

    # Target visualizer: continuous target binning reference.
    fig, ax = plt.subplots(figsize=(7, 5))
    binning = BalancedBinningReference(ax=ax, target="synthetic_score", bins=4)
    binning.fit(y_numeric)
    if len(binning.bin_edges_) != 5:
        raise RuntimeError(f"unexpected bin edge count: {len(binning.bin_edges_)}")
    outputs.append(save_visualizer(binning, outdir / "balanced_binning.png", fig))

    # Feature-to-target visualizer: Pearson feature correlations.
    fig, ax = plt.subplots(figsize=(7, 5))
    corr = FeatureCorrelation(ax=ax, method="pearson", labels=feature_names, sort=True)
    corr.fit(X, y_numeric)
    if corr.scores_.shape[0] != len(feature_names):
        raise RuntimeError("feature correlation did not score every feature")
    outputs.append(save_visualizer(corr, outdir / "feature_correlation.png", fig))

    return {
        "status": "ok",
        "n_samples": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "outputs": outputs,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a safe Yellowbrick feature/target visualizer smoke check."
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("yellowbrick-feature-target-smoke"),
        help="Directory where PNG outputs will be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_smoke(args.outdir)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
