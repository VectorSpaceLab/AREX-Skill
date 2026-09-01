#!/usr/bin/env python3
"""Compute positive-advantage Self-Imitation Learning losses."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def compute_sil_loss(returns, values, action_probabilities, beta=0.01, eps=1e-8):
    if not (len(returns) == len(values) == len(action_probabilities)):
        raise ValueError("returns, values, and action_probabilities must have equal length")
    if len(returns) == 0:
        return {
            "positive_advantages": [],
            "valid_mask": [],
            "valid_count": 0,
            "policy_loss": 0.0,
            "value_loss": 0.0,
            "total_loss": 0.0,
        }
    positive_advantages = [max(float(ret) - float(val), 0.0) for ret, val in zip(returns, values)]
    valid_mask = [adv > 0.0 for adv in positive_advantages]
    policy_terms = []
    value_terms = []
    for probability, advantage in zip(action_probabilities, positive_advantages):
        clipped = min(max(float(probability), eps), 1.0)
        policy_terms.append(-math.log(clipped) * advantage)
        value_terms.append(0.5 * advantage * advantage)
    count = len(returns)
    policy_loss = sum(policy_terms) / count
    value_loss = sum(value_terms) / count
    total_loss = policy_loss + float(beta) * value_loss
    return {
        "positive_advantages": positive_advantages,
        "valid_mask": valid_mask,
        "valid_count": sum(1 for item in valid_mask if item),
        "policy_loss": policy_loss,
        "value_loss": value_loss,
        "total_loss": total_loss,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json", help="JSON with returns, values, action_probabilities, and optional beta")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    result = compute_sil_loss(
        payload["returns"],
        payload["values"],
        payload["action_probabilities"],
        beta=payload.get("beta", 0.01),
    )
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
