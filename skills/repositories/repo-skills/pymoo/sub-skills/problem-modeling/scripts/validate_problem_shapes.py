#!/usr/bin/env python3
"""Validate key pymoo custom-problem output shape conventions.

This script defines tiny vectorized and elementwise constrained problems and
asserts that F/G/H shapes and finite values match pymoo expectations. Use it as a
safe smoke when adapting a custom problem.
"""

from __future__ import annotations

import argparse
import numpy as np

from pymoo.core.problem import ElementwiseProblem, Problem


class VectorizedConstrainedProblem(Problem):
    def __init__(self) -> None:
        super().__init__(n_var=2, n_obj=2, n_ieq_constr=2, n_eq_constr=1, xl=-2.0, xu=2.0)

    def _evaluate(self, X, out, *args, **kwargs) -> None:
        f1 = 100.0 * (X[:, 0] ** 2 + X[:, 1] ** 2)
        f2 = (X[:, 0] - 1.0) ** 2 + X[:, 1] ** 2
        g1 = 2.0 * (X[:, 0] - 0.1) * (X[:, 0] - 0.9) / 0.18
        g2 = -20.0 * (X[:, 0] - 0.4) * (X[:, 0] - 0.6) / 4.8
        h1 = X[:, 0] + X[:, 1] - 0.5
        out["F"] = np.column_stack([f1, f2])
        out["G"] = np.column_stack([g1, g2])
        out["H"] = h1[:, None]


class ElementwiseConstrainedProblem(ElementwiseProblem):
    def __init__(self) -> None:
        super().__init__(n_var=2, n_obj=1, n_ieq_constr=1, xl=-2.0, xu=2.0)

    def _evaluate(self, x, out, *args, **kwargs) -> None:
        out["F"] = float(np.sum((x - 0.25) ** 2))
        out["G"] = [float(np.sum(x) - 1.0)]


def assert_finite(name: str, value: np.ndarray) -> None:
    assert np.all(np.isfinite(value)), f"{name} contains non-finite values: {value}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate pymoo custom-problem F/G/H shapes.")
    parser.add_argument("--seed", type=int, default=1, help="Random seed for sample points.")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    X = rng.uniform(-1.0, 1.0, size=(5, 2))

    vector_problem = VectorizedConstrainedProblem()
    F, G, H = vector_problem.evaluate(X, return_values_of=["F", "G", "H"])
    assert F.shape == (5, 2), f"Expected vectorized F shape (5, 2), got {F.shape}"
    assert G.shape == (5, 2), f"Expected vectorized G shape (5, 2), got {G.shape}"
    assert H.shape == (5, 1), f"Expected vectorized H shape (5, 1), got {H.shape}"
    assert_finite("F", F)
    assert_finite("G", G)
    assert_finite("H", H)

    elementwise_problem = ElementwiseConstrainedProblem()
    F2, G2 = elementwise_problem.evaluate(X, return_values_of=["F", "G"])
    assert F2.shape == (5, 1), f"Expected elementwise F shape (5, 1), got {F2.shape}"
    assert G2.shape == (5, 1), f"Expected elementwise G shape (5, 1), got {G2.shape}"
    assert_finite("F2", F2)
    assert_finite("G2", G2)

    feasible_mask = G2[:, 0] <= 0.0
    print("pymoo problem shape validation passed")
    print(f"vectorized F/G/H shapes: {F.shape}, {G.shape}, {H.shape}")
    print(f"elementwise F/G shapes: {F2.shape}, {G2.shape}")
    print(f"elementwise feasible rows under G <= 0: {int(feasible_mask.sum())}/{len(feasible_mask)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
