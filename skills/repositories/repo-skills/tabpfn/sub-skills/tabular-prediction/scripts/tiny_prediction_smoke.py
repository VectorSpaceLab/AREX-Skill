#!/usr/bin/env python3
"""Run a tiny TabPFN prediction smoke check with a user-supplied local checkpoint.

The script never downloads weights by default: --model-path must point to an
existing local checkpoint file for the selected task.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from tabpfn import TabPFNClassifier, TabPFNRegressor


def require_local_model(path_text: str) -> str:
    path = Path(path_text).expanduser()
    if not path.exists():
        raise SystemExit(
            f"Local model path does not exist: {path}. Provide a cached checkpoint "
            "or use the model-management skill to prepare one."
        )
    return str(path)


def make_data(task: str, seed: int = 0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(32, 4)).astype("float32")
    if task == "classification":
        y = (X[:, 0] + 0.5 * X[:, 1] > 0).astype("int64")
    else:
        y = (2.0 * X[:, 0] - X[:, 1] + 0.1 * rng.normal(size=len(X))).astype("float32")
    return X[:24], X[24:], y[:24], y[24:]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=["classification", "regression"], required=True)
    parser.add_argument("--model-path", required=True, help="Existing local checkpoint path.")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--n-estimators", type=int, default=1)
    parser.add_argument(
        "--fit-mode",
        choices=["low_memory", "fit_preprocessors", "fit_with_cache"],
        default="fit_preprocessors",
    )
    args = parser.parse_args()

    model_path = require_local_model(args.model_path)
    X_train, X_test, y_train, _ = make_data(args.task)

    if args.task == "classification":
        est = TabPFNClassifier(
            model_path=model_path,
            device=args.device,
            n_estimators=args.n_estimators,
            fit_mode=args.fit_mode,
            random_state=0,
        )
        est.fit(X_train, y_train)
        proba = est.predict_proba(X_test)
        labels = est.predict(X_test)
        print(f"ok classification proba_shape={proba.shape} label_shape={labels.shape}")
    else:
        est = TabPFNRegressor(
            model_path=model_path,
            device=args.device,
            n_estimators=args.n_estimators,
            fit_mode=args.fit_mode,
            random_state=0,
        )
        est.fit(X_train, y_train)
        mean = est.predict(X_test)
        q = est.predict(X_test, output_type="quantiles", quantiles=[0.1, 0.5, 0.9])
        print(f"ok regression mean_shape={mean.shape} quantiles={len(q)}")


if __name__ == "__main__":
    main()
