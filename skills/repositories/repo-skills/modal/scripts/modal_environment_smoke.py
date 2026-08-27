#!/usr/bin/env python3
"""Small installed-package smoke for the modAL repo skill.

This helper imports the public `modAL` package, checks the distribution name
`modAL-python`, and runs tiny ActiveLearner, Committee, and BayesianOptimizer
operations. It does not read the original repository checkout, download data,
use credentials, train large models, or require a GPU.
"""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version

import numpy as np


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def active_learner_check() -> None:
    from sklearn.datasets import load_iris
    from sklearn.ensemble import RandomForestClassifier

    from modAL.models import ActiveLearner
    from modAL.uncertainty import entropy_sampling

    iris = load_iris()
    X, y = iris.data, iris.target
    init_idx = np.array([0, 1, 50, 51, 100, 101])
    pool_idx = np.setdiff1d(np.arange(len(X)), init_idx)[:20]

    learner = ActiveLearner(
        estimator=RandomForestClassifier(n_estimators=10, random_state=0),
        query_strategy=entropy_sampling,
        X_training=X[init_idx],
        y_training=y[init_idx],
    )
    query_idx, query_rows, metrics = learner.query(X[pool_idx], return_metrics=True)
    selected = int(np.ravel(query_idx)[0])
    require(metrics is not None, "entropy_sampling should return metrics through learner.query")
    require(np.asarray(query_rows).shape[-1] == X.shape[1], "query should return feature rows")
    learner.teach(X[pool_idx[selected]].reshape(1, -1), np.array([y[pool_idx[selected]]]))
    require(learner.X_training.shape[0] == len(init_idx) + 1, "teach should append one labeled row")


def committee_check() -> None:
    from sklearn.datasets import load_iris
    from sklearn.tree import DecisionTreeClassifier

    from modAL.models import ActiveLearner, Committee

    iris = load_iris()
    X, y = iris.data, iris.target
    idx_a = np.r_[np.where(y == 0)[0][:8], np.where(y == 1)[0][:8]]
    idx_b = np.r_[np.where(y == 1)[0][:8], np.where(y == 2)[0][:8]]
    learners = [
        ActiveLearner(DecisionTreeClassifier(max_depth=3, random_state=1), X_training=X[idx_a], y_training=y[idx_a]),
        ActiveLearner(DecisionTreeClassifier(max_depth=3, random_state=2), X_training=X[idx_b], y_training=y[idx_b]),
    ]
    committee = Committee(learners)
    require(tuple(committee.classes_.tolist()) == (0, 1, 2), "Committee should union learner classes")
    require(committee.vote_proba(X[:4]).shape == (4, 2, 3), "vote_proba should expose rows x learners x classes")


def bayesian_check() -> None:
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import Matern

    from modAL.acquisition import max_EI
    from modAL.models import BayesianOptimizer

    X_all = np.linspace(-1.0, 1.0, 21).reshape(-1, 1)
    objective = lambda X: (1.0 - (np.asarray(X).reshape(-1) - 0.25) ** 2).reshape(-1)
    init_idx = np.array([0, 10, 20])
    optimizer = BayesianOptimizer(
        estimator=GaussianProcessRegressor(kernel=Matern(length_scale=1.0), optimizer=None, normalize_y=True),
        query_strategy=max_EI,
        X_training=X_all[init_idx],
        y_training=objective(X_all[init_idx]),
    )
    X_pool = np.delete(X_all, init_idx, axis=0)
    query_idx, query_rows = optimizer.query(X_pool)
    optimizer.teach(np.asarray(query_rows).reshape(-1, 1), objective(query_rows))
    X_max, y_max = optimizer.get_max()
    require(X_max is not None and np.isfinite(float(np.asarray(y_max).reshape(-1)[0])), "get_max should be finite")


def optional_import_check() -> str:
    try:
        import torch  # noqa: F401
        import skorch  # noqa: F401
        import modAL.dropout  # noqa: F401
    except Exception as exc:
        return f"optional-deep-unavailable:{type(exc).__name__}:{exc}"
    return "optional-deep-imports-ok"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a small installed-package modAL smoke test.")
    parser.add_argument(
        "--include-optional-deep",
        action="store_true",
        help="Also import torch, skorch, and modAL.dropout if the optional stack is installed.",
    )
    args = parser.parse_args(argv)

    try:
        dist_version = version("modAL-python")
    except PackageNotFoundError:
        print("FAIL: distribution metadata for modAL-python was not found", file=sys.stderr)
        return 2

    try:
        import modAL  # noqa: F401

        active_learner_check()
        committee_check()
        bayesian_check()
        optional_status = optional_import_check() if args.include_optional_deep else "optional-deep-not-requested"
    except Exception as exc:
        print(f"FAIL modal_environment_smoke: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"PASS modal_environment_smoke modAL-python={dist_version} {optional_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
