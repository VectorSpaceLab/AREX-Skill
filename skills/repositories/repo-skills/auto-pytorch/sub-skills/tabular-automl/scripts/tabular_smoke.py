#!/usr/bin/env python3
"""Tiny tabular AutoML smoke check for Auto-PyTorch.

This script validates the tabular data path without running a full search.
It is safe to run on a small synthetic fixture.
"""

from __future__ import annotations

import argparse
import inspect
import json
from typing import Any, Dict

import numpy as np
import pandas as pd
from sklearn.datasets import make_classification, make_regression
from sklearn.model_selection import train_test_split

from autoPyTorch.data.tabular_validator import TabularInputValidator
from autoPyTorch.datasets.tabular_dataset import TabularDataset
from autoPyTorch.api.tabular_classification import TabularClassificationTask
from autoPyTorch.api.tabular_regression import TabularRegressionTask


def _make_frame(seed: int = 1) -> pd.DataFrame:
    rng = np.random.RandomState(seed)
    frame = pd.DataFrame(
        {
            "num_a": rng.normal(size=40),
            "num_b": rng.uniform(-1, 1, size=40),
            "cat_a": pd.Series(np.where(rng.rand(40) > 0.5, "x", "y"), dtype="category"),
        }
    )
    return frame


def _tabular_report(task: str) -> Dict[str, Any]:
    if task == "classification":
        X, y = make_classification(
            n_samples=40,
            n_features=4,
            n_informative=3,
            n_redundant=1,
            random_state=1,
        )
        X = _make_frame(seed=1).assign(num_d=np.asarray(X[:, 0]))
        y = pd.Series(y)
        validator = TabularInputValidator(is_classification=True).fit(X, y)
    else:
        X, y = make_regression(
            n_samples=40,
            n_features=4,
            n_informative=3,
            random_state=1,
        )
        X = _make_frame(seed=2).assign(num_d=np.asarray(X[:, 0]))
        y = pd.Series(y)
        validator = TabularInputValidator(is_classification=False).fit(X, y)

    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=1)
    dataset = TabularDataset(
        X=X_train,
        Y=y_train,
        X_test=X_test,
        Y_test=y_test,
        validator=validator,
    )

    if task == "classification":
        task_signature = str(inspect.signature(TabularClassificationTask.search))
    else:
        task_signature = str(inspect.signature(TabularRegressionTask.search))

    return {
        "task": task,
        "dataset_shape": list(X.shape),
        "train_shape": list(dataset.train_tensors[0].shape),
        "target_shape": list(dataset.train_tensors[1].shape),
        "validator_columns": list(getattr(validator.feature_validator, "column_order", [])),
        "dataset_info_keys": sorted(dataset.get_required_dataset_info().keys()),
        "task_signature": task_signature,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("classification", "regression", "both"),
        default="both",
        help="Which synthetic tabular path to check.",
    )
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    args = parser.parse_args()

    payload: Dict[str, Any] = {}
    if args.mode in {"classification", "both"}:
        payload["classification"] = _tabular_report("classification")
    if args.mode in {"regression", "both"}:
        payload["regression"] = _tabular_report("regression")

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for name, report in payload.items():
            print(f"[{name}] {report['dataset_shape']} -> {report['train_shape']} / {report['target_shape']}")
            print(f"  requirements: {report['requirements']}")
            print(f"  steps: {report['pipeline_steps']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
