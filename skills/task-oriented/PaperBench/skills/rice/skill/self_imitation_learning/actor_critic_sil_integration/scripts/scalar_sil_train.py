#!/usr/bin/env python3
"""Run a deterministic scalar actor-critic SIL update."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def selected_probability(policy_logit: float, action: int) -> float:
    p_one = sigmoid(policy_logit)
    return p_one if int(action) == 1 else 1.0 - p_one


def sil_loss(records, policy_logit: float, value_bias: float, beta: float):
    total = 0.0
    details = []
    for record in records:
        probability = selected_probability(policy_logit, int(record["action"]))
        advantage = max(float(record["return"]) - value_bias, 0.0)
        item_loss = -math.log(max(probability, 1e-8)) * advantage + beta * 0.5 * advantage * advantage
        total += item_loss
        details.append({"probability": probability, "value": value_bias, "positive_advantage": advantage, "loss": item_loss})
    return total / max(len(records), 1), details


def train_scalar_sil(records, learning_rate=0.2, updates=20, beta=0.1, initial_policy_logit=0.0, initial_value_bias=0.0):
    policy_logit = float(initial_policy_logit)
    value_bias = float(initial_value_bias)
    params_before = {"policy_logit": policy_logit, "value_bias": value_bias}
    loss_before, details_before = sil_loss(records, policy_logit, value_bias, beta)
    for _ in range(int(updates)):
        grad_logit = 0.0
        grad_value = 0.0
        for record in records:
            action = int(record["action"])
            ret = float(record["return"])
            probability = selected_probability(policy_logit, action)
            advantage = ret - value_bias
            if advantage <= 0.0:
                continue
            if action == 1:
                grad_logit += -(1.0 - probability) * advantage
            else:
                grad_logit += probability * advantage
            grad_value += math.log(max(probability, 1e-8)) - beta * advantage
        scale = 1.0 / max(len(records), 1)
        policy_logit -= learning_rate * grad_logit * scale
        value_bias -= learning_rate * grad_value * scale
    params_after = {"policy_logit": policy_logit, "value_bias": value_bias}
    loss_after, details_after = sil_loss(records, policy_logit, value_bias, beta)
    return {
        "loss_before": loss_before,
        "loss_after": loss_after,
        "params_before": params_before,
        "params_after": params_after,
        "parameters_before": params_before,
        "parameters_after": params_after,
        "details_before": details_before,
        "details_after": details_after,
        "optimizer_step_executed": params_before != params_after,
        "reduced_training_executed": True,
        "full_actor_critic_runtime": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay_json")
    parser.add_argument("--output", required=True)
    parser.add_argument("--learning-rate", type=float, default=0.2)
    parser.add_argument("--updates", type=int, default=20)
    parser.add_argument("--beta", type=float, default=0.1)
    args = parser.parse_args()
    records = json.loads(Path(args.replay_json).read_text(encoding="utf-8"))
    result = train_scalar_sil(records, args.learning_rate, args.updates, args.beta)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
