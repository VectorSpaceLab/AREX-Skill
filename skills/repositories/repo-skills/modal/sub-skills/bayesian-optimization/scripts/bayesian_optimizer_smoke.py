#!/usr/bin/env python3
"""Deterministic modAL BayesianOptimizer smoke test.

Purpose:
    Verify that an installed modAL package can run short BayesianOptimizer
    loops with PI, EI, and UCB acquisition strategies, update get_max(), and
    handle both one-dimensional and multidimensional candidate grids.

Prerequisites:
    modAL-python with NumPy, SciPy, and scikit-learn installed. No network,
    credentials, downloads, plotting, or destructive writes are used.

Example:
    python bayesian_optimizer_smoke.py --budget 3
"""

from __future__ import annotations

import argparse
import functools
import sys
import traceback
import warnings
from typing import Callable, Dict, Tuple

import numpy as np


def objective_1d(X: np.ndarray) -> np.ndarray:
    """Cheap deterministic scalar objective returning shape (n_rows,)."""
    X = np.asarray(X, dtype=float).reshape(-1, 1)
    x = X[:, 0]
    return (1.25 + 0.45 * np.sin(1.7 * x) - 0.06 * (x - 0.8) ** 2).reshape(-1)


def objective_2d(X: np.ndarray) -> np.ndarray:
    """Cheap deterministic scalar objective for a two-feature grid."""
    X = np.asarray(X, dtype=float)
    if X.ndim != 2 or X.shape[1] != 2:
        raise ValueError(f"objective_2d expects shape (n, 2), got {X.shape}")
    x0, x1 = X[:, 0], X[:, 1]
    return (
        1.0
        + 0.25 * np.cos(1.5 * x0)
        + 0.20 * np.sin(1.2 * x1)
        - 0.10 * (x0 - 0.4) ** 2
        - 0.08 * (x1 + 0.5) ** 2
    ).reshape(-1)


def scalar(value: object) -> float:
    return float(np.asarray(value, dtype=float).reshape(-1)[0])


def as_2d_rows(value: object, n_features: int) -> np.ndarray:
    return np.asarray(value, dtype=float).reshape(-1, n_features)


def make_gp(n_features: int):
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import Matern

    # ARD length_scale keeps the multidimensional case explicit; optimizer=None
    # makes the smoke deterministic and fast.
    length_scale = np.ones(n_features, dtype=float)
    return GaussianProcessRegressor(
        kernel=Matern(length_scale=length_scale, nu=2.5),
        alpha=1e-6,
        normalize_y=True,
        optimizer=None,
        random_state=0,
    )


def run_strategy_loop(
    name: str,
    query_strategy: Callable,
    score_fn: Callable,
    budget: int,
) -> Tuple[np.ndarray, float, int]:
    from modAL.models import BayesianOptimizer

    X_all = np.linspace(-3.0, 3.0, 61).reshape(-1, 1)
    initial_idx = np.array([0, 30, 60])
    X_initial = X_all[initial_idx]
    y_initial = objective_1d(X_initial)
    X_pool = np.delete(X_all, initial_idx, axis=0)

    optimizer = BayesianOptimizer(
        estimator=make_gp(n_features=1),
        query_strategy=query_strategy,
        X_training=X_initial,
        y_training=y_initial,
    )

    before_x, before_y = optimizer.get_max()
    if before_x is None or not np.isfinite(scalar(before_y)):
        raise AssertionError(f"{name}: get_max() was not initialized correctly")

    evaluations = 0
    for _ in range(budget):
        scores = np.asarray(score_fn(optimizer, X_pool), dtype=float).reshape(-1)
        if scores.shape[0] != X_pool.shape[0]:
            raise AssertionError(f"{name}: score length {scores.shape[0]} != pool length {X_pool.shape[0]}")
        if not np.all(np.isfinite(scores)):
            raise AssertionError(f"{name}: acquisition scores contain non-finite values")

        query_idx, query_inst = optimizer.query(X_pool)
        query_idx = np.asarray(query_idx, dtype=int).reshape(-1)
        query_inst = as_2d_rows(query_inst, n_features=1)
        if query_inst.shape[0] != query_idx.shape[0]:
            raise AssertionError(f"{name}: queried rows and indices disagree")

        y_new = objective_1d(query_inst)
        if y_new.shape != (query_inst.shape[0],):
            raise AssertionError(f"{name}: objective returned {y_new.shape}, expected one scalar per row")

        optimizer.teach(query_inst, y_new)
        X_pool = np.delete(X_pool, query_idx, axis=0)
        evaluations += query_inst.shape[0]

    X_max, y_max = optimizer.get_max()
    X_max = as_2d_rows(X_max, n_features=1)
    y_max = scalar(y_max)
    if not np.isfinite(y_max):
        raise AssertionError(f"{name}: final y_max is not finite")
    observed_best = float(np.max(optimizer.y_training))
    if abs(y_max - observed_best) > 1e-10:
        raise AssertionError(f"{name}: get_max y={y_max} does not match observed best={observed_best}")
    return X_max, y_max, evaluations


def run_multidim_loop(budget: int) -> Tuple[np.ndarray, float, int]:
    from modAL.acquisition import max_EI, optimizer_EI
    from modAL.models import BayesianOptimizer

    axis_0 = np.linspace(-2.0, 2.0, 9)
    axis_1 = np.linspace(-2.0, 2.0, 9)
    grid_0, grid_1 = np.meshgrid(axis_0, axis_1, indexing="ij")
    X_all = np.column_stack([grid_0.ravel(), grid_1.ravel()])
    initial_idx = np.array([0, len(X_all) // 2, len(X_all) - 1])
    X_initial = X_all[initial_idx]
    y_initial = objective_2d(X_initial)
    X_pool = np.delete(X_all, initial_idx, axis=0)

    optimizer = BayesianOptimizer(
        estimator=make_gp(n_features=2),
        query_strategy=max_EI,
        X_training=X_initial,
        y_training=y_initial,
    )

    evaluations = 0
    for _ in range(max(1, min(budget, 3))):
        scores = np.asarray(optimizer_EI(optimizer, X_pool), dtype=float).reshape(-1)
        if scores.shape[0] != X_pool.shape[0] or not np.all(np.isfinite(scores)):
            raise AssertionError("2D EI scores are invalid")
        query_idx, query_inst = optimizer.query(X_pool)
        query_idx = np.asarray(query_idx, dtype=int).reshape(-1)
        query_inst = as_2d_rows(query_inst, n_features=2)
        y_new = objective_2d(query_inst)
        if y_new.shape != (query_inst.shape[0],):
            raise AssertionError("2D objective did not return shape (n_rows,)")
        optimizer.teach(query_inst, y_new)
        X_pool = np.delete(X_pool, query_idx, axis=0)
        evaluations += query_inst.shape[0]

    X_max, y_max = optimizer.get_max()
    X_max = as_2d_rows(X_max, n_features=2)
    y_max = scalar(y_max)
    if abs(y_max - float(np.max(optimizer.y_training))) > 1e-10:
        raise AssertionError("2D get_max() does not match observed best")
    return X_max, y_max, evaluations


def run_smoke(budget: int) -> Dict[str, Tuple[np.ndarray, float, int]]:
    from modAL.acquisition import (
        max_EI,
        max_PI,
        max_UCB,
        optimizer_EI,
        optimizer_PI,
        optimizer_UCB,
    )

    strategies = {
        "PI": (
            functools.partial(max_PI, tradeoff=0.03),
            functools.partial(optimizer_PI, tradeoff=0.03),
        ),
        "EI": (
            functools.partial(max_EI, tradeoff=0.03),
            functools.partial(optimizer_EI, tradeoff=0.03),
        ),
        "UCB": (
            functools.partial(max_UCB, beta=1.25),
            functools.partial(optimizer_UCB, beta=1.25),
        ),
    }

    results: Dict[str, Tuple[np.ndarray, float, int]] = {}
    for name, (query_strategy, score_fn) in strategies.items():
        results[name] = run_strategy_loop(name, query_strategy, score_fn, budget)
    results["EI_2D"] = run_multidim_loop(budget)
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a deterministic modAL BayesianOptimizer smoke test.")
    parser.add_argument(
        "--budget",
        type=int,
        default=3,
        help="Number of 1-D objective evaluations per acquisition strategy; the 2-D check uses min(budget, 3).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print a traceback on failure.",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.budget < 1 or args.budget > 10:
        parser.error("--budget must be between 1 and 10 for this smoke test")

    try:
        from sklearn.exceptions import ConvergenceWarning

        warnings.filterwarnings("ignore", category=ConvergenceWarning)
    except Exception:
        pass

    try:
        import modAL  # noqa: F401
        import sklearn  # noqa: F401
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"FAIL import: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 2

    try:
        results = run_smoke(args.budget)
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"FAIL bayesian_optimizer_smoke: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 1

    summary_parts = []
    total_evaluations = 0
    for name in ("PI", "EI", "UCB", "EI_2D"):
        X_max, y_max, evaluations = results[name]
        total_evaluations += evaluations
        x_text = np.array2string(X_max.reshape(-1), precision=3, separator=",")
        summary_parts.append(f"{name}.get_max=({x_text}, {y_max:.6f})")

    print(
        "PASS bayesian_optimizer_smoke "
        + " ".join(summary_parts)
        + f" objective_evaluations={total_evaluations}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
