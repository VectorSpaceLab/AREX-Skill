#!/usr/bin/env python3
"""Fixed-step ODE solvers for deterministic Flow Matching recovery checks."""

import argparse
import json
from typing import Callable, List, Sequence

Vector = List[float]
VectorField = Callable[[float, Sequence[float]], Vector]


def _vector(values) -> Vector:
    return [float(value) for value in values]


def add_scaled(x: Sequence[float], dx: Sequence[float], scale: float) -> Vector:
    if len(x) != len(dx):
        raise ValueError("state and derivative dimensions must match")
    return [float(a) + float(scale) * float(b) for a, b in zip(x, dx)]


def constant_field(velocity: Sequence[float]) -> VectorField:
    velocity = _vector(velocity)

    def field(t: float, x: Sequence[float]) -> Vector:
        if len(x) != len(velocity):
            raise ValueError("state and velocity dimensions must match")
        return list(velocity)

    return field


def integrate(field: VectorField, x0: Sequence[float], steps: int, solver: str = "euler") -> dict:
    if steps <= 0:
        raise ValueError("steps must be positive")
    if solver not in {"euler", "midpoint", "rk4"}:
        raise ValueError("solver must be euler, midpoint, or rk4")
    h = 1.0 / int(steps)
    x = _vector(x0)
    trajectory = [list(x)]
    nfe = 0
    for index in range(int(steps)):
        t = index * h
        if solver == "euler":
            k1 = field(t, x)
            nfe += 1
            x = add_scaled(x, k1, h)
        elif solver == "midpoint":
            k1 = field(t, x)
            mid = add_scaled(x, k1, 0.5 * h)
            k2 = field(t + 0.5 * h, mid)
            nfe += 2
            x = add_scaled(x, k2, h)
        else:
            k1 = field(t, x)
            k2 = field(t + 0.5 * h, add_scaled(x, k1, 0.5 * h))
            k3 = field(t + 0.5 * h, add_scaled(x, k2, 0.5 * h))
            k4 = field(t + h, add_scaled(x, k3, h))
            nfe += 4
            x = [float(a) + h * (float(b) + 2.0 * float(c) + 2.0 * float(d) + float(e)) / 6.0 for a, b, c, d, e in zip(x, k1, k2, k3, k4)]
        trajectory.append(list(x))
    return {"final": x, "trajectory": trajectory, "nfe": nfe, "solver": solver, "steps": int(steps)}


def mse(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise ValueError("vectors must have the same dimension")
    return sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)) / max(1, len(a))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--x0", required=True, help="JSON vector")
    parser.add_argument("--velocity", required=True, help="JSON constant velocity vector")
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument("--solver", choices=["euler", "midpoint", "rk4"], default="euler")
    args = parser.parse_args()
    x0 = _vector(json.loads(args.x0))
    velocity = _vector(json.loads(args.velocity))
    result = integrate(constant_field(velocity), x0, args.steps, args.solver)
    reference = add_scaled(x0, velocity, 1.0)
    result["reference"] = reference
    result["reference_mse"] = mse(result["final"], reference)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
