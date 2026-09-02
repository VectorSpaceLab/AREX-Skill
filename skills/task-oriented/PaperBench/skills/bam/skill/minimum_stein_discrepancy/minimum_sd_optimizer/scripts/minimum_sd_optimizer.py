#!/usr/bin/env python3
"""Bounded optimiser for scalar minimum Stein discrepancy recovery."""

from __future__ import annotations

import argparse
import json
import math
from typing import Callable

LossFn = Callable[[float], float]


def linspace(lower: float, upper: float, count: int) -> list[float]:
    if count < 2:
        return [(lower + upper) / 2.0]
    step = (upper - lower) / float(count - 1)
    return [lower + i * step for i in range(count)]


def minimise_scalar_grid(
    loss_fn: LossFn,
    initial_theta: float,
    lower: float,
    upper: float,
    grid_size: int = 41,
    refinement_rounds: int = 1,
) -> dict[str, object]:
    if lower >= upper:
        raise ValueError("lower bound must be less than upper bound")
    trace: list[dict[str, float]] = []

    def record(theta: float, stage: str) -> tuple[float, float]:
        loss = float(loss_fn(theta))
        trace.append({"theta": theta, "loss": loss, "stage": stage})
        return theta, loss

    initial_loss = record(initial_theta, "initial")[1]
    candidates = [record(theta, "grid") for theta in linspace(lower, upper, grid_size)]
    finite_candidates = [(theta, loss) for theta, loss in candidates if math.isfinite(loss)]
    if not finite_candidates:
        raise ValueError("all candidate losses were non-finite")
    best_theta, best_loss = min(finite_candidates, key=lambda item: item[1])

    radius = (upper - lower) / max(grid_size - 1, 1)
    for round_index in range(refinement_rounds):
        local_lower = max(lower, best_theta - radius)
        local_upper = min(upper, best_theta + radius)
        local_candidates = [record(theta, f"refine_{round_index + 1}") for theta in linspace(local_lower, local_upper, max(7, min(grid_size, 21)))]
        finite_local = [(theta, loss) for theta, loss in local_candidates if math.isfinite(loss)]
        if finite_local:
            local_best_theta, local_best_loss = min(finite_local, key=lambda item: item[1])
            if local_best_loss < best_loss:
                best_theta, best_loss = local_best_theta, local_best_loss
        radius *= 0.5

    return {
        "initial_theta": initial_theta,
        "estimated_theta": best_theta,
        "loss_before": initial_loss,
        "loss_after": best_loss,
        "loss_improvement": initial_loss - best_loss,
        "params_before": {"theta": initial_theta},
        "params_after": {"theta": best_theta},
        "parameter_changed": abs(best_theta - initial_theta) > 1e-12,
        "trace": trace,
    }


def quadratic_loss(target: float) -> LossFn:
    return lambda theta: (theta - target) ** 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=float, default=1.25, help="Target for built-in quadratic smoke mode.")
    parser.add_argument("--initial-theta", type=float, default=0.0)
    parser.add_argument("--lower", type=float, default=-3.0)
    parser.add_argument("--upper", type=float, default=3.0)
    parser.add_argument("--grid-size", type=int, default=41)
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    result = minimise_scalar_grid(quadratic_loss(args.target), args.initial_theta, args.lower, args.upper, args.grid_size)
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
