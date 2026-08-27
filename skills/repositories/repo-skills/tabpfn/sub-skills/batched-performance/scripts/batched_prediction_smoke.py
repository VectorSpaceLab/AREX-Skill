#!/usr/bin/env python3
"""Run a tiny batched prediction smoke check with a local checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from tabpfn import TabPFNClassifier, TabPFNRegressor


def require_local_model(path_text: str) -> str:
    path = Path(path_text).expanduser()
    if not path.exists():
        raise SystemExit(f"Local model path does not exist: {path}")
    return str(path)


def make_classifier_data(seed: int, n: int = 24, f: int = 4):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, f)).astype("float32")
    y = (X[:, 0] + 0.25 * X[:, 1] > 0).astype("int64")
    return X, y


def make_regressor_data(seed: int, n: int = 24, f: int = 4):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, f)).astype("float32")
    y = (2.0 * X[:, 0] - X[:, 1] + 0.1 * rng.normal(size=n)).astype("float32")
    return X, y


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=["classification", "regression"], required=True)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--n-estimators", type=int, default=1)
    args = parser.parse_args()

    model_path = require_local_model(args.model_path)

    if args.task == "classification":
        data = [make_classifier_data(seed) for seed in range(3)]
        X_train_list = [d[0][:16] for d in data]
        y_train_list = [d[1][:16] for d in data]
        X_test_list = [d[0][16:] for d in data]
        est = TabPFNClassifier(
            model_path=model_path,
            device=args.device,
            n_estimators=args.n_estimators,
            random_state=0,
        )
        batched = est.predict_proba_batched(X_train_list, y_train_list, X_test_list)
        refs = []
        for X, y, X_test in zip(X_train_list, y_train_list, X_test_list, strict=True):
            ref = TabPFNClassifier(
                model_path=model_path,
                device=args.device,
                n_estimators=args.n_estimators,
                random_state=0,
            )
            ref.fit(X, y)
            refs.append(ref.predict_proba(X_test))
        max_diff = max(float(np.max(np.abs(a - b))) for a, b in zip(batched, refs, strict=True))
        print(f"ok classification batched_shape={batched.shape} max_diff={max_diff:.3e}")
    else:
        data = [make_regressor_data(seed) for seed in range(3)]
        X_train_list = [d[0][:16] for d in data]
        y_train_list = [d[1][:16] for d in data]
        X_test_list = [d[0][16:] for d in data]
        est = TabPFNRegressor(
            model_path=model_path,
            device=args.device,
            n_estimators=args.n_estimators,
            random_state=0,
        )
        batched = est.predict_batched(X_train_list, y_train_list, X_test_list)
        refs = []
        for X, y, X_test in zip(X_train_list, y_train_list, X_test_list, strict=True):
            ref = TabPFNRegressor(
                model_path=model_path,
                device=args.device,
                n_estimators=args.n_estimators,
                random_state=0,
            )
            ref.fit(X, y)
            refs.append(ref.predict(X_test))
        max_diff = max(float(np.max(np.abs(np.asarray(a) - np.asarray(b)))) for a, b in zip(batched, refs, strict=True))
        print(f"ok regression datasets={len(batched)} max_diff={max_diff:.3e}")


if __name__ == "__main__":
    main()
