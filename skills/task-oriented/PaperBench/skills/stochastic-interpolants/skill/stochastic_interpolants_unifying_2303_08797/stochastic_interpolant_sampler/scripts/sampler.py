#!/usr/bin/env python3
"""Bounded samplers for stochastic-interpolant recovery checks."""

from __future__ import annotations

import argparse
import json
import math
import random
from typing import Callable, Iterable


def _floats(values: Iterable[float]) -> list[float]:
    return [float(value) for value in values]


def summarize(values: list[float]) -> dict:
    if not values:
        return {"count": 0, "mean": 0.0, "min": 0.0, "max": 0.0}
    return {"count": len(values), "mean": sum(values) / len(values), "min": min(values), "max": max(values)}


def integrate_ode(samples: Iterable[float], velocity: Callable[[float, float], float], steps: int = 20) -> dict:
    if steps <= 0:
        raise ValueError("steps must be positive")
    values = _floats(samples)
    dt = 1.0 / steps
    trajectory = [{"t": 0.0, "summary": summarize(values)}]
    for step in range(steps):
        t = step * dt
        values = [x + dt * velocity(t, x) for x in values]
    trajectory.append({"t": 1.0, "summary": summarize(values)})
    return {"solver": "euler_ode", "steps": steps, "samples": values, "trajectory": trajectory}


def integrate_sde(samples: Iterable[float], velocity: Callable[[float, float], float], score: Callable[[float, float], float], epsilon: float = 0.0, steps: int = 20, seed: int = 0) -> dict:
    if steps <= 0:
        raise ValueError("steps must be positive")
    rng = random.Random(seed)
    values = _floats(samples)
    dt = 1.0 / steps
    noise_scale = math.sqrt(max(0.0, 2.0 * epsilon * dt))
    trajectory = [{"t": 0.0, "summary": summarize(values)}]
    for step in range(steps):
        t = step * dt
        next_values = []
        for x in values:
            drift = velocity(t, x) + epsilon * score(t, x)
            next_values.append(x + dt * drift + noise_scale * rng.gauss(0.0, 1.0))
        values = next_values
    trajectory.append({"t": 1.0, "summary": summarize(values)})
    return {"solver": "euler_maruyama_sde", "epsilon": epsilon, "steps": steps, "samples": values, "trajectory": trajectory}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    output = integrate_ode([0.0, 1.0], lambda t, x: 2.0, steps=4)
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
