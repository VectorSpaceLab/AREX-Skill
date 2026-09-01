#!/usr/bin/env python3
"""Scalar Gaussian posterior API for reduced SBI recovery."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path


class ScalarGaussianPosterior:
    def __init__(self, a: float, b: float, posterior_std: float):
        if posterior_std <= 0:
            raise ValueError("posterior_std must be positive")
        self.a = float(a)
        self.b = float(b)
        self.posterior_std = float(posterior_std)

    def mean(self, x_o: float) -> float:
        return self.a * float(x_o) + self.b

    def sample(self, x_o: float, count: int, seed: int = 0) -> list[float]:
        if count <= 0:
            raise ValueError("count must be positive")
        rng = random.Random(seed)
        mean = self.mean(x_o)
        return [rng.gauss(mean, self.posterior_std) for _ in range(count)]

    def log_prob(self, theta: float, x_o: float) -> float:
        mean = self.mean(x_o)
        variance = self.posterior_std ** 2
        return -0.5 * math.log(2.0 * math.pi * variance) - ((float(theta) - mean) ** 2) / (2.0 * variance)

    def summarize(self, x_o: float, sample_count: int = 32, seed: int = 0) -> dict:
        samples = self.sample(x_o, sample_count, seed=seed)
        mean_sample = sum(samples) / float(len(samples))
        variance_sample = sum((item - mean_sample) ** 2 for item in samples) / float(len(samples))
        return {
            "schema_version": 1,
            "x_o": float(x_o),
            "posterior_mean": self.mean(x_o),
            "posterior_std": self.posterior_std,
            "sample_count": sample_count,
            "sample_mean": mean_sample,
            "sample_variance": variance_sample,
            "first_samples": samples[:5],
            "log_prob_at_mean": self.log_prob(self.mean(x_o), x_o),
        }


def posterior_from_estimator(estimator: dict) -> ScalarGaussianPosterior:
    return ScalarGaussianPosterior(
        float(estimator["a"]),
        float(estimator["b"]),
        float(estimator.get("posterior_std", 1.0)),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Run a built-in posterior API demo.")
    parser.add_argument("--estimator", default="", help="JSON file containing an estimator or training result.")
    parser.add_argument("--x-o", type=float, default=1.0)
    parser.add_argument("--sample-count", type=int, default=32)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", default="", help="Optional JSON output path.")
    args = parser.parse_args()

    if args.estimator:
        data = json.loads(Path(args.estimator).read_text(encoding="utf-8"))
        estimator = data.get("estimator", data)
    elif args.demo:
        estimator = {"a": 0.5, "b": 0.0, "posterior_std": 0.75}
    else:
        parser.error("provide --demo or --estimator")

    posterior = posterior_from_estimator(estimator)
    result = posterior.summarize(args.x_o, sample_count=args.sample_count, seed=args.seed)
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        path = Path(args.output).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
