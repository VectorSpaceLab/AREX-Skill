#!/usr/bin/env python3
"""Tiny deterministic scikit-learn HPO diagnostic for bayesian-optimization."""

from __future__ import annotations

import argparse
import math

import numpy as np
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import log_loss
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

from bayes_opt import BayesianOptimization

try:
    from importlib.metadata import version
except ImportError:  # pragma: no cover - Python 3.9+ normally has this
    version = None  # type: ignore[assignment]


def make_tiny_data(seed: int, n_samples: int) -> tuple[np.ndarray, np.ndarray]:
    return make_classification(
        n_samples=n_samples,
        n_features=12,
        n_informative=6,
        n_redundant=2,
        n_classes=2,
        random_state=seed,
    )


def validate_best(best: dict | None, expected_keys: set[str]) -> None:
    if best is None:
        raise AssertionError("optimizer.max is None")
    if set(best["params"]) != expected_keys:
        raise AssertionError(f"unexpected best params keys: {best!r}")
    if not math.isfinite(float(best["target"])):
        raise AssertionError(f"non-finite target: {best!r}")


def run_accuracy_hpo(args: argparse.Namespace) -> BayesianOptimization:
    X, y = make_tiny_data(args.seed, args.samples)
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=args.seed)

    def rf_accuracy(n_estimators_float: float, min_samples_split_float: float, max_features: float) -> float:
        # Float suggestions are cast/clipped before constructing the estimator.
        n_estimators = int(np.clip(round(n_estimators_float), 4, 24))
        min_samples_split = int(np.clip(round(min_samples_split_float), 2, 10))
        max_features_safe = float(np.clip(max_features, 0.25, 1.0))
        estimator = RandomForestClassifier(
            n_estimators=n_estimators,
            min_samples_split=min_samples_split,
            max_features=max_features_safe,
            random_state=args.seed,
            n_jobs=1,
        )
        scores = cross_val_score(estimator, X, y, scoring="accuracy", cv=cv, n_jobs=1)
        return float(scores.mean())  # accuracy is already larger-is-better

    pbounds = {
        "n_estimators_float": (4.0, 24.0),
        "min_samples_split_float": (2.0, 10.0),
        "max_features": (0.25, 1.0),
    }
    optimizer = BayesianOptimization(f=rf_accuracy, pbounds=pbounds, random_state=args.seed, verbose=args.verbose)
    optimizer.maximize(init_points=args.init_points, n_iter=args.n_iter)
    validate_best(optimizer.max, set(pbounds))
    if not (0.0 <= float(optimizer.max["target"]) <= 1.0):
        raise AssertionError(f"accuracy target outside [0, 1]: {optimizer.max!r}")
    return optimizer


def run_neg_loss_demo(args: argparse.Namespace) -> tuple[dict[str, float], float, float]:
    X, y = make_tiny_data(args.seed + 1, max(80, args.samples // 2))
    X_train, X_valid, y_train, y_valid = train_test_split(
        X,
        y,
        test_size=0.35,
        stratify=y,
        random_state=args.seed,
    )

    def rf_neg_log_loss(n_estimators_float: float, max_depth_float: float) -> float:
        # This objective demonstrates minimizing a positive loss by returning -loss.
        n_estimators = int(np.clip(round(n_estimators_float), 4, 20))
        max_depth = int(np.clip(round(max_depth_float), 1, 6))
        estimator = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=args.seed + 1,
            n_jobs=1,
        )
        estimator.fit(X_train, y_train)
        probabilities = estimator.predict_proba(X_valid)
        loss = log_loss(y_valid, probabilities, labels=[0, 1])
        return -float(loss)

    pbounds = {"n_estimators_float": (4.0, 20.0), "max_depth_float": (1.0, 6.0)}
    optimizer = BayesianOptimization(f=rf_neg_log_loss, pbounds=pbounds, random_state=args.seed + 1, verbose=0)
    optimizer.maximize(init_points=max(1, args.init_points), n_iter=max(1, args.n_iter))
    validate_best(optimizer.max, set(pbounds))
    best_target = float(optimizer.max["target"])
    best_loss = -best_target
    if best_loss < 0 or not math.isfinite(best_loss):
        raise AssertionError(f"invalid flipped loss: target={best_target!r} loss={best_loss!r}")
    return optimizer.max["params"], best_target, best_loss


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny deterministic scikit-learn HPO smoke check using BayesianOptimization. "
            "Uses synthetic data only and writes no plot files."
        ),
    )
    parser.add_argument("--seed", type=int, default=21, help="Random seed for data and optimizer.")
    parser.add_argument("--samples", type=int, default=120, help="Synthetic sample count; minimum 60.")
    parser.add_argument("--init-points", type=int, default=2, help="Random initialization points.")
    parser.add_argument("--n-iter", type=int, default=2, help="Acquisition-driven iterations.")
    parser.add_argument("--verbose", type=int, default=0, choices=[0, 1, 2], help="Optimizer verbosity.")
    parser.add_argument(
        "--skip-loss-demo",
        action="store_true",
        help="Skip the separate negative-log-loss sign-handling demonstration.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.samples < 60:
        raise SystemExit("--samples must be at least 60")
    if args.init_points < 0 or args.n_iter < 0:
        raise SystemExit("--init-points and --n-iter must be non-negative")

    score_optimizer = run_accuracy_hpo(args)
    best_score = float(score_optimizer.max["target"])

    message = (
        "PASS sklearn_hpo_smoke "
        f"observations={len(score_optimizer.res)} best_accuracy={best_score:.4f}"
    )

    if not args.skip_loss_demo:
        _, best_target, best_loss = run_neg_loss_demo(args)
        message += f" neg_loss_target={best_target:.4f} flipped_loss={best_loss:.4f}"

    package_version = version("bayesian-optimization") if version else "unknown"
    message += f" version={package_version}"
    print(message)


if __name__ == "__main__":
    main()
