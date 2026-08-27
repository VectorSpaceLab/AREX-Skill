#!/usr/bin/env python3
"""Tiny, headless scikit-opt run-mode smoke checks.

This script intentionally covers only common, vectorization, cached, and
multithreading modes. Multiprocessing is skipped by default because process
pools require picklable top-level objectives, import-safe __main__ guards, and
platform-specific startup behavior that is not suitable for a generic smoke.
"""

from __future__ import annotations

import argparse
import math
import sys
from typing import Callable, Iterable

import numpy as np


def scalar_sphere(x: Iterable[float]) -> float:
    """Scalar objective: one candidate vector in, one finite scalar out."""
    arr = np.asarray(tuple(x), dtype=float)
    return float(np.sum(arr * arr))


def cached_integer_sphere(x: Iterable[float]) -> float:
    """Cache-friendly scalar objective; cached mode passes a tuple row."""
    row = tuple(float(v) for v in x)
    return float((row[0] - 1.0) ** 2 + (row[1] - 1.0) ** 2)


def vectorized_sphere(X: np.ndarray) -> np.ndarray:
    """Vectorized objective: population matrix in, one value per row out."""
    matrix = np.asarray(X, dtype=float)
    if matrix.ndim != 2 or matrix.shape[1] != 2:
        raise ValueError(f"expected X with shape (population, 2), got {matrix.shape}")
    return np.sum(matrix * matrix, axis=1)


def finite_scalar(value: object, mode: str) -> float:
    arr = np.asarray(value, dtype=float)
    if arr.size == 0:
        raise AssertionError(f"{mode}: optimizer returned an empty objective value")
    if not np.all(np.isfinite(arr)):
        raise AssertionError(f"{mode}: optimizer returned non-finite objective value {arr!r}")
    scalar = float(arr.reshape(-1)[0])
    if not math.isfinite(scalar):
        raise AssertionError(f"{mode}: scalar objective value is not finite: {scalar!r}")
    return scalar


def run_mode(mode: str) -> tuple[np.ndarray, float]:
    try:
        from sko.GA import GA
        from sko.tools import set_run_mode
    except Exception as exc:  # pragma: no cover - depends on caller environment
        raise RuntimeError("Could not import scikit-opt package modules. Install scikit-opt/sko first.") from exc

    np.random.seed(202405 + sum(ord(ch) for ch in mode))

    n_processes = 0
    if mode == "vectorization":
        func: Callable[..., object] = vectorized_sphere
        set_run_mode(func, "vectorization")
        lb = [-1, -1]
        ub = [1, 1]
        precision = 1e-2
    elif mode == "cached":
        func = cached_integer_sphere
        set_run_mode(func, "cached")
        lb = [0, 0]
        ub = [2, 2]
        precision = 1
    elif mode == "multithreading":
        func = scalar_sphere
        set_run_mode(func, "multithreading")
        n_processes = 2
        lb = [-1, -1]
        ub = [1, 1]
        precision = 1e-2
    elif mode == "common":
        func = scalar_sphere
        set_run_mode(func, "common")
        lb = [-1, -1]
        ub = [1, 1]
        precision = 1e-2
    else:  # argparse should prevent this path.
        raise ValueError(f"unsupported mode: {mode}")

    ga = GA(
        func=func,
        n_dim=2,
        size_pop=6,
        max_iter=3,
        lb=lb,
        ub=ub,
        precision=precision,
        n_processes=n_processes,
    )
    best_x, best_y = ga.run()
    best_scalar = finite_scalar(best_y, mode)
    if np.asarray(best_x).shape != (2,):
        raise AssertionError(f"{mode}: expected best_x shape (2,), got {np.asarray(best_x).shape}")
    return np.asarray(best_x, dtype=float), best_scalar


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run tiny, deterministic scikit-opt GA smoke checks for safe objective run modes.",
        epilog=(
            "Multiprocessing is intentionally not a smoke mode: validate it only in an "
            "import-safe Python module with picklable top-level objectives and an "
            "if __name__ == '__main__' guard. Joblib is optional and is documented "
            "but not required for this smoke."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=("common", "vectorization", "cached", "multithreading", "all"),
        default="all",
        help="Run one safe mode or all safe modes. Default: all.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    modes = ["common", "vectorization", "cached", "multithreading"] if args.mode == "all" else [args.mode]
    for mode in modes:
        best_x, best_y = run_mode(mode)
        best_x_text = np.array2string(best_x, precision=4, separator=", ")
        print(f"{mode}: ok best_y={best_y:.6g} best_x={best_x_text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
