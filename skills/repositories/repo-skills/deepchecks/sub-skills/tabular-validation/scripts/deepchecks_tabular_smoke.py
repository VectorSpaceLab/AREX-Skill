#!/usr/bin/env python
"""Safe Deepchecks tabular smoke helper.

Creates tiny in-memory pandas DataFrames, wraps them in deepchecks.tabular.Dataset,
trains a small sklearn Pipeline, and optionally runs selected tabular suites. The
script performs no downloads, credential use, or report writes unless --html-out
is supplied explicitly.
"""
from __future__ import annotations

import argparse
import os
import warnings
from pathlib import Path
from typing import Dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a safe tiny Deepchecks tabular Dataset/suite smoke test."
    )
    parser.add_argument(
        "--suite",
        choices=("data-integrity", "train-test-validation", "model-evaluation", "all"),
        default="data-integrity",
        help="Which suite to run after constructing data/model objects (default: data-integrity).",
    )
    parser.add_argument(
        "--skip-run",
        action="store_true",
        help="Only verify imports, construct Dataset objects, and fit the tiny sklearn model.",
    )
    parser.add_argument(
        "--predictions-only",
        action="store_true",
        help="For model-evaluation/all, pass y_pred/y_proba arrays instead of the fitted model object.",
    )
    parser.add_argument(
        "--html-out",
        type=Path,
        default=None,
        help="Optional path for saving the last SuiteResult as standalone HTML. No file is written by default.",
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=40,
        help="Number of synthetic rows to generate before splitting (default: 40).",
    )
    return parser.parse_args()


def _one_hot_encoder():
    from sklearn.preprocessing import OneHotEncoder

    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:  # older scikit-learn
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def build_objects(n_samples: int):
    if n_samples < 12:
        raise ValueError("--n-samples must be at least 12 so both classes appear in train/test splits")

    # Avoid Deepchecks latest-version network checks in smoke contexts and keep
    # known dependency deprecation noise out of smoke output.
    os.environ.setdefault("DISABLE_LATEST_VERSION_CHECK", "True")
    warnings.filterwarnings(
        "ignore",
        message="pkg_resources is deprecated as an API.*",
        category=UserWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message="Downcasting object dtype arrays on .*",
        category=FutureWarning,
    )

    import numpy as np
    import pandas as pd
    from sklearn.compose import ColumnTransformer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline

    from deepchecks.tabular import Dataset

    rng = np.random.default_rng(7)
    idx = np.arange(n_samples)
    segment = np.array(["low", "mid", "high", "mid"] * ((n_samples // 4) + 1))[:n_samples]
    numeric_signal = np.sin(idx / 3.0) + rng.normal(0, 0.05, size=n_samples)
    numeric_noise = rng.normal(0, 1, size=n_samples)
    target = ((numeric_signal + (segment == "high") * 0.35) > 0.05).astype(int)

    df = pd.DataFrame(
        {
            "sample_id": idx,
            "event_time": pd.Timestamp("2024-01-01") + pd.to_timedelta(idx, unit="D"),
            "numeric_signal": numeric_signal,
            "numeric_noise": numeric_noise,
            "segment": segment,
            "target": target,
        }
    )

    train_df, test_df = train_test_split(
        df,
        test_size=0.35,
        random_state=13,
        stratify=df["target"],
    )
    train_df = train_df.sort_values("sample_id").copy()
    test_df = test_df.sort_values("sample_id").copy()
    # Static-prediction mode validates by DataFrame index, so keep train/test
    # indexes disjoint even though the meaningful sample id is a regular column.
    train_df.index = [f"train-{sample_id}" for sample_id in train_df["sample_id"]]
    test_df.index = [f"test-{sample_id}" for sample_id in test_df["sample_id"]]

    feature_cols = ["numeric_signal", "numeric_noise", "segment"]
    cat_cols = ["segment"]

    train_ds = Dataset(
        train_df,
        label="target",
        features=feature_cols,
        cat_features=cat_cols,
        index_name="sample_id",
        datetime_name="event_time",
        label_type="binary",
        dataset_name="Train",
    )
    test_ds = Dataset(
        test_df,
        label="target",
        features=feature_cols,
        cat_features=cat_cols,
        index_name="sample_id",
        datetime_name="event_time",
        label_type="binary",
        dataset_name="Test",
    )

    model = Pipeline(
        steps=[
            (
                "preprocess",
                ColumnTransformer(
                    transformers=[
                        ("category", _one_hot_encoder(), cat_cols),
                        ("numeric", "passthrough", ["numeric_signal", "numeric_noise"]),
                    ]
                ),
            ),
            ("model", LogisticRegression(max_iter=200, random_state=3)),
        ]
    )
    model.fit(train_ds.features_columns, train_ds.label_col)

    feature_importance = pd.Series(
        {"numeric_signal": 0.60, "numeric_noise": 0.20, "segment": 0.20},
        dtype=float,
    )

    return train_ds, test_ds, model, feature_importance


def run_suites(args: argparse.Namespace, train_ds, test_ds, model, feature_importance) -> Dict[str, object]:
    from deepchecks.tabular.suites import data_integrity, model_evaluation, train_test_validation

    outputs: Dict[str, object] = {}

    if args.suite in ("data-integrity", "all"):
        outputs["data-integrity"] = data_integrity(n_samples=args.n_samples, random_state=42).run(
            train_dataset=train_ds,
            with_display=False,
        )

    if args.suite in ("train-test-validation", "all"):
        outputs["train-test-validation"] = train_test_validation(n_samples=args.n_samples, random_state=42).run(
            train_dataset=train_ds,
            test_dataset=test_ds,
            with_display=False,
        )

    if args.suite in ("model-evaluation", "all"):
        suite = model_evaluation(n_samples=args.n_samples, random_state=42)
        if args.predictions_only:
            y_pred_train = model.predict(train_ds.features_columns)
            y_pred_test = model.predict(test_ds.features_columns)
            y_proba_train = model.predict_proba(train_ds.features_columns)
            y_proba_test = model.predict_proba(test_ds.features_columns)
            outputs["model-evaluation"] = suite.run(
                train_dataset=train_ds,
                test_dataset=test_ds,
                y_pred_train=y_pred_train,
                y_pred_test=y_pred_test,
                y_proba_train=y_proba_train,
                y_proba_test=y_proba_test,
                model_classes=[0, 1],
                feature_importance=feature_importance,
                with_display=False,
            )
        else:
            outputs["model-evaluation"] = suite.run(
                train_dataset=train_ds,
                test_dataset=test_ds,
                model=model,
                feature_importance=feature_importance,
                feature_importance_timeout=0,
                with_display=False,
            )

    return outputs


def summarize_result(name: str, result: object) -> str:
    total = len(getattr(result, "results", []))
    not_ran = len(result.get_not_ran_checks()) if hasattr(result, "get_not_ran_checks") else 0
    try:
        passed = result.passed(fail_if_warning=True, fail_if_check_not_run=False)
    except Exception as exc:  # pragma: no cover - defensive summary only
        passed = f"unavailable ({exc.__class__.__name__})"
    return f"{name}: total_results={total} not_ran={not_ran} passed={passed}"


def main() -> int:
    args = parse_args()
    train_ds, test_ds, model, feature_importance = build_objects(args.n_samples)

    print(
        "constructed: "
        f"train_rows={train_ds.n_samples} test_rows={test_ds.n_samples} "
        f"features={train_ds.features} cat_features={train_ds.cat_features} "
        f"model={type(model).__name__}"
    )

    if args.skip_run:
        print("skip-run requested: imports, Dataset construction, and model fit succeeded")
        return 0

    outputs = run_suites(args, train_ds, test_ds, model, feature_importance)
    for name, result in outputs.items():
        print(summarize_result(name, result))

    if args.html_out is not None:
        if not outputs:
            raise RuntimeError("No SuiteResult was produced; cannot write --html-out")
        last_name, last_result = next(reversed(outputs.items()))
        args.html_out.parent.mkdir(parents=True, exist_ok=True)
        last_result.save_as_html(str(args.html_out), as_widget=False, connected=False)
        print(f"saved_html={args.html_out} suite={last_name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
