#!/usr/bin/env python3
"""Run a bounded Lazy Predict supervised smoke test.

Examples:
    python scripts/smoke_supervised.py --task both --max-models 1
    python scripts/smoke_supervised.py --task classification --with-categorical

The script uses sklearn toy datasets and explicit small estimator lists. It does
not need the Lazy Predict source repository.
"""

from __future__ import annotations

import argparse
import json
import sys

import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer, load_diabetes
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import train_test_split

from lazypredict.Supervised import LazyClassifier, LazyRegressor


def classification(with_categorical: bool, max_models: int) -> dict:
    X, y = load_breast_cancer(return_X_y=True)
    X = X[:, :6]
    if with_categorical:
        df = pd.DataFrame(X, columns=[f"num_{i}" for i in range(X.shape[1])])
        df["bool_signal"] = df["num_0"] > df["num_0"].median()
        df["cat_low"] = np.where(df["num_1"] > df["num_1"].median(), "high", "low")
        X = df
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=7)
    clf = LazyClassifier(
        verbose=0,
        ignore_warnings=True,
        predictions=True,
        classifiers=[LogisticRegression],
        max_models=max_models,
        categorical_encoder="onehot",
    )
    scores, predictions = clf.fit(X_train, X_test, y_train, y_test)
    assert not scores.empty, "classification scores are empty"
    assert "Balanced Accuracy" in scores.columns, "missing Balanced Accuracy column"
    assert not predictions.empty, "predictions=True should return predictions"
    return {
        "task": "classification",
        "models": list(map(str, scores.index)),
        "score_shape": list(scores.shape),
        "prediction_shape": list(predictions.shape),
    }


def regression(with_categorical: bool, max_models: int) -> dict:
    X, y = load_diabetes(return_X_y=True)
    X = X[:, :6]
    if with_categorical:
        df = pd.DataFrame(X, columns=[f"num_{i}" for i in range(X.shape[1])])
        df["bool_signal"] = df["num_0"] > df["num_0"].median()
        df["cat_low"] = np.where(df["num_1"] > df["num_1"].median(), "high", "low")
        X = df
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=7)
    reg = LazyRegressor(
        verbose=0,
        ignore_warnings=True,
        predictions=True,
        regressors=[Ridge],
        max_models=max_models,
        categorical_encoder="onehot",
    )
    scores, predictions = reg.fit(X_train, X_test, y_train, y_test)
    assert not scores.empty, "regression scores are empty"
    assert "R-Squared" in scores.columns, "missing R-Squared column"
    assert not predictions.empty, "predictions=True should return predictions"
    return {
        "task": "regression",
        "models": list(map(str, scores.index)),
        "score_shape": list(scores.shape),
        "prediction_shape": list(predictions.shape),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bounded Lazy Predict supervised smoke test.")
    parser.add_argument("--task", choices=["classification", "regression", "both"], default="both")
    parser.add_argument("--max-models", type=int, default=1, help="Positive guardrail passed to Lazy Predict.")
    parser.add_argument("--with-categorical", action="store_true", help="Add boolean and low-cardinality categorical columns.")
    args = parser.parse_args(argv)

    if args.max_models < 1:
        parser.error("--max-models must be positive")

    results = []
    if args.task in {"classification", "both"}:
        results.append(classification(args.with_categorical, args.max_models))
    if args.task in {"regression", "both"}:
        results.append(regression(args.with_categorical, args.max_models))
    print(json.dumps({"ok": True, "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - smoke failure path
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, indent=2), file=sys.stderr)
        raise
