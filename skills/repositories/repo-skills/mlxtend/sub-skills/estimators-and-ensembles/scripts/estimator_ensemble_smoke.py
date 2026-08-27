#!/usr/bin/env python3
"""Deterministic smoke checks for mlxtend estimator and ensemble APIs.

The script uses installed package imports plus tiny sklearn-generated datasets.
It does not read from a source checkout or write artifacts.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable

import numpy as np


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _task_voting() -> None:
    from sklearn.datasets import load_iris
    from sklearn.linear_model import LogisticRegression
    from sklearn.naive_bayes import GaussianNB
    from sklearn.tree import DecisionTreeClassifier

    from mlxtend.classifier import EnsembleVoteClassifier

    X, y = load_iris(return_X_y=True)
    X = X[:, :2].astype(float)

    classifiers = [
        LogisticRegression(max_iter=300, random_state=11),
        GaussianNB(),
        DecisionTreeClassifier(max_depth=3, random_state=11),
    ]
    sample_weight = np.ones(y.shape[0], dtype=float)
    sample_weight[y == 0] = 1.25

    ensemble = EnsembleVoteClassifier(
        clfs=classifiers,
        voting="soft",
        weights=[2, 1, 1],
    )
    ensemble.fit(X, y, sample_weight=sample_weight)

    pred = ensemble.predict(X[:8])
    probas = ensemble.predict_proba(X[:8])
    params = ensemble.get_params()

    _require(pred.shape == (8,), f"unexpected voting prediction shape: {pred.shape}")
    _require(probas.shape == (8, 3), f"unexpected voting proba shape: {probas.shape}")
    _require(np.allclose(probas.sum(axis=1), 1.0), "probability rows do not sum to 1")
    _require("logisticregression__C" in params, "missing LogisticRegression grid prefix")
    _require(
        "decisiontreeclassifier__max_depth" in params,
        "missing DecisionTreeClassifier grid prefix",
    )
    print("OK voting: soft probabilities, sample_weight, and grid prefixes")


def _task_stacking_regression() -> None:
    from sklearn.datasets import make_regression
    from sklearn.linear_model import Ridge
    from sklearn.model_selection import KFold
    from sklearn.tree import DecisionTreeRegressor

    from mlxtend.regressor import StackingCVRegressor

    X, y = make_regression(
        n_samples=48,
        n_features=5,
        n_informative=4,
        noise=0.4,
        random_state=7,
    )
    X = X.astype(float)
    y = y.astype(float)

    stack = StackingCVRegressor(
        regressors=[
            Ridge(alpha=1.0),
            DecisionTreeRegressor(max_depth=3, random_state=7),
        ],
        meta_regressor=Ridge(alpha=0.5),
        cv=KFold(n_splits=3, shuffle=True, random_state=7),
        random_state=7,
        use_features_in_secondary=True,
        store_train_meta_features=True,
    )
    stack.fit(X, y)

    pred = stack.predict(X[:6])
    meta_features = stack.predict_meta_features(X[:6])
    params = stack.get_params()

    _require(pred.shape == (6,), f"unexpected stacking prediction shape: {pred.shape}")
    _require(
        meta_features.shape == (6, 2),
        f"unexpected stacking meta-feature shape: {meta_features.shape}",
    )
    _require(
        stack.train_meta_features_.shape == (X.shape[0], 2),
        f"unexpected stored train meta-feature shape: {stack.train_meta_features_.shape}",
    )
    _require("meta_regressor__alpha" in params, "missing meta_regressor grid prefix")
    _require("ridge__alpha" in params, "missing Ridge grid prefix")
    _require(
        "decisiontreeregressor__max_depth" in params,
        "missing DecisionTreeRegressor grid prefix",
    )
    _require(np.isfinite(pred).all(), "stacking predictions contain non-finite values")
    print("OK stacking-regression: CV stack, meta-features, and grid prefixes")


def _task_kmeans() -> None:
    from sklearn.datasets import make_blobs

    from mlxtend.cluster import Kmeans

    X, _ = make_blobs(
        n_samples=36,
        centers=3,
        n_features=2,
        cluster_std=0.45,
        random_state=3,
    )
    X = X.astype(float)

    km = Kmeans(k=3, max_iter=20, convergence_tolerance=1e-5, random_seed=3)
    km.fit(X)
    labels = km.predict(X[:10])
    params = km.get_params()

    _require(km.centroids_.shape == (3, 2), f"unexpected centroid shape: {km.centroids_.shape}")
    _require(labels.shape == (10,), f"unexpected Kmeans label shape: {labels.shape}")
    _require(set(labels.tolist()).issubset({0, 1, 2}), f"unexpected labels: {labels}")
    _require(np.isfinite(km.centroids_).all(), "centroids contain non-finite values")
    _require(isinstance(km.clusters_, dict), "clusters_ is not a dict")
    _require(params.get("k") == 3, "missing Kmeans get_params k")
    print("OK kmeans: fit, predict, centroids, clusters, and get_params")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--task",
        choices=("voting", "stacking-regression", "kmeans", "all"),
        default="all",
        help="Smoke task to run.",
    )
    args = parser.parse_args(argv)

    tasks: dict[str, Callable[[], None]] = {
        "voting": _task_voting,
        "stacking-regression": _task_stacking_regression,
        "kmeans": _task_kmeans,
    }
    selected = tasks.keys() if args.task == "all" else (args.task,)

    for name in selected:
        tasks[name]()
    print(f"OK completed estimator_ensemble_smoke task={args.task}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 - concise nonzero smoke failure
        print(f"FAIL estimator_ensemble_smoke: {exc}", file=sys.stderr)
        raise
