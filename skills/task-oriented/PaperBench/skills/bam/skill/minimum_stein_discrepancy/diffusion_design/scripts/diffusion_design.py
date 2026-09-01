#!/usr/bin/env python3
"""Scalar diffusion designs for Minimum Stein Discrepancy recovery."""

from __future__ import annotations

import argparse
import json
import math
from typing import Callable, Iterable

DiffusionFn = Callable[[float, float], float]


def ordinary_diffusion(theta: float, x: float) -> float:
    return 1.0


def student_t_heavy_tail_diffusion(theta: float, x: float, scale: float = 1.0, nu: float = 5.0) -> float:
    z = (x - theta) / scale
    return 1.0 + (z * z) / max(nu, 1e-12)


def robust_decay_diffusion(theta: float, x: float, alpha: float = 2.0) -> float:
    return 1.0 / (1.0 + abs(x) ** alpha)


def make_diffusion(kind: str, scale: float = 1.0, nu: float = 5.0, alpha: float = 2.0) -> DiffusionFn:
    if kind == "ordinary":
        return ordinary_diffusion
    if kind == "student_t_heavy_tail":
        return lambda theta, x: student_t_heavy_tail_diffusion(theta, x, scale=scale, nu=nu)
    if kind == "robust_decay":
        return lambda theta, x: robust_decay_diffusion(theta, x, alpha=alpha)
    raise ValueError(f"unsupported diffusion kind: {kind}")


def evaluate_diffusion(samples: Iterable[float], theta: float, kind: str, scale: float = 1.0, nu: float = 5.0, alpha: float = 2.0) -> dict[str, object]:
    xs = [float(x) for x in samples]
    if not xs:
        raise ValueError("samples must be non-empty")
    diffusion = make_diffusion(kind, scale=scale, nu=nu, alpha=alpha)
    values = [diffusion(theta, x) for x in xs]
    finite = all(math.isfinite(v) for v in values)
    positive = all(v > 0 for v in values)
    distances = [abs(x - theta) for x in xs]
    far_index = max(range(len(xs)), key=lambda i: distances[i])
    near_index = min(range(len(xs)), key=lambda i: distances[i])
    return {
        "kind": kind,
        "theta": theta,
        "values": values,
        "min": min(values),
        "max": max(values),
        "finite": finite,
        "positive": positive,
        "far_value": values[far_index],
        "near_value": values[near_index],
        "paper_mechanism": "diffusion factor changes Stein operator weighting without requiring normalising constants",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-json", required=True)
    parser.add_argument("--theta", type=float, required=True)
    parser.add_argument("--kind", default="student_t_heavy_tail", choices=["ordinary", "student_t_heavy_tail", "robust_decay"])
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--nu", type=float, default=5.0)
    parser.add_argument("--alpha", type=float, default=2.0)
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    result = evaluate_diffusion(json.loads(args.samples_json), args.theta, args.kind, args.scale, args.nu, args.alpha)
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
