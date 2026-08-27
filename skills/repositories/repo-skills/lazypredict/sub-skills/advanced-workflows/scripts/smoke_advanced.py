#!/usr/bin/env python3
"""Run safe Lazy Predict advanced-workflow checks.

Examples:
    python scripts/smoke_advanced.py --json
    python scripts/smoke_advanced.py --permutation --json

By default this script does not run expensive tuning. It checks constructor
validation, search-space registry availability, optional package presence, and
optionally a tiny permutation-importance workflow.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys

import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from lazypredict.Supervised import LazyClassifier
from lazypredict.TimeSeriesForecasting import LazyForecaster
from lazypredict.search_spaces import get_search_space
from lazypredict.ts_search_spaces import get_ts_search_space

OPTIONAL = ["optuna", "flaml", "shap", "interpret", "matplotlib"]


def available(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except Exception:
        return False


def permutation_smoke() -> dict:
    data = load_breast_cancer()
    X = pd.DataFrame(data.data[:, :5], columns=[f"f{i}" for i in range(5)])
    y = data.target
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    clf = LazyClassifier(verbose=0, ignore_warnings=True, classifiers=[LogisticRegression], max_models=1)
    scores, _ = clf.fit(X_train, X_test, y_train, y_test)
    assert not scores.empty, "base classifier fit failed"
    importance = clf.explain(X_test, y_test, method="permutation", n_repeats=2, max_samples=50)
    assert importance.shape[0] == X_test.shape[1], "importance row count mismatch"
    return {"importance_shape": list(importance.shape), "models": list(map(str, scores.index))}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safe advanced Lazy Predict smoke checks.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    parser.add_argument("--permutation", action="store_true", help="Run a tiny permutation-importance check.")
    args = parser.parse_args(argv)

    report = {
        "optional": {name: available(name) for name in OPTIONAL},
        "constructors": {},
        "search_spaces": {
            "RandomForestClassifier": get_search_space("RandomForestClassifier") is not None,
            "DummyClassifier": get_search_space("DummyClassifier") is not None,
            "SARIMAX": get_ts_search_space("SARIMAX") is not None,
            "Naive": get_ts_search_space("Naive") is not None,
        },
        "permutation": None,
    }

    clf = LazyClassifier(tune=True, tune_top_k=1, tune_trials=2, tune_backend="sklearn")
    fcst = LazyForecaster(tune=True, tune_top_k=1, tune_trials=2, tune_metric="MAE")
    report["constructors"] = {
        "LazyClassifier.tune_backend": clf.tune_backend,
        "LazyForecaster.tune_metric": fcst.tune_metric,
    }

    if args.permutation:
        report["permutation"] = permutation_smoke()

    report["ok"] = True
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Advanced checks passed")
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - smoke failure path
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, indent=2), file=sys.stderr)
        raise
