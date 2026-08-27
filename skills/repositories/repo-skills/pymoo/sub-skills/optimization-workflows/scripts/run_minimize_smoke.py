#!/usr/bin/env python3
"""Tiny pymoo minimize smoke test.

Runs NSGA-II on ZDT1 for a very small generation budget. This verifies that the
base pymoo import, algorithm construction, termination tuple, and Result fields
work in the current Python environment.
"""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny pymoo NSGA-II/ZDT1 minimize smoke test.")
    parser.add_argument("--pop-size", type=int, default=20, help="Small NSGA-II population size.")
    parser.add_argument("--n-gen", type=int, default=3, help="Small generation budget.")
    parser.add_argument("--seed", type=int, default=1, help="Random seed for reproducibility.")
    args = parser.parse_args()

    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.optimize import minimize
    from pymoo.problems import get_problem

    if args.pop_size < 4:
        raise SystemExit("--pop-size should be at least 4 for this multi-objective smoke")
    if args.n_gen < 1:
        raise SystemExit("--n-gen must be positive")

    problem = get_problem("zdt1")
    algorithm = NSGA2(pop_size=args.pop_size, eliminate_duplicates=True)
    res = minimize(problem, algorithm, ("n_gen", args.n_gen), seed=args.seed, verbose=False)

    assert res.F is not None, "Result objective matrix is None"
    assert res.F.ndim == 2 and res.F.shape[1] == 2, f"Unexpected F shape: {res.F.shape}"
    assert res.X is not None and res.X.shape[0] == res.F.shape[0], "X/F rows are not aligned"
    assert res.algorithm.evaluator.n_eval > 0, "No function evaluations were counted"

    print("pymoo minimize smoke passed")
    print(f"F shape: {res.F.shape}")
    print(f"X shape: {res.X.shape}")
    print(f"evaluations: {res.algorithm.evaluator.n_eval}")
    print(f"generations: {res.algorithm.n_gen}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
