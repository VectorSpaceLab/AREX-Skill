#!/usr/bin/env python3
"""Tiny Fairlearn reductions smoke check."""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

from fairlearn.metrics import MetricFrame, selection_rate
from fairlearn.reductions import DemographicParity, EqualizedOdds, ExponentiatedGradient, GridSearch


def make_fixture(n_samples: int = 80):
    rng = np.random.default_rng(0)
    sensitive = rng.integers(0, 2, size=n_samples)
    x0 = rng.normal(loc=sensitive * 0.6, scale=1.0, size=n_samples)
    x1 = rng.normal(size=n_samples)
    logits = x0 + 0.7 * x1 - 0.2 + 0.4 * sensitive
    y = (logits > np.median(logits)).astype(int)
    X = pd.DataFrame({"x0": x0, "x1": x1})
    return X, y, sensitive


def summarize(label: str, y_true, pred, sensitive) -> None:
    mf = MetricFrame(
        metrics={"accuracy": accuracy_score, "selection_rate": selection_rate},
        y_true=y_true,
        y_pred=pred,
        sensitive_features=sensitive,
    )
    print(f"\n{label} overall:\n{mf.overall}")
    print(f"{label} by group:\n{mf.by_group}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-iter", type=int, default=3, help="ExponentiatedGradient max_iter for smoke.")
    parser.add_argument("--grid-size", type=int, default=3, help="GridSearch grid_size for smoke.")
    args = parser.parse_args()

    X, y, sensitive = make_fixture()
    base = LogisticRegression(solver="liblinear", random_state=0)
    base.fit(X, y)
    summarize("baseline", y, base.predict(X), sensitive)

    eg = ExponentiatedGradient(
        LogisticRegression(solver="liblinear", random_state=0),
        DemographicParity(),
        max_iter=args.max_iter,
    )
    eg.fit(X, y, sensitive_features=sensitive)
    pred_eg = eg.predict(X)
    summarize("ExponentiatedGradient", y, pred_eg, sensitive)

    grid = GridSearch(
        LogisticRegression(solver="liblinear", random_state=0),
        EqualizedOdds(),
        grid_size=args.grid_size,
    )
    grid.fit(X, y, sensitive_features=sensitive)
    pred_grid = grid.predict(X)
    summarize("GridSearch", y, pred_grid, sensitive)

    if len(pred_eg) != len(y) or len(pred_grid) != len(y):
        raise AssertionError("Reductions predictions must preserve sample count")
    print("Reductions smoke check completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
