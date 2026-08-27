#!/usr/bin/env python3
"""Deterministic smoke checks for ML-From-Scratch supervised regressors."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Tuple

os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np


def _import_regression_tools():
    try:
        from mlfromscratch.supervised_learning import LinearRegression, PolynomialRegression
        from mlfromscratch.utils import mean_squared_error
    except Exception as exc:  # pragma: no cover - diagnostic path depends on environment
        print("Failed to import ML-From-Scratch regression tools.", file=sys.stderr)
        print(f"Import error: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(
            "Check that mlfromscratch and its supervised dependencies are installed. "
            "A missing cvxopt package can break supervised imports because SVM is "
            "exported at package import time.",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    return LinearRegression, PolynomialRegression, mean_squared_error


def _linear_case() -> Tuple[np.ndarray, np.ndarray]:
    x = np.linspace(-3.0, 3.0, 24)
    X = x.reshape(-1, 1)
    y = -1.5 + 2.0 * x
    return X, y


def _polynomial_case() -> Tuple[np.ndarray, np.ndarray]:
    x = np.linspace(-1.0, 1.0, 30)
    X = x.reshape(-1, 1)
    y = 1.0 + 0.5 * x - 2.0 * x**2
    return X, y


def run(model_name: str, seed: int, tolerance: float) -> int:
    LinearRegression, PolynomialRegression, mean_squared_error = _import_regression_tools()
    np.random.seed(seed)

    if model_name == "linear-gd":
        X, y = _linear_case()
        model = LinearRegression(n_iterations=800, learning_rate=0.001, gradient_descent=True)
    elif model_name == "polynomial":
        X, y = _polynomial_case()
        model = PolynomialRegression(degree=2, n_iterations=4000, learning_rate=0.001)
    else:  # argparse prevents this
        raise ValueError(model_name)

    model.fit(X, y)
    y_pred = np.asarray(model.predict(X), dtype=float).reshape(-1)
    mse = float(mean_squared_error(y, y_pred))

    print(f"model={model_name}")
    print(f"n_samples={X.shape[0]} n_features={X.shape[1]}")
    print(f"mse={mse:.12g}")
    print("first_predictions=" + np.array2string(y_pred[:5], precision=6, separator=", "))

    if not np.isfinite(mse) or mse > tolerance:
        print(f"FAIL: mse {mse:.6g} exceeded tolerance {tolerance:.6g}", file=sys.stderr)
        return 1
    print("PASS: regression smoke completed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a quick, plot-free ML-From-Scratch supervised regression smoke test."
    )
    parser.add_argument(
        "--model",
        choices=("linear-gd", "polynomial"),
        default="linear-gd",
        help="Regression model to smoke-test. Default: linear-gd.",
    )
    parser.add_argument("--seed", type=int, default=11, help="NumPy random seed used before model construction.")
    parser.add_argument(
        "--tolerance",
        type=float,
        default=1e-4,
        help="Maximum allowed mean squared error on the deterministic in-memory case.",
    )
    args = parser.parse_args(argv)
    return run(args.model, args.seed, args.tolerance)


if __name__ == "__main__":
    raise SystemExit(main())
