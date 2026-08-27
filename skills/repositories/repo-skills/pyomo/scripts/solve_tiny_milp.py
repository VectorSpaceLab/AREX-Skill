#!/usr/bin/env python3
"""Solve a tiny binary MILP with a requested Pyomo solver.

This helper is safe, deterministic, and designed as a smoke test for solver
availability. It does not download data or mutate the repository.
"""

from __future__ import annotations

import argparse

import pyomo.environ as pyo


def build_model() -> pyo.ConcreteModel:
    m = pyo.ConcreteModel()
    m.x = pyo.Var(within=pyo.Binary)
    m.y = pyo.Var(within=pyo.Binary)
    m.limit = pyo.Constraint(expr=m.x + m.y <= 1)
    m.obj = pyo.Objective(expr=3 * m.x + 2 * m.y, sense=pyo.maximize)
    return m


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solver", default="glpk", help="Pyomo solver name.")
    args = parser.parse_args()

    solver = pyo.SolverFactory(args.solver)
    if not solver.available(False):
        print(f"solver-unavailable: {args.solver}")
        return 2

    m = build_model()
    results = solver.solve(m)
    term = str(results.solver.termination_condition).lower()
    obj = pyo.value(m.obj)
    x = pyo.value(m.x)
    y = pyo.value(m.y)

    print(f"solver={args.solver}")
    print(f"termination={term}")
    print(f"objective={obj}")
    print(f"x={x}")
    print(f"y={y}")

    if term != "optimal":
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
