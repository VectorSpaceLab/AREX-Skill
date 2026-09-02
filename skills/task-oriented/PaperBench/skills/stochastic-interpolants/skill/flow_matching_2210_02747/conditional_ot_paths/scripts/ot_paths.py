#!/usr/bin/env python3
"""Deterministic utilities for Flow Matching conditional OT paths."""

import argparse
import json
import math
from typing import Iterable, List, Sequence

Number = float
Vector = List[Number]


def _as_float_vector(values: Iterable[Number]) -> Vector:
    return [float(value) for value in values]


def validate_time(t: float) -> float:
    t = float(t)
    if not 0.0 <= t <= 1.0:
        raise ValueError("t must be in [0, 1]")
    return t


def validate_sigma_min(sigma_min: float) -> float:
    sigma_min = float(sigma_min)
    if not 0.0 < sigma_min <= 1.0:
        raise ValueError("sigma_min must be in (0, 1]")
    return sigma_min


def sigma_t(t: float, sigma_min: float) -> float:
    t = validate_time(t)
    sigma_min = validate_sigma_min(sigma_min)
    return 1.0 - (1.0 - sigma_min) * t


def interpolate_ot(x0: Sequence[Number], x1: Sequence[Number], t: float, sigma_min: float = 0.001) -> Vector:
    if len(x0) != len(x1):
        raise ValueError("x0 and x1 must have the same dimension")
    scale = sigma_t(t, sigma_min)
    t = float(t)
    return [scale * float(a) + t * float(b) for a, b in zip(x0, x1)]


def target_ot(x0: Sequence[Number], x1: Sequence[Number], sigma_min: float = 0.001) -> Vector:
    if len(x0) != len(x1):
        raise ValueError("x0 and x1 must have the same dimension")
    sigma_min = validate_sigma_min(sigma_min)
    return [float(b) - (1.0 - sigma_min) * float(a) for a, b in zip(x0, x1)]


def squared_distance(a: Sequence[Number], b: Sequence[Number]) -> float:
    if len(a) != len(b):
        raise ValueError("vectors must have the same dimension")
    return sum((float(x) - float(y)) ** 2 for x, y in zip(a, b))


def path_diagnostics(x0: Sequence[Number], x1: Sequence[Number], sigma_min: float = 0.001) -> dict:
    start = interpolate_ot(x0, x1, 0.0, sigma_min)
    end = interpolate_ot(x0, x1, 1.0, sigma_min)
    expected_end = [validate_sigma_min(sigma_min) * float(a) + float(b) for a, b in zip(x0, x1)]
    target_a = target_ot(x0, x1, sigma_min)
    target_b = target_ot(x0, x1, sigma_min)
    finite = all(math.isfinite(value) for value in start + end + target_a)
    return {
        "start_mse": squared_distance(start, x0) / max(1, len(x0)),
        "end_mse": squared_distance(end, expected_end) / max(1, len(x0)),
        "target_time_invariant": target_a == target_b,
        "finite": finite,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--x0", required=True, help="JSON vector")
    parser.add_argument("--x1", required=True, help="JSON vector")
    parser.add_argument("--t", type=float, required=True)
    parser.add_argument("--sigma-min", type=float, default=0.001)
    args = parser.parse_args()
    x0 = _as_float_vector(json.loads(args.x0))
    x1 = _as_float_vector(json.loads(args.x1))
    output = {
        "x_t": interpolate_ot(x0, x1, args.t, args.sigma_min),
        "u_t": target_ot(x0, x1, args.sigma_min),
        "diagnostics": path_diagnostics(x0, x1, args.sigma_min),
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
