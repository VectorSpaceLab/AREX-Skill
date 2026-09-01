#!/usr/bin/env python3
"""Pure-Python centered multinomial bootstrap for KSD U-statistic tests."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path


def validate_matrix(stein_matrix) -> list[list[float]]:
    matrix = [[float(item) for item in row] for row in stein_matrix]
    if not matrix or any(len(row) != len(matrix) for row in matrix):
        raise ValueError("stein_matrix must be a non-empty square matrix")
    if len(matrix) < 2:
        raise ValueError("at least two samples are required")
    for row in matrix:
        if any(not math.isfinite(value) for value in row):
            raise ValueError("stein_matrix contains non-finite values")
    return matrix


def ksd_u_statistic(stein_matrix) -> float:
    matrix = validate_matrix(stein_matrix)
    n = len(matrix)
    total = sum(sum(row) for row in matrix)
    diagonal = sum(matrix[i][i] for i in range(n))
    return (total - diagonal) / (n * (n - 1))


def multinomial_counts(rng: random.Random, n: int) -> list[int]:
    counts = [0] * n
    for _ in range(n):
        counts[rng.randrange(n)] += 1
    return counts


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    index = probability * (len(ordered) - 1)
    lower = int(math.floor(index))
    upper = int(math.ceil(index))
    if lower == upper:
        return ordered[lower]
    fraction = index - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def bootstrap_ksd_test(stein_matrix, alpha: float = 0.05, num_bootstrap: int = 1000, seed: int = 0) -> dict:
    matrix = validate_matrix(stein_matrix)
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be between 0 and 1")
    if num_bootstrap < 1:
        raise ValueError("num_bootstrap must be positive")
    n = len(matrix)
    observed = ksd_u_statistic(matrix)
    rng = random.Random(seed)
    boot = []
    for _ in range(num_bootstrap):
        counts = multinomial_counts(rng, n)
        centered = [(count / n) - (1.0 / n) for count in counts]
        value = 0.0
        for i in range(n):
            for j in range(n):
                if i != j:
                    value += centered[i] * centered[j] * matrix[i][j]
        boot.append(n * value)
    scaled_observed = n * observed
    p_value = sum(1 for value in boot if value > scaled_observed) / len(boot)
    return {
        "n": n,
        "alpha": float(alpha),
        "num_bootstrap": int(num_bootstrap),
        "seed": int(seed),
        "ksd_u": float(observed),
        "scaled_observed": float(scaled_observed),
        "p_value": float(p_value),
        "reject": bool(p_value < alpha),
        "bootstrap_mean": float(sum(boot) / len(boot)),
        "bootstrap_quantile_95": float(quantile(boot, 0.95)),
        "bootstrap_scaled": boot,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json", help="JSON file containing stein_matrix")
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--num-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    data = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    result = bootstrap_ksd_test(data["stein_matrix"], args.alpha, args.num_bootstrap, args.seed)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
