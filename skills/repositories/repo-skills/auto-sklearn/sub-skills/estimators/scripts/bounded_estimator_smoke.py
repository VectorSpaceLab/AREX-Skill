#!/usr/bin/env python3
"""Dry-run-first bounded smoke helper for auto-sklearn estimators.

The default mode prints the planned workflow without importing auto-sklearn or
running AutoML. Add --run to execute a small classification or regression fit.
This is a smoke check only; it does not prove model quality.
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
from pprint import pprint
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Plan or run a bounded auto-sklearn estimator smoke. By default this "
            "only prints the planned workflow; pass --run to execute AutoML."
        )
    )
    parser.add_argument(
        "--task",
        choices=("classification", "regression"),
        default="classification",
        help="Estimator workflow to smoke (default: classification).",
    )
    parser.add_argument(
        "--time-left",
        type=int,
        default=60,
        help="time_left_for_this_task in seconds for --run mode (default: 60).",
    )
    parser.add_argument(
        "--per-run-time-limit",
        type=int,
        default=15,
        help="per_run_time_limit in seconds for --run mode (default: 15).",
    )
    parser.add_argument(
        "--tmp-dir",
        type=Path,
        default=None,
        help=(
            "Directory for auto-sklearn temporary output. If omitted in --run "
            "mode, a fresh temporary directory is created."
        ),
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Actually import auto-sklearn and run the bounded smoke fit.",
    )
    return parser


def planned_workflow(args: argparse.Namespace) -> dict[str, Any]:
    dataset = "breast_cancer" if args.task == "classification" else "diabetes"
    estimator = "AutoSklearnClassifier" if args.task == "classification" else "AutoSklearnRegressor"
    metric = "accuracy_score" if args.task == "classification" else "r2_score"
    tmp_dir = str(args.tmp_dir) if args.tmp_dir is not None else "<fresh temporary directory>"
    return {
        "mode": "execute" if args.run else "dry-run",
        "task": args.task,
        "dataset": dataset,
        "estimator": estimator,
        "time_left_for_this_task": args.time_left,
        "per_run_time_limit": args.per_run_time_limit,
        "tmp_folder": tmp_dir,
        "delete_tmp_folder_after_terminate": False,
        "post_fit_checks": [
            "predict shape",
            metric,
            "sprint_statistics()",
            "leaderboard(top_k=5, ensemble_only=True)",
        ],
    }


def _prepare_tmp_dir(args: argparse.Namespace) -> Path:
    if args.tmp_dir is None:
        path = Path(tempfile.mkdtemp(prefix="autosklearn_bounded_smoke_"))
    else:
        path = args.tmp_dir
        path.mkdir(parents=True, exist_ok=True)
    return path


def run_classification(args: argparse.Namespace) -> None:
    import autosklearn.classification
    import sklearn.datasets
    import sklearn.metrics
    import sklearn.model_selection

    X, y = sklearn.datasets.load_breast_cancer(return_X_y=True)
    X_train, X_test, y_train, y_test = sklearn.model_selection.train_test_split(
        X, y, random_state=1, stratify=y
    )
    tmp_dir = _prepare_tmp_dir(args)

    automl = autosklearn.classification.AutoSklearnClassifier(
        time_left_for_this_task=args.time_left,
        per_run_time_limit=args.per_run_time_limit,
        seed=1,
        tmp_folder=str(tmp_dir),
        delete_tmp_folder_after_terminate=False,
        disable_evaluator_output=False,
        load_models=True,
    )
    automl.fit(X_train, y_train, dataset_name="breast_cancer_smoke")

    predictions = automl.predict(X_test)
    probabilities = automl.predict_proba(X_test)
    print("Prediction shape:", predictions.shape)
    print("Probability shape:", probabilities.shape)
    print("Accuracy:", sklearn.metrics.accuracy_score(y_test, predictions))
    print("Sprint statistics:")
    print(automl.sprint_statistics())
    print("Leaderboard:")
    print(automl.leaderboard(top_k=5, ensemble_only=True))
    print("Temporary folder preserved at:", tmp_dir)


def run_regression(args: argparse.Namespace) -> None:
    import autosklearn.regression
    import sklearn.datasets
    import sklearn.metrics
    import sklearn.model_selection

    X, y = sklearn.datasets.load_diabetes(return_X_y=True)
    X_train, X_test, y_train, y_test = sklearn.model_selection.train_test_split(
        X, y, random_state=1
    )
    tmp_dir = _prepare_tmp_dir(args)

    automl = autosklearn.regression.AutoSklearnRegressor(
        time_left_for_this_task=args.time_left,
        per_run_time_limit=args.per_run_time_limit,
        seed=1,
        tmp_folder=str(tmp_dir),
        delete_tmp_folder_after_terminate=False,
        disable_evaluator_output=False,
        load_models=True,
    )
    automl.fit(X_train, y_train, dataset_name="diabetes_smoke")

    train_predictions = automl.predict(X_train)
    test_predictions = automl.predict(X_test)
    print("Train prediction shape:", train_predictions.shape)
    print("Test prediction shape:", test_predictions.shape)
    print("Train R2:", sklearn.metrics.r2_score(y_train, train_predictions))
    print("Test R2:", sklearn.metrics.r2_score(y_test, test_predictions))
    print("Sprint statistics:")
    print(automl.sprint_statistics())
    print("Leaderboard:")
    print(automl.leaderboard(top_k=5, ensemble_only=True))
    print("Temporary folder preserved at:", tmp_dir)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    plan = planned_workflow(args)
    print("Planned bounded estimator smoke:")
    pprint(plan, indent=2, sort_dicts=False)

    if not args.run:
        print("\nDry-run only. Re-run with --run to execute the bounded AutoML fit.")
        return 0

    if args.time_left <= 0 or args.per_run_time_limit <= 0:
        parser.error("--time-left and --per-run-time-limit must be positive in --run mode")
    if args.per_run_time_limit > args.time_left:
        print("Warning: --per-run-time-limit is greater than --time-left; the total task limit dominates.")

    if args.task == "classification":
        run_classification(args)
    else:
        run_regression(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
