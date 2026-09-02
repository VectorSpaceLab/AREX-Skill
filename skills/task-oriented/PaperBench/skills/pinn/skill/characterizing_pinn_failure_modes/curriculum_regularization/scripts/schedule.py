#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any


def make_schedule(start: float, target: float, stages: int, residual_weight: float = 1.0) -> list[dict[str, Any]]:
    if stages < 1:
        raise ValueError("stages must be positive")
    if start < 0 or target < 0:
        raise ValueError("coefficients must be non-negative for this reduced convection scheduler")
    if stages == 1:
        values = [target]
    else:
        values = [start + (target - start) * i / (stages - 1) for i in range(stages)]
    if any(values[i] > values[i + 1] for i in range(len(values) - 1)) and target >= start:
        raise ValueError("schedule is not monotone increasing")
    return [{"stage": i, "beta": value, "residual_weight": residual_weight} for i, value in enumerate(values)]


def validate_schedule(schedule: list[dict[str, Any]], start: float, target: float) -> dict[str, Any]:
    betas = [float(s["beta"]) for s in schedule]
    return {
        "stage_count": len(schedule),
        "starts_at_expected": abs(betas[0] - (target if len(schedule) == 1 else start)) < 1e-12,
        "ends_at_target": abs(betas[-1] - target) < 1e-12,
        "monotone": all(betas[i] <= betas[i + 1] for i in range(len(betas) - 1)),
        "betas": betas
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=float, default=1.0)
    parser.add_argument("--target", type=float, default=30.0)
    parser.add_argument("--stages", type=int, default=4)
    parser.add_argument("--residual-weight", type=float, default=1.0)
    args = parser.parse_args()
    schedule = make_schedule(args.start, args.target, args.stages, args.residual_weight)
    print(json.dumps({"schedule": schedule, "validation": validate_schedule(schedule, args.start, args.target)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
