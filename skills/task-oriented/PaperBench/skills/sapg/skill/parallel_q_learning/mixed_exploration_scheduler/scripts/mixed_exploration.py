#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random


def assign_scales(actor_count: int, scales: list[float]) -> list[float]:
    if actor_count <= 0:
        raise ValueError("actor_count must be positive")
    if not scales:
        raise ValueError("scales must be non-empty")
    if any(scale < 0 for scale in scales):
        raise ValueError("scales must be non-negative")
    return [scales[index % len(scales)] for index in range(actor_count)]


def noisy_actions(actor_count: int, scales: list[float], base_actions: list[float] | float, low: float = -1.0, high: float = 1.0, seed: int = 0) -> dict:
    if low >= high:
        raise ValueError("low must be smaller than high")
    assignments = assign_scales(actor_count, scales)
    if isinstance(base_actions, (int, float)):
        bases = [float(base_actions)] * actor_count
    else:
        bases = [float(value) for value in base_actions]
        if len(bases) != actor_count:
            raise ValueError("base_actions length must equal actor_count")
    rng = random.Random(seed)
    actions = []
    noises = []
    for base, scale in zip(bases, assignments):
        noise = rng.gauss(0.0, scale) if scale else 0.0
        action = max(low, min(high, base + noise))
        noises.append(noise)
        actions.append(action)
    mean = sum(actions) / len(actions)
    variance = sum((action - mean) ** 2 for action in actions) / len(actions)
    return {
        "actor_count": actor_count,
        "scales": assignments,
        "actions": actions,
        "noises": noises,
        "stats": {
            "distinct_scales": len(set(assignments)),
            "action_variance": variance,
            "min_action": min(actions),
            "max_action": max(actions),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--actor-count", type=int, required=True)
    parser.add_argument("--scales", required=True, help="comma-separated scales")
    parser.add_argument("--base-action", type=float, default=0.0)
    parser.add_argument("--low", type=float, default=-1.0)
    parser.add_argument("--high", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    scales = [float(part) for part in args.scales.split(",") if part.strip()]
    result = noisy_actions(args.actor_count, scales, args.base_action, args.low, args.high, args.seed)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
