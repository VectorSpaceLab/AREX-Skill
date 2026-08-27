#!/usr/bin/env python3
"""Tiny synthetic fairness smoke helper for mljar-supervised.

The helper does not fetch network datasets or read local CSV files. It creates a
small synthetic tabular dataset, fits `supervised.AutoML` with sensitive features,
calls `report_structured()`, and prints compact fairness signals.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import warnings
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union


CLASSIFICATION_METRICS = {
    "auto",
    "demographic_parity_difference",
    "demographic_parity_ratio",
    "equalized_odds_difference",
    "equalized_odds_ratio",
}
REGRESSION_METRICS = {"auto", "group_loss_difference", "group_loss_ratio"}


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fit a tiny synthetic fairness-aware supervised.AutoML model and "
            "print report_structured() fairness signals."
        )
    )
    parser.add_argument(
        "--task",
        choices=["binary", "multiclass", "regression"],
        default="binary",
        help="Synthetic ML task to run. Default: binary.",
    )
    parser.add_argument(
        "--metric",
        default="auto",
        help=(
            "Fairness metric name, or 'auto'. Classification: demographic_parity_* "
            "or equalized_odds_*; regression: group_loss_ratio or "
            "group_loss_difference. Default: auto."
        ),
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help=(
            "Fairness threshold. Defaults to AutoML's task/metric default. Required "
            "when --metric group_loss_difference."
        ),
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=80,
        help="Number of synthetic rows to generate. Default: 80.",
    )
    parser.add_argument(
        "--algorithm",
        default="Decision Tree",
        help="Single AutoML algorithm to use for a small smoke run. Default: Decision Tree.",
    )
    parser.add_argument(
        "--model-time-limit",
        type=int,
        default=10,
        help="Per-model time limit in seconds. Default: 10.",
    )
    parser.add_argument(
        "--two-sensitive",
        action="store_true",
        help="Include a second sensitive feature to exercise multi-column handling.",
    )
    parser.add_argument(
        "--privileged",
        default=None,
        help="Optional privileged value for the primary synthetic sensitive feature.",
    )
    parser.add_argument(
        "--underprivileged",
        default=None,
        help="Optional underprivileged value for the primary synthetic sensitive feature.",
    )
    parser.add_argument(
        "--results-path",
        default=None,
        help="Optional output directory. If omitted, a temporary directory is used.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow removing an existing --results-path before running.",
    )
    parser.add_argument(
        "--keep-results",
        action="store_true",
        help="Do not delete the temporary results directory at the end.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=123,
        help="Random seed for data generation and AutoML. Default: 123.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    allowed = REGRESSION_METRICS if args.task == "regression" else CLASSIFICATION_METRICS
    if args.metric not in allowed:
        parser.error(
            f"metric {args.metric!r} is not valid for task {args.task!r}; "
            f"allowed values are: {', '.join(sorted(allowed))}"
        )
    if args.metric == "group_loss_difference" and args.threshold is None:
        parser.error("--threshold is required when --metric group_loss_difference")
    if (args.privileged is None) ^ (args.underprivileged is None):
        parser.error("set both --privileged and --underprivileged, or omit both")
    if args.n_samples < 40:
        parser.error("--n-samples must be at least 40 for a stable split")
    return args


def build_synthetic_data(args: argparse.Namespace):
    import numpy as np
    import pandas as pd
    from sklearn.datasets import make_classification, make_regression

    rng = np.random.default_rng(args.random_state)
    n = args.n_samples

    if args.task == "binary":
        X_array, y = make_classification(
            n_samples=n,
            n_features=6,
            n_informative=4,
            n_redundant=0,
            n_classes=2,
            weights=[0.55, 0.45],
            random_state=args.random_state,
        )
        ml_task = "binary_classification"
    elif args.task == "multiclass":
        X_array, y = make_classification(
            n_samples=max(n, 60),
            n_features=7,
            n_informative=5,
            n_redundant=0,
            n_classes=3,
            n_clusters_per_class=1,
            random_state=args.random_state,
        )
        n = X_array.shape[0]
        ml_task = "multiclass_classification"
    else:
        X_array, y = make_regression(
            n_samples=n,
            n_features=6,
            n_informative=4,
            noise=15.0,
            random_state=args.random_state,
        )
        ml_task = "regression"

    X = pd.DataFrame(X_array, columns=[f"feature_{i}" for i in range(X_array.shape[1])])

    # The primary sensitive feature is categorical and balanced enough for tiny runs.
    primary = np.where(np.arange(n) % 2 == 0, "female", "male")
    # Add a small correlation with a feature so fairness values are not always identical.
    primary = np.where(X["feature_0"].to_numpy() > np.median(X["feature_0"]), primary, primary[::-1])
    sensitive_data = {"gender": primary}

    if args.two_sensitive:
        sensitive_data["region"] = np.where(
            (np.arange(n) + rng.integers(0, 2, size=n)) % 3 == 0, "urban", "rural"
        )

    sensitive_features = pd.DataFrame(sensitive_data)
    return X, y, sensitive_features, ml_task


def prepare_results_path(args: argparse.Namespace) -> Tuple[Path, bool]:
    if args.results_path is None:
        return Path(tempfile.mkdtemp(prefix="mljar-fairness-smoke-")), True

    path = Path(args.results_path).expanduser()
    if path.exists():
        if not args.overwrite:
            raise SystemExit(
                f"Results path already exists: {path}. Use --overwrite or choose a new path."
            )
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    return path, False


def compact_fairness_signals(payload: Dict[str, Any], selected_payload: Dict[str, Any]) -> Dict[str, Any]:
    leaderboard = payload.get("leaderboard") or []
    fairness_columns: List[str] = []
    if leaderboard:
        fairness_columns = [
            key
            for key in leaderboard[0].keys()
            if key == "is_fair" or key == "fairness_metric" or key.startswith("fairness_")
        ]

    selected = selected_payload.get("selected_model") or {}
    selected_metrics = selected.get("metrics") or {}
    fairness_details = selected_metrics.get("fairness_metrics_details") or {}

    return {
        "top_level_keys": sorted(payload.keys()),
        "leaderboard_rows": len(leaderboard),
        "leaderboard_fairness_columns": fairness_columns,
        "fairness_summary": payload.get("fairness_summary"),
        "selected_model_name": selected.get("name"),
        "selected_model_fairness": selected.get("fairness"),
        "selected_model_fairness_detail_keys": sorted(fairness_details.keys()),
    }


def run(args: argparse.Namespace) -> int:
    # Tiny synthetic fairness runs can trigger divide-by-zero RuntimeWarnings in
    # fairness-weight search when a group/class intersection is empty. Keep the
    # helper output focused on structured report signals.
    warnings.filterwarnings(
        "ignore", category=RuntimeWarning, message="invalid value encountered in divide"
    )
    warnings.filterwarnings(
        "ignore", category=FutureWarning, message='Value `"friedman_mse"`.*'
    )
    from supervised import AutoML

    X, y, sensitive_features, ml_task = build_synthetic_data(args)
    results_path, is_temp = prepare_results_path(args)

    fairness_threshold: Union[float, str] = args.threshold if args.threshold is not None else "auto"
    privileged_groups = "auto"
    underprivileged_groups = "auto"
    if args.privileged is not None and args.underprivileged is not None:
        privileged_groups = [{"gender": args.privileged}]
        underprivileged_groups = [{"gender": args.underprivileged}]

    try:
        validation_strategy = {
            "validation_type": "split",
            "train_ratio": 0.8,
            "shuffle": True,
        }
        if args.task != "regression":
            validation_strategy["stratify"] = True

        automl = AutoML(
            results_path=str(results_path),
            mode="Explain",
            ml_task=ml_task,
            algorithms=[args.algorithm],
            model_time_limit=args.model_time_limit,
            train_ensemble=False,
            stack_models=False,
            explain_level=0,
            validation_strategy=validation_strategy,
            start_random_models=1,
            hill_climbing_steps=0,
            top_models_to_improve=0,
            fairness_metric=args.metric,
            fairness_threshold=fairness_threshold,
            privileged_groups=privileged_groups,
            underprivileged_groups=underprivileged_groups,
            n_jobs=1,
            verbose=0,
            random_state=args.random_state,
        )
        automl.fit(X, y, sensitive_features=sensitive_features)

        payload = automl.report_structured(format="dict")
        leaderboard = payload.get("leaderboard") or []
        selected_name = leaderboard[0].get("name") if leaderboard else None
        selected_payload: Dict[str, Any] = {}
        if selected_name:
            selected_payload = automl.report_structured(format="dict", model_name=selected_name)

        signals = compact_fairness_signals(payload, selected_payload)
        print("MLJAR fairness smoke completed")
        print(f"task: {args.task} ({ml_task})")
        print(f"metric: {args.metric}")
        print(f"threshold: {fairness_threshold}")
        print(f"sensitive_features: {list(sensitive_features.columns)}")
        print(f"results_path: {results_path}")
        print(json.dumps(signals, indent=2, sort_keys=True, default=str))
        return 0
    finally:
        if is_temp and not args.keep_results:
            shutil.rmtree(results_path, ignore_errors=True)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
