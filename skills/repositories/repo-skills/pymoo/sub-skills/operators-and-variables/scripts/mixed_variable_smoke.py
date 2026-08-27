#!/usr/bin/env python3
"""Tiny pymoo mixed-variable smoke test.

Solves a small Real/Integer/Binary/Choice problem with MixedVariableGA and
asserts that the returned candidate uses valid Python types/options.
"""

from __future__ import annotations

import argparse
import numbers

import numpy as np

from pymoo.core.mixed import MixedVariableGA
from pymoo.core.problem import ElementwiseProblem
from pymoo.core.variable import Binary, Choice, Integer, Real
from pymoo.optimize import minimize


class MixedToyProblem(ElementwiseProblem):
    def __init__(self) -> None:
        variables = {
            "x": Real(bounds=(0.0, 1.0)),
            "n": Integer(bounds=(0, 5)),
            "flag": Binary(),
            "mode": Choice(options=["cheap", "accurate"]),
        }
        super().__init__(vars=variables, n_obj=1)

    def _evaluate(self, x, out, *args, **kwargs) -> None:
        mode_penalty = 0.0 if x["mode"] == "accurate" else 0.2
        flag_penalty = 0.0 if x["flag"] else 0.1
        out["F"] = (x["x"] - 0.25) ** 2 + abs(x["n"] - 2) + mode_penalty + flag_penalty


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny pymoo MixedVariableGA smoke test.")
    parser.add_argument("--pop-size", type=int, default=12, help="Small population size.")
    parser.add_argument("--n-gen", type=int, default=4, help="Small generation count.")
    parser.add_argument("--seed", type=int, default=1, help="Random seed.")
    args = parser.parse_args()

    if args.pop_size < 4:
        raise SystemExit("--pop-size must be at least 4")
    if args.n_gen < 1:
        raise SystemExit("--n-gen must be positive")

    problem = MixedToyProblem()
    res = minimize(problem, MixedVariableGA(pop_size=args.pop_size), ("n_gen", args.n_gen), seed=args.seed, verbose=False)

    assert isinstance(res.X, dict), f"Expected dict X from mixed-variable problem, got {type(res.X)!r}"
    assert set(res.X) == {"x", "n", "flag", "mode"}, f"Unexpected keys: {res.X}"
    assert 0.0 <= float(res.X["x"]) <= 1.0, res.X
    assert isinstance(res.X["n"], numbers.Integral), f"n should be integer-like, got {type(res.X['n'])!r}: {res.X}"
    assert 0 <= int(res.X["n"]) <= 5, res.X
    assert isinstance(res.X["flag"], (bool, np.bool_)), f"flag should be bool-like, got {type(res.X['flag'])!r}: {res.X}"
    assert res.X["mode"] in {"cheap", "accurate"}, res.X
    assert res.F is not None, "Result F is None"
    best_f = float(np.asarray(res.F, dtype=float).reshape(-1)[0])
    assert best_f >= 0.0, res.F

    normalized = {"x": float(res.X["x"]), "n": int(res.X["n"]), "flag": bool(res.X["flag"]), "mode": res.X["mode"]}
    print("pymoo mixed-variable smoke passed")
    print(f"best X: {normalized}")
    print(f"best F: {best_f:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
