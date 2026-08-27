#!/usr/bin/env python3
"""Safe synthetic smoke helper for supervised.AutoML.

Runs from any working directory. It does not read network resources and does not
refer to the source repository checkout. Use --help for options.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


TASK_TO_ML_TASK = {
    "binary": "binary_classification",
    "multiclass": "multiclass_classification",
    "regression": "regression",
}


SAFE_DEFAULT_ALGORITHMS = "Baseline"


def parse_algorithms(value: str) -> List[str]:
    algorithms = [part.strip() for part in value.split(",") if part.strip()]
    if not algorithms:
        raise argparse.ArgumentTypeError("at least one algorithm name is required")
    return algorithms


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Train a tiny no-network supervised.AutoML model on synthetic data "
            "and assert fit/predict/predict_proba-or-regression-error/"
            "predict_all/score/need_retrain signals."
        )
    )
    parser.add_argument(
        "--task",
        choices=sorted(TASK_TO_ML_TASK),
        default="binary",
        help="Synthetic task to run (default: binary).",
    )
    parser.add_argument(
        "--results-path",
        type=Path,
        default=None,
        help=(
            "Directory for AutoML results. If omitted, a temporary directory is "
            "created and removed unless --keep-results is set."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Delete an existing --results-path before training.",
    )
    parser.add_argument(
        "--keep-results",
        action="store_true",
        help="Keep the temporary results directory when --results-path is omitted.",
    )
    parser.add_argument(
        "--algorithms",
        type=parse_algorithms,
        default=parse_algorithms(SAFE_DEFAULT_ALGORITHMS),
        help=(
            "Comma-separated AutoML algorithm names. Default: Baseline. "
            "Example: --algorithms 'Baseline,Decision Tree'"
        ),
    )
    parser.add_argument(
        "--mode",
        choices=["Explain", "Perform", "Compete", "Optuna"],
        default="Explain",
        help="AutoML mode. Defaults to Explain for a bounded smoke.",
    )
    parser.add_argument(
        "--allow-expensive",
        action="store_true",
        help="Allow mode=Optuna. Without this flag the helper refuses Optuna.",
    )
    parser.add_argument(
        "--total-time-limit",
        type=int,
        default=30,
        help="Overall training limit in seconds when model_time_limit is unset.",
    )
    parser.add_argument(
        "--model-time-limit",
        type=int,
        default=None,
        help="Optional per-model limit in seconds. If set, AutoML ignores total_time_limit.",
    )
    parser.add_argument(
        "--optuna-time-budget",
        type=int,
        default=10,
        help="Per-algorithm Optuna budget in seconds when --mode Optuna is allowed.",
    )
    parser.add_argument(
        "--explain-level",
        type=int,
        choices=[0, 1, 2],
        default=0,
        help="AutoML explain_level. Default 0 avoids expensive explanations.",
    )
    parser.add_argument(
        "--eval-metric",
        default="auto",
        help="AutoML eval_metric string. Default: auto.",
    )
    parser.add_argument(
        "--validation",
        choices=["split", "kfold", "auto"],
        default="split",
        help="Validation strategy for the smoke. Default: split.",
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.75,
        help="Train ratio for split validation.",
    )
    parser.add_argument(
        "--k-folds",
        type=int,
        default=3,
        help="Number of folds for kfold validation.",
    )
    parser.add_argument(
        "--no-stratify",
        action="store_true",
        help="Disable stratification for classification split/kfold validation.",
    )
    parser.add_argument(
        "--train-ensemble",
        action="store_true",
        help="Enable AutoML ensembling. Default is disabled for a fast smoke.",
    )
    parser.add_argument(
        "--stack-models",
        action="store_true",
        help="Enable stacking. Default is disabled for a fast smoke.",
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=None,
        help="Synthetic sample count. Defaults are task-specific and small.",
    )
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=1,
        help="CPU parallelism for AutoML. Default 1 for predictable smokes.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=123,
        help="Random seed for synthetic data and AutoML.",
    )
    parser.add_argument(
        "--verbose",
        type=int,
        default=0,
        help="AutoML verbose level. Default 0 keeps smoke output compact.",
    )
    return parser


def prepare_results_path(path: Optional[Path], overwrite: bool, task: str) -> Tuple[Path, bool]:
    """Return (results_path, is_temporary)."""
    if path is None:
        temp_dir = Path(tempfile.mkdtemp(prefix=f"mljar-automl-{task}-"))
        return temp_dir, True

    path = path.expanduser().resolve()
    if path.exists():
        if overwrite:
            shutil.rmtree(path)
        elif any(path.iterdir()):
            raise SystemExit(
                f"Refusing to use non-empty results path without --overwrite: {path}"
            )
    path.mkdir(parents=True, exist_ok=True)
    return path, False


def make_synthetic_data(task: str, n_samples: Optional[int], random_state: int):
    import pandas as pd
    from sklearn.datasets import make_classification, make_regression
    from sklearn.model_selection import train_test_split

    if task == "binary":
        n = n_samples or 96
        X, y = make_classification(
            n_samples=n,
            n_features=6,
            n_informative=4,
            n_redundant=1,
            n_classes=2,
            n_clusters_per_class=1,
            random_state=random_state,
        )
        stratify = y
    elif task == "multiclass":
        n = n_samples or 120
        X, y = make_classification(
            n_samples=n,
            n_features=8,
            n_informative=5,
            n_redundant=1,
            n_classes=3,
            n_clusters_per_class=1,
            random_state=random_state,
        )
        stratify = y
    else:
        n = n_samples or 96
        X, y = make_regression(
            n_samples=n,
            n_features=6,
            n_informative=5,
            noise=5.0,
            random_state=random_state,
        )
        stratify = None

    X = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(X.shape[1])])
    return train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=random_state,
        stratify=stratify,
    )


def build_validation_strategy(args: argparse.Namespace):
    if args.validation == "auto":
        return "auto"
    if args.validation == "split":
        strategy = {
            "validation_type": "split",
            "train_ratio": args.train_ratio,
            "shuffle": True,
        }
    else:
        strategy = {
            "validation_type": "kfold",
            "k_folds": args.k_folds,
            "shuffle": True,
            "random_seed": args.random_state,
        }
    if args.task != "regression" and not args.no_stratify:
        strategy["stratify"] = True
    return strategy


def finite_float(value) -> bool:
    try:
        return math.isfinite(float(value))
    except Exception:
        return False


def run_smoke(args: argparse.Namespace) -> int:
    if args.mode == "Optuna" and not args.allow_expensive:
        raise SystemExit(
            "Refusing mode=Optuna without --allow-expensive. "
            "Optuna can spend a per-algorithm budget."
        )

    try:
        import numpy as np
        import pandas as pd
        import supervised
        from supervised import AutoML
    except Exception as exc:  # pragma: no cover - depends on environment
        raise SystemExit(f"Failed to import supervised AutoML dependencies: {exc}")

    results_path, is_temporary = prepare_results_path(
        args.results_path, args.overwrite, args.task
    )

    try:
        X_train, X_test, y_train, y_test = make_synthetic_data(
            args.task, args.n_samples, args.random_state
        )
        validation_strategy = build_validation_strategy(args)

        automl_kwargs = {
            "results_path": str(results_path),
            "total_time_limit": args.total_time_limit,
            "mode": args.mode,
            "ml_task": TASK_TO_ML_TASK[args.task],
            "model_time_limit": args.model_time_limit,
            "algorithms": args.algorithms,
            "train_ensemble": args.train_ensemble,
            "stack_models": args.stack_models,
            "eval_metric": args.eval_metric,
            "validation_strategy": validation_strategy,
            "explain_level": args.explain_level,
            "golden_features": False,
            "features_selection": False,
            "start_random_models": 1,
            "hill_climbing_steps": 0,
            "top_models_to_improve": 0,
            "boost_on_errors": False,
            "kmeans_features": False,
            "mix_encoding": False,
            "n_jobs": args.n_jobs,
            "verbose": args.verbose,
            "random_state": args.random_state,
        }
        if args.mode == "Optuna":
            automl_kwargs["optuna_time_budget"] = args.optuna_time_budget

        print(
            "SIGNAL config "
            + json.dumps(
                {
                    "task": args.task,
                    "ml_task": TASK_TO_ML_TASK[args.task],
                    "mode": args.mode,
                    "algorithms": args.algorithms,
                    "validation": validation_strategy,
                    "results_path": str(results_path),
                    "supervised_version": getattr(supervised, "__version__", "unknown"),
                },
                sort_keys=True,
            )
        )

        automl = AutoML(**automl_kwargs)
        fit_result = automl.fit(X_train, y_train)
        assert fit_result is automl, "fit() should return self"
        print("ASSERT fit_returned_self ok")

        predictions = automl.predict(X_test)
        assert len(predictions) == len(X_test), "predict length mismatch"
        print(f"ASSERT predict_length ok rows={len(predictions)}")

        all_predictions = automl.predict_all(X_test)
        assert isinstance(all_predictions, pd.DataFrame), "predict_all is not a DataFrame"
        assert len(all_predictions) == len(X_test), "predict_all length mismatch"

        if args.task == "regression":
            assert "prediction" in all_predictions.columns, "missing regression prediction column"
            try:
                automl.predict_proba(X_test)
            except Exception as exc:
                msg = str(exc).lower()
                assert "classification" in msg and "predict_proba" in msg, msg
                print("ASSERT regression_predict_proba_error ok")
            else:  # pragma: no cover - indicates package behavior changed
                raise AssertionError("predict_proba unexpectedly succeeded for regression")
        else:
            assert "label" in all_predictions.columns, "missing classification label column"
            probabilities = automl.predict_proba(X_test)
            expected_classes = len(set(y_train))
            assert probabilities.shape == (
                len(X_test),
                expected_classes,
            ), f"unexpected probability shape {probabilities.shape}"
            row_sums = np.sum(probabilities, axis=1)
            assert np.allclose(row_sums, 1.0, atol=1e-5), "probabilities do not sum to one"
            print(
                f"ASSERT predict_proba_shape ok rows={probabilities.shape[0]} classes={probabilities.shape[1]}"
            )

        print(
            "ASSERT predict_all ok "
            + json.dumps(
                {"rows": int(all_predictions.shape[0]), "columns": list(all_predictions.columns)},
                sort_keys=True,
            )
        )

        score = automl.score(X_test, y_test)
        assert finite_float(score), f"score is not finite: {score!r}"
        print(f"ASSERT score_finite ok value={float(score):.6f}")

        retrain_flag = automl.need_retrain(X_test, y_test)
        assert isinstance(bool(retrain_flag), bool), "need_retrain did not return bool-like value"
        print(f"ASSERT need_retrain_bool ok value={bool(retrain_flag)}")

        print("SMOKE PASSED")
        return 0
    finally:
        if is_temporary and not args.keep_results:
            shutil.rmtree(results_path, ignore_errors=True)


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_smoke(args)


if __name__ == "__main__":
    raise SystemExit(main())
