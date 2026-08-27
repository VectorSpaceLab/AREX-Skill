#!/usr/bin/env python3
"""Save and reload a fitted TabPFN estimator using a local checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from sklearn.datasets import load_breast_cancer, load_diabetes
from sklearn.model_selection import train_test_split

from tabpfn import TabPFNClassifier, TabPFNRegressor


def require_local_model(path_text: str) -> str:
    path = Path(path_text).expanduser()
    if not path.exists():
        raise SystemExit(f"Local model path does not exist: {path}")
    return str(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=["classifier", "regressor"], required=True)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--save-path", default="roundtrip.tabpfn_fit")
    args = parser.parse_args()

    model_path = require_local_model(args.model_path)
    save_path = Path(args.save_path)
    if save_path.suffix != ".tabpfn_fit":
        raise SystemExit("save-path must end with .tabpfn_fit")

    if args.task == "classifier":
        X, y = load_breast_cancer(return_X_y=True)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=0, stratify=y
        )
        est = TabPFNClassifier(model_path=model_path, device=args.device, n_estimators=1, random_state=0)
        est.fit(X_train, y_train)
        before = est.predict_proba(X_test)
        est.save_fit_state(save_path)
        loaded = TabPFNClassifier.load_from_fit_state(save_path, device=args.device)
        after = loaded.predict_proba(X_test)
        max_diff = float(np.max(np.abs(before - after)))
        print(f"ok classifier save_path={save_path} max_diff={max_diff:.3e}")
    else:
        X, y = load_diabetes(return_X_y=True)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=0)
        est = TabPFNRegressor(model_path=model_path, device=args.device, n_estimators=1, random_state=0)
        est.fit(X_train, y_train)
        before = est.predict(X_test)
        est.save_fit_state(save_path)
        loaded = TabPFNRegressor.load_from_fit_state(save_path, device=args.device)
        after = loaded.predict(X_test)
        max_diff = float(np.max(np.abs(before - after)))
        print(f"ok regressor save_path={save_path} max_diff={max_diff:.3e}")


if __name__ == "__main__":
    main()
