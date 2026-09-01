"""Annealed Langevin dynamics utilities."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from typing import Callable, Iterable


Vector = list[float]
Matrix = list[Vector]


def column_mean(samples: Matrix) -> Vector:
    return [sum(row[j] for row in samples) / len(samples) for j in range(len(samples[0]))]


def column_std(samples: Matrix) -> Vector:
    means = column_mean(samples)
    return [
        math.sqrt(sum((row[j] - means[j]) ** 2 for row in samples) / len(samples))
        for j in range(len(samples[0]))
    ]


def run_annealed_langevin(
    initial_samples: Matrix,
    score_fn: Callable[[Matrix, int | float], Matrix],
    levels: Iterable[int | float],
    step_size: float,
    steps_per_level: int,
    seed: int = 0,
) -> tuple[Matrix, dict]:
    if step_size <= 0:
        raise ValueError("step_size must be positive")
    if steps_per_level < 1:
        raise ValueError("steps_per_level must be positive")
    samples = [[float(value) for value in row] for row in initial_samples]
    rng = random.Random(seed)
    trace_levels = []
    for level in levels:
        norms = []
        for _ in range(steps_per_level):
            score = score_fn(samples, level)
            if len(score) != len(samples) or len(score[0]) != len(samples[0]):
                raise ValueError("score_fn returned an array with the wrong shape")
            norms.append(sum(math.sqrt(sum(value * value for value in row)) for row in score) / len(score))
            next_samples: Matrix = []
            for sample_row, score_row in zip(samples, score):
                next_samples.append([
                    value + 0.5 * step_size * score_value + math.sqrt(step_size) * rng.gauss(0.0, 1.0)
                    for value, score_value in zip(sample_row, score_row)
                ])
            samples = next_samples
        trace_levels.append(
            {
                "level": float(level),
                "mean_score_norm": sum(norms) / len(norms),
                "sample_mean": column_mean(samples),
            }
        )
    trace = {
        "seed": int(seed),
        "step_size": float(step_size),
        "steps_per_level": int(steps_per_level),
        "level_count": len(trace_levels),
        "levels": trace_levels,
        "final_sample_mean": column_mean(samples),
        "final_sample_std": column_std(samples),
    }
    return samples, trace


def gaussian_reference(sample_count: int, dim: int, variance: float, seed: int) -> Matrix:
    if sample_count < 1 or dim < 1:
        raise ValueError("sample_count and dim must be positive")
    if variance <= 0:
        raise ValueError("variance must be positive")
    rng = random.Random(seed)
    return [[rng.gauss(0.0, math.sqrt(variance)) for _ in range(dim)] for _ in range(sample_count)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-mean", required=True, help="JSON vector for demo Gaussian score.")
    parser.add_argument("--sample-count", type=int, default=64)
    parser.add_argument("--dim", type=int, default=2)
    parser.add_argument("--reference-variance", type=float, default=1.0)
    parser.add_argument("--step-size", type=float, default=0.02)
    parser.add_argument("--steps-per-level", type=int, default=5)
    parser.add_argument("--levels", default="[3,2,1]")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    target = [float(value) for value in json.loads(args.target_mean)]
    initial = gaussian_reference(args.sample_count, args.dim, args.reference_variance, args.seed)

    def score_fn(samples: Matrix, level: int | float) -> Matrix:
        return [[target[j] - row[j] for j in range(len(target))] for row in samples]

    samples, trace = run_annealed_langevin(
        initial,
        score_fn,
        json.loads(args.levels),
        step_size=args.step_size,
        steps_per_level=args.steps_per_level,
        seed=args.seed + 1,
    )
    result = {"samples": samples, "trace": trace}
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
