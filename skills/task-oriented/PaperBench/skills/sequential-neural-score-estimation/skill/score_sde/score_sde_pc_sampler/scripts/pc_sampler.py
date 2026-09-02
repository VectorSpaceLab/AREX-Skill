#!/usr/bin/env python3
"""Tiny predictor-corrector sampler diagnostics."""

from __future__ import annotations

import argparse
import json
import math
import random
from typing import List


def gaussian_score(x: float, variance: float = 1.0) -> float:
    return -x / variance


def run_pc_sampler(initial: float, steps: int = 5, corrector_steps: int = 1, snr: float = 0.1, seed: int = 0) -> dict:
    rng = random.Random(seed)
    x = float(initial)
    trajectory: List[dict] = []
    predictor_count = 0
    corrector_count = 0
    for index in range(steps):
        t = 1.0 - index / max(steps, 1)
        score = gaussian_score(x)
        dt = -1.0 / steps
        drift = -score
        x_mean = x + drift * dt
        x = x_mean
        predictor_count += 1
        for _ in range(corrector_steps):
            score = gaussian_score(x)
            step_size = (snr * abs(score) + 1e-4) ** 2
            noise = rng.gauss(0.0, 1.0) * 0.0
            x = x + step_size * score + math.sqrt(2.0 * step_size) * noise
            corrector_count += 1
        trajectory.append({"step": index, "time": t, "state": x, "score": gaussian_score(x)})
    return {
        "initial": initial,
        "final": x,
        "trajectory": trajectory,
        "predictor_count": predictor_count,
        "corrector_count": corrector_count,
        "finite": math.isfinite(x) and all(math.isfinite(item["state"]) for item in trajectory),
        "moved_toward_zero": abs(x) < abs(initial),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--initial", type=float, required=True)
    parser.add_argument("--steps", type=int, default=5)
    parser.add_argument("--corrector-steps", type=int, default=1)
    args = parser.parse_args()
    print(json.dumps(run_pc_sampler(args.initial, args.steps, args.corrector_steps), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
