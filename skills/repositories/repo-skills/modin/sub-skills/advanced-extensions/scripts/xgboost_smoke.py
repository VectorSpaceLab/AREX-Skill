#!/usr/bin/env python3
"""Tiny local-CPU Ray smoke for Modin's experimental XGBoost extension."""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic Modin distributed XGBoost smoke on the sklearn "
            "Iris dataset. Requires Ray, xgboost, and scikit-learn."
        )
    )
    parser.add_argument("--engine", choices=("Ray", "Python", "Dask"), default="Ray", help="Modin engine to request before importing modin.pandas; must be Ray.")
    parser.add_argument("--cpus", type=int, default=2, help="Small local CPU count for Ray and Modin.")
    parser.add_argument("--num-actors", type=int, default=1, help="Ray actors for tiny training; use 1 for a quick local smoke.")
    parser.add_argument("--rounds", type=int, default=1, help="Number of XGBoost boosting rounds; keep small for smoke tests.")
    return parser.parse_args()


def require_module(module_name: str, package_hint: str) -> None:
    if importlib.util.find_spec(module_name) is None:
        raise SystemExit(f"Missing optional dependency {module_name!r}. Install {package_hint} in the Modin environment before running this smoke.")


def run_smoke(args: argparse.Namespace) -> None:
    if args.engine != "Ray":
        raise SystemExit("Modin's experimental XGBoost extension currently supports only the Ray engine. Re-run with --engine Ray.")
    if args.cpus < 1:
        raise SystemExit("--cpus must be >= 1")
    if args.num_actors < 1:
        raise SystemExit("--num-actors must be >= 1")
    if args.rounds < 1:
        raise SystemExit("--rounds must be >= 1")

    require_module("ray", "the Ray extra")
    require_module("xgboost", "xgboost")
    require_module("sklearn", "scikit-learn")

    os.environ.pop("MODIN_BACKEND", None)
    os.environ["MODIN_ENGINE"] = args.engine
    os.environ["MODIN_CPUS"] = str(args.cpus)
    os.environ["MODIN_NPARTITIONS"] = str(max(args.num_actors, 1))

    import ray
    import xgboost as native_xgboost
    from sklearn.datasets import load_iris

    missing_xgb_apis = [name for name in ("RabitTracker", "rabit") if not hasattr(native_xgboost, name)]
    if missing_xgb_apis:
        raise SystemExit(
            "The installed xgboost package is importable but incompatible with this Modin XGBoost implementation; missing API(s): "
            + ", ".join(missing_xgb_apis)
            + ". Pin a compatible xgboost version or treat this extension as unavailable."
        )

    import modin.pandas as pd
    import modin.experimental.xgboost as mxgb
    from modin.config import Engine

    if Engine.get() != "Ray":
        raise RuntimeError(f"Modin XGBoost requires Ray engine; current engine is {Engine.get()!r}. Set MODIN_ENGINE=Ray before importing modin.pandas.")

    if not ray.is_initialized():
        ray.init(num_cpus=args.cpus, include_dashboard=False, ignore_reinit_error=True, log_to_driver=False)

    iris = load_iris()
    feature_names = [f"f{i}" for i in range(iris.data.shape[1])]
    feature_types = ["q"] * len(feature_names)
    X = pd.DataFrame(iris.data, columns=feature_names)
    y = pd.Series(iris.target)

    dtrain = mxgb.DMatrix(X, label=y, feature_names=feature_names, feature_types=feature_types)
    if dtrain.num_row() != len(X) or dtrain.num_col() != len(feature_names):
        raise AssertionError(f"Unexpected DMatrix shape: rows={dtrain.num_row()} cols={dtrain.num_col()}")
    if dtrain.feature_names != feature_names:
        raise AssertionError("Feature names did not round-trip through DMatrix")

    params = {"objective": "multi:softprob", "num_class": 3, "eval_metric": "mlogloss", "eta": 0.3, "max_depth": 2}
    evals_result: dict = {}
    booster = mxgb.train(
        params,
        dtrain,
        num_boost_round=args.rounds,
        evals=[(dtrain, "train")],
        evals_result=evals_result,
        num_actors=args.num_actors,
        verbose_eval=False,
    )
    predictions = booster.predict(dtrain)

    expected_shape = (len(X), 3)
    if tuple(predictions.shape) != expected_shape:
        raise AssertionError(f"Unexpected prediction shape: {tuple(predictions.shape)!r}, expected {expected_shape!r}")
    if "train" not in evals_result or "mlogloss" not in evals_result["train"]:
        raise AssertionError(f"Missing training history in evals_result: {evals_result!r}")

    print(f"XGBoost smoke passed: rows={len(X)} classes=3 rounds={args.rounds} actors={args.num_actors}")


def main() -> None:
    run_smoke(parse_args())


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"xgboost_smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
