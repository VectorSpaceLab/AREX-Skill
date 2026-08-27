#!/usr/bin/env python3
"""Tiny, deterministic scikit-opt smoke checks for GA-family workflows.

Run from any working directory. This script uses the installed `sko` package
only and does not depend on the original repository checkout.
"""

from __future__ import annotations

import argparse
import math
import sys
from typing import Iterable

import numpy as np


def sphere(x: Iterable[float]) -> float:
    arr = np.asarray(tuple(x), dtype=float)
    return float(np.sum(arr * arr))


def mixed_precision_objective(x: Iterable[float]) -> float:
    arr = np.asarray(tuple(x), dtype=float)
    return float((arr[0] - 1.0) ** 2 + (arr[1] + 0.5) ** 2)


def finite_scalar(value: object, label: str) -> float:
    arr = np.asarray(value, dtype=float)
    if arr.size == 0:
        raise AssertionError(f"{label}: empty objective value")
    if not np.all(np.isfinite(arr)):
        raise AssertionError(f"{label}: non-finite objective value {arr!r}")
    scalar = float(arr.reshape(-1)[0])
    if not math.isfinite(scalar):
        raise AssertionError(f"{label}: scalar objective is not finite: {scalar!r}")
    return scalar


def run_ga() -> tuple[np.ndarray, float]:
    from sko.GA import GA

    np.random.seed(4101)
    ga = GA(func=mixed_precision_objective, n_dim=2, size_pop=8, max_iter=2, lb=[-2, -2], ub=[2, 2], precision=[1, 0.5])
    ga.run(2)
    best_x, best_y = ga.run(2)
    return np.asarray(best_x, dtype=float), finite_scalar(best_y, "GA")


def run_ega() -> tuple[np.ndarray, float]:
    from sko.GA import EGA

    np.random.seed(4102)
    ega = EGA(func=sphere, n_dim=2, size_pop=10, max_iter=3, lb=[-1, -1], ub=[1, 1], n_elitist=2)
    best_x, best_y = ega.run()
    return np.asarray(best_x, dtype=float), finite_scalar(best_y, "EGA")


def run_rcga() -> tuple[np.ndarray, float]:
    from sko.GA import RCGA

    np.random.seed(4103)
    rcga = RCGA(func=sphere, n_dim=2, size_pop=8, max_iter=3, lb=[-1, -1], ub=[1, 1])
    best_x, best_y = rcga.run()
    return np.asarray(best_x, dtype=float), finite_scalar(best_y, "RCGA")


def run_custom() -> tuple[np.ndarray, float]:
    from sko.GA import GA
    from sko.operators import crossover, mutation, ranking

    def selection_top_half(self):
        order = np.argsort(-self.FitV)
        elite = order[: self.size_pop // 2]
        self.Chrom = np.repeat(self.Chrom[elite], 2, axis=0)
        return self.Chrom

    np.random.seed(4104)
    ga = GA(func=sphere, n_dim=2, size_pop=8, max_iter=3, lb=[-1, -1], ub=[1, 1], precision=1e-2)
    ga.register("selection", selection_top_half)
    ga.register("ranking", ranking.ranking)
    ga.register("crossover", crossover.crossover_2point_bit)
    ga.register("mutation", mutation.mutation)
    best_x, best_y = ga.run()
    return np.asarray(best_x, dtype=float), finite_scalar(best_y, "custom")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run tiny, deterministic scikit-opt smoke checks for GA-family workflows.",
        epilog="GA_TSP is intentionally left to the routing sub-skill; this smoke focuses on GA, EGA, RCGA, and custom operators.",
    )
    parser.add_argument(
        "--mode",
        choices=("ga", "rcga", "custom", "all"),
        default="all",
        help="Run classic GA+EGA smoke, RCGA, custom operators, or all of them. Default: all.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    checks = {
        "ga": run_ga,
        "ega": run_ega,
        "rcga": run_rcga,
        "custom": run_custom,
    }
    if args.mode == "ga":
        run_order = ["ga", "ega"]
    elif args.mode == "all":
        run_order = ["ga", "ega", "rcga", "custom"]
    else:
        run_order = [args.mode]
    for name in run_order:
        best_x, best_y = checks[name]()
        best_x_text = np.array2string(best_x, precision=4, separator=", ")
        print(f"{name}: ok best_y={best_y:.6g} best_x={best_x_text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
