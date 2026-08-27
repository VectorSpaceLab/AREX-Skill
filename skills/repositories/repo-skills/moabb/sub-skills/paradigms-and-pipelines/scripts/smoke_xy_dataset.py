#!/usr/bin/env python3
"""Run a deterministic, offline sklearn pipeline on synthetic X/y epochs.

This is a small replacement for the X/y integration example.  It deliberately
uses arrays rather than a network dataset and checks the central MOABB pipeline
shape contract: epochs are 3-D, LogVariance produces 2-D features, and the
classifier can fit/predict inside a sklearn Pipeline.
"""

from __future__ import annotations

import argparse
from typing import Sequence

import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.pipeline import make_pipeline

from moabb.pipelines import LogVariance


def build_fixture(seed: int = 17) -> tuple[np.ndarray, np.ndarray]:
    """Create two deterministic classes with different channel variance."""
    rng = np.random.default_rng(seed)
    n_trials, n_channels, n_times = 24, 3, 64
    y = np.repeat(np.array([0, 1], dtype=int), n_trials // 2)
    X = rng.normal(0.0, 0.08, size=(n_trials, n_channels, n_times))
    X[y == 0, 0, :] += rng.normal(0.0, 0.8, size=(np.sum(y == 0), n_times))
    X[y == 1, 1, :] += rng.normal(0.0, 0.8, size=(np.sum(y == 1), n_times))
    return X, y


def run(tiny_fixture: bool = False) -> int:
    """Run the local smoke check and return a process status."""
    X, y = build_fixture()
    if X.ndim != 3 or X.shape[0] != len(y):
        raise AssertionError(f"unexpected fixture contract: X={X.shape}, y={y.shape}")

    pipeline = make_pipeline(LogVariance(), LinearDiscriminantAnalysis())
    pipeline.fit(X, y)
    features = pipeline.named_steps["logvariance"].transform(X)
    predictions = pipeline.predict(X)

    if features.ndim != 2 or features.shape[0] != len(y):
        raise AssertionError(f"LogVariance did not produce 2-D rows: {features.shape}")
    if predictions.shape != y.shape or not np.all(np.isfinite(features)):
        raise AssertionError("pipeline output is not finite or trial-aligned")

    print(
        f"ok: X={X.shape}, features={features.shape}, "
        f"predictions={predictions.shape}, classes={np.unique(y).tolist()}"
    )
    if tiny_fixture:
        print("tiny fixture: deterministic offline X/y pipeline passed")
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tiny-fixture",
        action="store_true",
        help="run the deterministic local fixture (the default behavior)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    return run(tiny_fixture=args.tiny_fixture)


if __name__ == "__main__":
    raise SystemExit(main())
