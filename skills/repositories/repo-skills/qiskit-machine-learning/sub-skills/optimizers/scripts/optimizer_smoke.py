#!/usr/bin/env python3
"""Run a bounded, low-cost optimizer smoke test.

The script imports Qiskit Machine Learning lazily so ``--help`` works even in
an environment where the package's Qiskit dependency is not installed. It does
not read repository files and may be launched from any current directory.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable

import numpy as np


Objective = Callable[[np.ndarray], float]


def quadratic(x: np.ndarray) -> float:
    """A bounded two-variable quadratic with an interior minimizer."""
    target = np.asarray([0.5, -0.75])
    return float(np.sum((x - target) ** 2))


def rosenbrock(x: np.ndarray) -> float:
    """The two-variable Rosenbrock objective."""
    return float(100.0 * (x[1] - x[0] ** 2) ** 2 + (1.0 - x[0]) ** 2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run bounded quadratic/Rosenbrock optimizer smoke tests."
    )
    parser.add_argument(
        "--objective",
        choices=("quadratic", "rosenbrock", "both"),
        default="both",
        help="objective(s) to run (default: both)",
    )
    parser.add_argument(
        "--optimizer",
        choices=("slsqp", "l_bfgs_b"),
        default="slsqp",
        help="bound-aware optimizer (default: slsqp)",
    )
    parser.add_argument(
        "--maxiter",
        type=int,
        default=40,
        help="small iteration budget for each objective (default: 40)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1376,
        help="Qiskit algorithm_globals seed (default: 1376)",
    )
    return parser


def _make_optimizer(name: str, maxiter: int):
    from qiskit_machine_learning.optimizers import L_BFGS_B, SLSQP

    if maxiter < 1:
        raise ValueError("--maxiter must be at least 1")
    if name == "slsqp":
        return SLSQP(maxiter=maxiter, ftol=1e-9)
    return L_BFGS_B(maxfun=maxiter * 10, maxiter=maxiter)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        from qiskit_machine_learning.utils import algorithm_globals
    except ImportError as exc:
        print(
            "optimizer smoke requires an installed qiskit-machine-learning "
            "environment with its Qiskit dependency: " + str(exc),
            file=sys.stderr,
        )
        return 2

    algorithm_globals.random_seed = args.seed
    objectives: dict[str, Objective] = {
        "quadratic": quadratic,
        "rosenbrock": rosenbrock,
    }
    selected = objectives.keys() if args.objective == "both" else (args.objective,)
    bounds = [(-2.0, 2.0), (-2.0, 2.0)]
    initial_point = np.asarray([-1.2, 1.0])
    records = []

    for name in selected:
        optimizer = _make_optimizer(args.optimizer, args.maxiter)
        objective = objectives[name]
        result = optimizer.minimize(objective, initial_point.copy(), bounds=bounds)
        point = np.asarray(result.x, dtype=float)
        if point.shape != (2,) or not np.all(np.isfinite(point)):
            raise RuntimeError(f"{name}: optimizer returned an invalid point {result.x!r}")
        if not np.all((point >= -2.0) & (point <= 2.0)):
            raise RuntimeError(f"{name}: returned point outside bounds: {point!r}")
        if result.fun is None or not np.isfinite(float(result.fun)):
            raise RuntimeError(f"{name}: optimizer returned invalid fun={result.fun!r}")
        records.append(
            {
                "objective": name,
                "optimizer": type(optimizer).__name__,
                "x": point.tolist(),
                "fun": float(result.fun),
                "nfev": result.nfev,
                "nit": result.nit,
            }
        )

    print(json.dumps(records, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
