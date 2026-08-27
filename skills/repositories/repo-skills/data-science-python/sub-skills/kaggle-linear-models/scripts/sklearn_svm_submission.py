#!/usr/bin/env python3
"""Train an SVC on dense CSV matrices and write class predictions."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from sklearn.svm import SVC


def load_matrix(path: Path) -> np.ndarray:
    """Load a headerless dense numeric CSV as a 2D matrix."""
    matrix = np.loadtxt(path, delimiter=",", ndmin=2)
    if matrix.ndim != 2:
        raise ValueError(f"{path} did not load as a 2D numeric matrix")
    return matrix.astype(float, copy=False)


def load_labels(path: Path) -> np.ndarray:
    """Load one integer-coded label per row."""
    labels = np.loadtxt(path, delimiter=",", ndmin=1)
    labels = np.asarray(labels).ravel()
    if labels.size == 0:
        raise ValueError(f"{path} contains no labels")
    return labels.astype(int, copy=False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train sklearn.svm.SVC on dense CSV matrices and write one prediction per test row.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--train", required=True, type=Path, help="Headerless dense numeric training CSV.")
    parser.add_argument("--labels", required=True, type=Path, help="CSV with one integer label per training row.")
    parser.add_argument("--test", required=True, type=Path, help="Headerless dense numeric test CSV.")
    parser.add_argument("--output", required=True, type=Path, help="Output CSV with one class prediction per line.")
    parser.add_argument("--kernel", default="rbf", help="SVC kernel name, e.g. rbf, linear, poly, sigmoid.")
    parser.add_argument("--C", type=float, default=1.0, help="SVC regularization strength.")
    parser.add_argument("--gamma", default="scale", help="SVC gamma value or one of scale/auto.")
    parser.add_argument("--degree", type=int, default=3, help="Polynomial degree when --kernel poly.")
    parser.add_argument("--coef0", type=float, default=0.0, help="Independent term for poly/sigmoid kernels.")
    parser.add_argument("--cache-size", type=float, default=200.0, help="SVC kernel cache size in MB.")
    parser.add_argument("--max-iter", type=int, default=-1, help="Solver iteration cap; -1 means no cap.")
    parser.add_argument("--random-state", type=int, default=None, help="Random seed passed through to SVC.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    train = load_matrix(args.train)
    labels = load_labels(args.labels)
    test = load_matrix(args.test)

    if train.shape[0] != labels.shape[0]:
        raise ValueError(
            f"Training row count ({train.shape[0]}) does not match label count ({labels.shape[0]})"
        )
    if train.shape[1] != test.shape[1]:
        raise ValueError(
            f"Train feature count ({train.shape[1]}) does not match test feature count ({test.shape[1]})"
        )

    model = SVC(
        C=args.C,
        kernel=args.kernel,
        degree=args.degree,
        gamma=args.gamma,
        coef0=args.coef0,
        cache_size=args.cache_size,
        max_iter=args.max_iter,
        random_state=args.random_state,
    )
    model.fit(train, labels)
    predictions = model.predict(test).astype(int, copy=False)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(args.output, predictions, fmt="%d", delimiter=",")
    print(f"Wrote {len(predictions)} predictions to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
