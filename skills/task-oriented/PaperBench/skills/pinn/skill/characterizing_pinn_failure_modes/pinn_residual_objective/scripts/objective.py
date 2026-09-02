#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from typing import Any


def surrogate_value(x: float, t: float, amplitude: float, speed: float, phase: float = 0.0) -> float:
    return amplitude * math.sin((x - speed * t + phase) % (2.0 * math.pi))


def convection_residual(x: float, t: float, beta: float, amplitude: float, speed: float, phase: float = 0.0) -> float:
    angle = (x - speed * t + phase) % (2.0 * math.pi)
    u_t = -amplitude * speed * math.cos(angle)
    u_x = amplitude * math.cos(angle)
    return u_t + beta * u_x


def loss_decomposition(benchmark: dict[str, Any], amplitude: float, speed: float, beta: float | None = None, residual_weight: float = 1.0, phase: float = 0.0) -> dict[str, float]:
    coeff_beta = float(beta if beta is not None else benchmark["coefficients"]["beta"])
    initial = benchmark["initial_condition"]
    boundary_pairs = benchmark["boundary_pairs"]
    collocation = benchmark["collocation"]
    initial_loss = sum((surrogate_value(x, t, amplitude, speed, phase) - target) ** 2 for x, t, target in initial) / len(initial)
    boundary_loss = sum((surrogate_value(left[0], left[1], amplitude, speed, phase) - surrogate_value(right[0], right[1], amplitude, speed, phase)) ** 2 for left, right in boundary_pairs) / len(boundary_pairs)
    residual_loss = sum(convection_residual(x, t, coeff_beta, amplitude, speed, phase) ** 2 for x, t in collocation) / len(collocation)
    total = initial_loss + boundary_loss + residual_weight * residual_loss
    return {"initial_loss": initial_loss, "boundary_loss": boundary_loss, "residual_loss": residual_loss, "total_loss": total, "beta": coeff_beta, "amplitude": amplitude, "speed": speed, "phase": phase}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmark_json")
    parser.add_argument("--amplitude", type=float, default=1.0)
    parser.add_argument("--speed", type=float, default=30.0)
    parser.add_argument("--beta", type=float, default=None)
    parser.add_argument("--residual-weight", type=float, default=1.0)
    args = parser.parse_args()
    with open(args.benchmark_json, "r", encoding="utf-8") as handle:
        benchmark = json.load(handle)
    print(json.dumps(loss_decomposition(benchmark, args.amplitude, args.speed, args.beta, args.residual_weight), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
