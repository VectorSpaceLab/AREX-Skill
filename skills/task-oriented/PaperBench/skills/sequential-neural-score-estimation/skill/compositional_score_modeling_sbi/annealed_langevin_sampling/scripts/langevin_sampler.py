#!/usr/bin/env python3
"""Bounded one-dimensional annealed Langevin sampler."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path


def gaussian_score(theta: float, mean: float, variance: float) -> float:
    return -(theta - mean) / variance


def sample_gaussian(mean: float, variance: float, sample_count: int, seed: int, levels: int = 8, steps_per_level: int = 8, step_size: float = 0.03, reference_variance: float = 1.0) -> dict:
    rng = random.Random(seed)
    samples = [rng.gauss(0.0, math.sqrt(reference_variance)) for _ in range(sample_count)]
    initial_mean = sum(samples) / len(samples)
    score_evaluations = 0
    score_norms = []
    for level in range(levels, 0, -1):
        progress = level / levels
        for _ in range(steps_per_level):
            for idx, value in enumerate(samples):
                score = gaussian_score(value, mean, variance)
                score_evaluations += 1
                score_norms.append(abs(score))
                noise = rng.gauss(0.0, 1.0)
                samples[idx] = value + 0.5 * step_size * progress * score + math.sqrt(step_size) * noise
    final_mean = sum(samples) / len(samples)
    return {
        "schema_version": 1,
        "samples": samples,
        "trace": {
            "seed": seed,
            "sample_count": sample_count,
            "levels": levels,
            "steps_per_level": steps_per_level,
            "step_size": step_size,
            "reference_variance": reference_variance,
            "score_evaluations": score_evaluations,
            "initial_mean": initial_mean,
            "final_mean": final_mean,
            "target_mean": mean,
            "target_variance": variance,
            "mean_abs_score": sum(score_norms) / len(score_norms),
            "all_finite": all(math.isfinite(value) for value in samples),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mean", type=float, required=True)
    parser.add_argument("--variance", type=float, required=True)
    parser.add_argument("--sample-count", type=int, default=128)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--levels", type=int, default=8)
    parser.add_argument("--steps-per-level", type=int, default=8)
    parser.add_argument("--step-size", type=float, default=0.03)
    parser.add_argument("--reference-variance", type=float, default=1.0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = sample_gaussian(args.mean, args.variance, args.sample_count, args.seed, args.levels, args.steps_per_level, args.step_size, args.reference_variance)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["trace"]["all_finite"], "output": args.output, "score_evaluations": result["trace"]["score_evaluations"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
