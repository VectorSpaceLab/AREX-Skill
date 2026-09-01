#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from typing import List, Sequence

Matrix = List[List[float]]


def validate_embeddings(embeddings: Sequence[Sequence[float]]) -> Matrix:
    if len(embeddings) < 2:
        raise ValueError("at least two embeddings are required")
    rows: Matrix = []
    width = None
    for row in embeddings:
        if not row:
            raise ValueError("embedding rows must be non-empty")
        converted = [float(item) for item in row]
        if any(not math.isfinite(item) for item in converted):
            raise ValueError("embeddings contain non-finite values")
        if width is None:
            width = len(converted)
        elif len(converted) != width:
            raise ValueError("embeddings must be rectangular")
        rows.append(converted)
    return rows


def euclidean(left: Sequence[float], right: Sequence[float]) -> float:
    return math.sqrt(sum((a - b) * (a - b) for a, b in zip(left, right)))


def particle_entropy_reward(embeddings: Sequence[Sequence[float]], k: int = 3, epsilon: float = 1e-6) -> dict:
    rows = validate_embeddings(embeddings)
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    effective_k = max(1, min(int(k), len(rows) - 1))
    rewards = []
    neighbor_distances = []
    for index, row in enumerate(rows):
        distances = sorted(euclidean(row, other) for other_index, other in enumerate(rows) if other_index != index)
        selected = distances[:effective_k]
        neighbor_distances.append(selected)
        rewards.append(sum(math.log(distance + epsilon) for distance in selected) / effective_k)
    diagnostics = {
        "effective_k": effective_k,
        "min_reward": min(rewards),
        "max_reward": max(rewards),
        "mean_reward": sum(rewards) / len(rewards),
        "neighbor_distances": neighbor_distances,
    }
    return {"rewards": rewards, "diagnostics": diagnostics}


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute CIC particle entropy rewards.")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if not args.demo:
        parser.error("Use --demo for CLI output or import particle_entropy_reward.")
    embeddings = [[0, 0], [0.1, 0.0], [3.0, 3.0], [3.1, 3.0]]
    print(json.dumps(particle_entropy_reward(embeddings, k=1), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
