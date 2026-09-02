#!/usr/bin/env python3
"""Build deterministic 1D Poisson PINN proxy problems."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def exact_solution(x: float, frequency: float = 1.0) -> float:
    return math.sin(frequency * math.pi * x)


def poisson_second_derivative(x: float, frequency: float = 1.0) -> float:
    scale = frequency * math.pi
    return -(scale * scale) * math.sin(scale * x)


def build_problem(frequency: float = 1.0, residual_points: list[float] | None = None) -> dict:
    if frequency <= 0:
        raise ValueError("frequency must be positive")
    residual_points = residual_points or [0.25, 0.5, 0.75]
    if not residual_points:
        raise ValueError("residual_points must be non-empty")
    boundary_points = [0.0, 1.0]
    problem = {
        "schema_version": 1,
        "problem_id": "synthetic_1d_poisson_proxy",
        "is_proxy": True,
        "domain": [0.0, 1.0],
        "operator": "poisson_second_derivative",
        "exact_solution": "sin(frequency*pi*x)",
        "frequency": frequency,
        "boundary_points": boundary_points,
        "boundary_targets": [exact_solution(x, frequency) for x in boundary_points],
        "residual_points": residual_points,
        "residual_targets": [poisson_second_derivative(x, frequency) for x in residual_points],
    }
    validate_problem(problem)
    return problem


def validate_problem(problem: dict) -> None:
    for key in ["boundary_points", "boundary_targets", "residual_points", "residual_targets"]:
        values = problem.get(key)
        if not isinstance(values, list) or not values:
            raise ValueError(f"{key} must be a non-empty list")
        if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in values):
            raise ValueError(f"{key} must contain finite numeric values")
    if len(problem["boundary_points"]) != len(problem["boundary_targets"]):
        raise ValueError("boundary points and targets must align")
    if len(problem["residual_points"]) != len(problem["residual_targets"]):
        raise ValueError("residual points and targets must align")
    if problem.get("operator") != "poisson_second_derivative":
        raise ValueError("unsupported operator")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frequency", type=float, default=1.0)
    parser.add_argument("--residual-points", default="0.25,0.5,0.75")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    points = [float(item) for item in args.residual_points.split(",") if item.strip()]
    problem = build_problem(args.frequency, points)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(problem, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "problem_id": problem["problem_id"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
