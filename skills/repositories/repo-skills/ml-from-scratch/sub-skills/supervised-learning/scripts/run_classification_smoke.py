#!/usr/bin/env python3
"""Deterministic smoke checks for ML-From-Scratch supervised classifiers."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Callable, Dict, Iterable, Tuple

os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np


ArrayPair = Tuple[np.ndarray, np.ndarray]


def _import_classification_tools():
    try:
        from mlfromscratch.supervised_learning import (
            Adaboost,
            KNN,
            LDA,
            LogisticRegression,
            NaiveBayes,
            SupportVectorMachine,
        )
        from mlfromscratch.utils import accuracy_score, normalize
        from mlfromscratch.utils.kernels import linear_kernel
    except Exception as exc:  # pragma: no cover - diagnostic path depends on environment
        print("Failed to import ML-From-Scratch classification tools.", file=sys.stderr)
        print(f"Import error: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(
            "Check that mlfromscratch and supervised dependencies are installed. "
            "The SVM export requires cvxopt, so missing cvxopt can break package-level "
            "supervised imports even when another classifier was requested.",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    return {
        "Adaboost": Adaboost,
        "KNN": KNN,
        "LDA": LDA,
        "LogisticRegression": LogisticRegression,
        "NaiveBayes": NaiveBayes,
        "SupportVectorMachine": SupportVectorMachine,
        "accuracy_score": accuracy_score,
        "normalize": normalize,
        "linear_kernel": linear_kernel,
    }


def _binary_data(normalize: Callable[[np.ndarray], np.ndarray]) -> ArrayPair:
    # Two compact, linearly separable clusters. Kept tiny so SVM/cvxopt is fast.
    X = np.array(
        [
            [-2.0, -1.0],
            [-1.5, -1.0],
            [-1.0, -2.0],
            [-2.0, -2.0],
            [1.0, 1.5],
            [1.5, 1.0],
            [2.0, 2.0],
            [1.0, 2.0],
        ],
        dtype=float,
    )
    y01 = np.array([0, 0, 0, 0, 1, 1, 1, 1], dtype=int)
    return normalize(X), y01


def _run_one(model_name: str, seed: int, tools: Dict[str, object]) -> Tuple[float, np.ndarray, np.ndarray]:
    np.random.seed(seed)
    X, y01 = _binary_data(tools["normalize"])
    ypm = np.where(y01 == 1, 1.0, -1.0)

    if model_name == "logistic":
        clf = tools["LogisticRegression"](learning_rate=0.1, gradient_descent=True)
        clf.fit(X, y01, n_iterations=600)
        truth = y01
        pred = np.asarray(clf.predict(X), dtype=int)
    elif model_name == "knn":
        clf = tools["KNN"](k=3)
        truth = y01
        pred = np.asarray(clf.predict(X, X, y01), dtype=int)
    elif model_name == "naive-bayes":
        clf = tools["NaiveBayes"]()
        clf.fit(X, y01)
        truth = y01
        pred = np.asarray(clf.predict(X), dtype=int)
    elif model_name == "lda":
        clf = tools["LDA"]()
        clf.fit(X, y01)
        truth = y01
        pred = np.asarray(clf.predict(X), dtype=int)
    elif model_name == "svm":
        clf = tools["SupportVectorMachine"](kernel=tools["linear_kernel"], C=1)
        clf.fit(X, ypm)
        truth = ypm
        pred = np.asarray(clf.predict(X), dtype=float)
    elif model_name == "adaboost":
        clf = tools["Adaboost"](n_clf=3)
        clf.fit(X, ypm)
        truth = ypm
        pred = np.asarray(clf.predict(X), dtype=float)
    else:  # argparse prevents this
        raise ValueError(model_name)

    accuracy = float(tools["accuracy_score"](truth, pred))
    return accuracy, truth, pred


def _selected_models(name: str) -> Iterable[str]:
    if name == "all-fast":
        return ("logistic", "knn", "naive-bayes", "lda", "svm", "adaboost")
    return (name,)


def run(model_name: str, seed: int, min_accuracy: float) -> int:
    tools = _import_classification_tools()
    failures = []
    for name in _selected_models(model_name):
        accuracy, truth, pred = _run_one(name, seed, tools)
        print(f"model={name}")
        print(f"accuracy={accuracy:.6f}")
        print("truth=" + np.array2string(truth, precision=3, separator=", "))
        print("pred =" + np.array2string(pred, precision=3, separator=", "))
        if not np.isfinite(accuracy) or accuracy < min_accuracy:
            failures.append((name, accuracy))

    if failures:
        for name, accuracy in failures:
            print(f"FAIL: {name} accuracy {accuracy:.6f} below {min_accuracy:.6f}", file=sys.stderr)
        return 1
    print("PASS: classification smoke completed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run quick, plot-free ML-From-Scratch supervised classification smoke tests."
    )
    parser.add_argument(
        "--model",
        choices=("all-fast", "logistic", "knn", "naive-bayes", "lda", "svm", "adaboost"),
        default="logistic",
        help="Classifier to smoke-test. all-fast runs every supported quick option. Default: logistic.",
    )
    parser.add_argument("--seed", type=int, default=7, help="NumPy random seed used before model construction.")
    parser.add_argument(
        "--min-accuracy",
        type=float,
        default=0.99,
        help="Minimum accuracy required on the deterministic in-memory case.",
    )
    args = parser.parse_args(argv)
    return run(args.model, args.seed, args.min_accuracy)


if __name__ == "__main__":
    raise SystemExit(main())
