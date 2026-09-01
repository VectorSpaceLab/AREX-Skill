#!/usr/bin/env python3
"""REINFORCE score-function helper for a Bernoulli-logit policy."""

from __future__ import annotations

import argparse
import json


def clamp_probability(probability: float, eps: float = 1e-8) -> float:
    return min(1.0 - eps, max(eps, float(probability)))


def bernoulli_score_update(prob_action_one: float, action: int, reward: float, baseline: float = 0.0) -> dict:
    if action not in (0, 1):
        raise ValueError("action must be 0 or 1")
    prob = clamp_probability(prob_action_one)
    grad_log_prob = float(action) - prob
    advantage = float(reward) - float(baseline)
    update = advantage * grad_log_prob
    return {
        "prob_action_one": prob,
        "action": int(action),
        "reward": float(reward),
        "baseline": float(baseline),
        "advantage": advantage,
        "grad_log_prob": grad_log_prob,
        "update": update,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prob", type=float, required=True)
    parser.add_argument("--action", type=int, required=True)
    parser.add_argument("--reward", type=float, required=True)
    parser.add_argument("--baseline", type=float, default=0.0)
    args = parser.parse_args()
    print(json.dumps(bernoulli_score_update(args.prob, args.action, args.reward, args.baseline), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
