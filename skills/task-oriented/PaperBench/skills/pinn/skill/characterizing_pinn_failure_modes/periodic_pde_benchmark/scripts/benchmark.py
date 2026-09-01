#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import random
from typing import Any


def build_convection_benchmark(beta: float = 30.0, x_points: int = 64, t_points: int = 16, collocation_count: int = 128, seed: int = 0) -> dict[str, Any]:
    if x_points < 2 or t_points < 2 or collocation_count < 1:
        raise ValueError("x_points and t_points must be >=2 and collocation_count must be >=1")
    xs = [2.0 * math.pi * i / x_points for i in range(x_points)]
    ts = [i / (t_points - 1) for i in range(t_points)]
    values = [[math.sin((x - beta * t) % (2.0 * math.pi)) for x in xs] for t in ts]
    rng = random.Random(seed)
    collocation = [[rng.random() * 2.0 * math.pi, rng.random()] for _ in range(collocation_count)]
    boundary_pairs = [[[0.0, t], [2.0 * math.pi, t]] for t in ts]
    initial = [[x, 0.0, math.sin(x)] for x in xs]
    return {
        "system": "convection",
        "coefficients": {"beta": beta},
        "domain": {"x": [0.0, 2.0 * math.pi], "t": [0.0, 1.0], "periodic_x": True},
        "grid": {"x": xs, "t": ts, "values": values},
        "collocation": collocation,
        "boundary_pairs": boundary_pairs,
        "initial_condition": initial,
        "target_type": "exact_periodic_sinusoid"
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--beta", type=float, default=30.0)
    parser.add_argument("--x-points", type=int, default=64)
    parser.add_argument("--t-points", type=int, default=16)
    parser.add_argument("--collocation-count", type=int, default=128)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    print(json.dumps(build_convection_benchmark(args.beta, args.x_points, args.t_points, args.collocation_count, args.seed), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
