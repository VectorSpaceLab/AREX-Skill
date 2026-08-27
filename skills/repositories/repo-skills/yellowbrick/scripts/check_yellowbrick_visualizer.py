#!/usr/bin/env python3
"""Safe Yellowbrick import and visualizer smoke check.

This helper uses synthetic scikit-learn data, forces Matplotlib's non-
interactive Agg backend, writes PNG outputs to --outdir, and performs no
network access or destructive writes.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs, make_classification, make_regression
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import train_test_split

import yellowbrick
from yellowbrick.classifier import ConfusionMatrix
from yellowbrick.cluster import KElbowVisualizer
from yellowbrick.regressor import ResidualsPlot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create small Yellowbrick classifier, regressor, and cluster diagnostic PNGs with Matplotlib Agg.",
    )
    parser.add_argument(
        "--outdir",
        default="yellowbrick-smoke-output",
        help="directory where PNG files and manifest.json will be written",
    )
    parser.add_argument("--random-state", type=int, default=42, help="deterministic random seed")
    return parser.parse_args()


def prepare_outdir(value: str) -> Path:
    outdir = Path(value).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    return outdir


def save(name: str, visualizer: Any, outdir: Path) -> dict[str, Any]:
    path = outdir / f"{name}.png"
    visualizer.show(outpath=str(path), clear_figure=True)
    plt.close("all")
    size = path.stat().st_size if path.exists() else 0
    if size <= 0:
        raise RuntimeError(f"{name} did not create a non-empty output at {path}")
    return {"name": name, "path": str(path), "size_bytes": size}


def classifier_smoke(outdir: Path, seed: int) -> dict[str, Any]:
    X, y = make_classification(
        n_samples=100,
        n_features=6,
        n_informative=4,
        n_redundant=0,
        random_state=seed,
    )
    X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, random_state=seed)
    visualizer = ConfusionMatrix(
        LogisticRegression(max_iter=300, solver="liblinear"),
        classes=["negative", "positive"],
    )
    visualizer.fit(X_train, y_train)
    visualizer.score(X_test, y_test)
    return save("confusion_matrix", visualizer, outdir)


def regression_smoke(outdir: Path, seed: int) -> dict[str, Any]:
    X, y = make_regression(n_samples=80, n_features=5, noise=0.3, random_state=seed)
    visualizer = ResidualsPlot(LinearRegression(), hist=False)
    visualizer.fit(X, y)
    visualizer.score(X, y)
    return save("residuals", visualizer, outdir)


def cluster_smoke(outdir: Path, seed: int) -> dict[str, Any]:
    X, _ = make_blobs(n_samples=80, centers=3, cluster_std=0.7, random_state=seed)
    visualizer = KElbowVisualizer(
        KMeans(n_init=5, random_state=seed),
        k=(2, 5),
        timings=False,
        locate_elbow=False,
    )
    visualizer.fit(X)
    return save("kelbow", visualizer, outdir)


def main() -> int:
    args = parse_args()
    outdir = prepare_outdir(args.outdir)
    outputs = [
        classifier_smoke(outdir, args.random_state),
        regression_smoke(outdir, args.random_state),
        cluster_smoke(outdir, args.random_state),
    ]
    manifest = {
        "yellowbrick_version": yellowbrick.__version__,
        "backend": matplotlib.get_backend(),
        "outputs": outputs,
    }
    manifest_path = outdir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
