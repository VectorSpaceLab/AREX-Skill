#!/usr/bin/env python3
"""Tiny Fairlearn ThresholdOptimizer smoke check."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from fairlearn.metrics import MetricFrame, selection_rate
from fairlearn.postprocessing import ThresholdOptimizer


def make_fixture(n_samples: int = 100):
    rng = np.random.default_rng(0)
    sensitive = rng.integers(0, 2, size=n_samples)
    x0 = rng.normal(loc=sensitive * 0.7, scale=1.0, size=n_samples)
    x1 = rng.normal(size=n_samples)
    logits = 1.2 * x0 + 0.6 * x1 - 0.1
    y = (logits + 0.3 * sensitive > np.median(logits)).astype(int)
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


def run_smoke(plot: bool, output_dir: Path) -> None:
    X, y, sensitive = make_fixture()
    X_train, X_test, y_train, y_test, A_train, A_test = train_test_split(
        X, y, sensitive, test_size=0.35, random_state=0, stratify=y
    )

    base = LogisticRegression(solver="liblinear", random_state=0)
    base.fit(X_train, y_train)
    summarize("baseline", y_test, base.predict(X_test), A_test)

    optimizer = ThresholdOptimizer(
        estimator=LogisticRegression(solver="liblinear", random_state=0),
        constraints="demographic_parity",
        objective="accuracy_score",
        grid_size=25,
        prefit=False,
        predict_method="predict_proba",
    )
    optimizer.fit(X_train, y_train, sensitive_features=A_train)
    pred = optimizer.predict(X_test, sensitive_features=A_test, random_state=0)
    summarize("postprocessed", y_test, pred, A_test)
    if len(pred) != len(y_test):
        raise AssertionError("ThresholdOptimizer predictions must preserve sample count")

    if plot:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from fairlearn.postprocessing import plot_threshold_optimizer

        output_dir.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots()
        plot_threshold_optimizer(optimizer, ax=ax, show_plot=False)
        fig.savefig(output_dir / "threshold-optimizer.png", bbox_inches="tight")
        plt.close(fig)
        print(f"Wrote plot to {output_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot", action="store_true", help="Also exercise matplotlib threshold-optimizer plotting.")
    parser.add_argument("--output-dir", type=Path, default=Path("fairlearn-threshold-plots"), help="Plot output directory when --plot is set.")
    args = parser.parse_args()
    run_smoke(args.plot, args.output_dir)
    print("ThresholdOptimizer smoke check completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
