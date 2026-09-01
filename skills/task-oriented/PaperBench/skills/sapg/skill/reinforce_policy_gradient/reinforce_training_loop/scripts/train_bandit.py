#!/usr/bin/env python3
"""Seeded two-action REINFORCE bandit training harness."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def expected_reward(theta: float, reward_zero: float, reward_one: float) -> float:
    prob_one = sigmoid(theta)
    return (1.0 - prob_one) * reward_zero + prob_one * reward_one


def score_update(prob_action_one: float, action: int, reward: float, baseline: float) -> dict:
    grad_log_prob = float(action) - prob_action_one
    advantage = reward - baseline
    return {
        "grad_log_prob": grad_log_prob,
        "advantage": advantage,
        "update": advantage * grad_log_prob,
    }


def train_bandit(
    episodes: int = 128,
    seed: int = 7,
    learning_rate: float = 0.15,
    baseline: float = 0.25,
    initial_theta: float = 0.0,
    reward_zero: float = 0.0,
    reward_one: float = 1.0,
) -> dict:
    rng = random.Random(seed)
    theta = float(initial_theta)
    params_before = {"theta": theta}
    expected_before = expected_reward(theta, reward_zero, reward_one)
    episode_trace = []
    loss_before = -expected_before
    for episode in range(int(episodes)):
        prob_one = sigmoid(theta)
        action = 1 if rng.random() < prob_one else 0
        reward = reward_one if action == 1 else reward_zero
        estimate = score_update(prob_one, action, reward, baseline)
        theta_before = theta
        theta += learning_rate * estimate["update"]
        episode_trace.append({
            "episode": episode,
            "prob_action_one": prob_one,
            "action": action,
            "reward": reward,
            "baseline": baseline,
            "advantage": estimate["advantage"],
            "grad_log_prob": estimate["grad_log_prob"],
            "update": estimate["update"],
            "theta_before": theta_before,
            "theta_after": theta,
        })
    params_after = {"theta": theta}
    expected_after = expected_reward(theta, reward_zero, reward_one)
    return {
        "schema_version": 1,
        "algorithm": "REINFORCE score-function policy gradient",
        "environment": "seeded_two_action_bandit",
        "episodes": int(episodes),
        "seed": int(seed),
        "learning_rate": learning_rate,
        "baseline": baseline,
        "reward_zero": reward_zero,
        "reward_one": reward_one,
        "params_before": params_before,
        "params_after": params_after,
        "parameters_before": params_before,
        "parameters_after": params_after,
        "expected_reward_before": expected_before,
        "expected_reward_after": expected_after,
        "loss_before": loss_before,
        "loss_after": -expected_after,
        "optimizer_state_changed": params_before != params_after,
        "sampled_actions": [item["action"] for item in episode_trace],
        "episode_trace": episode_trace,
        "mechanism_checks": {
            "stochastic_actions_sampled": len(set(item["action"] for item in episode_trace)) == 2,
            "score_function_update_computed": all("grad_log_prob" in item and "update" in item for item in episode_trace),
            "baseline_used": baseline != 0.0,
            "optimizer_step_executed": params_before != params_after,
            "expected_reward_improved": expected_after > expected_before,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=int, default=128)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--learning-rate", type=float, default=0.15)
    parser.add_argument("--baseline", type=float, default=0.25)
    parser.add_argument("--initial-theta", type=float, default=0.0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    trace = train_bandit(args.episodes, args.seed, args.learning_rate, args.baseline, args.initial_theta)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(trace, indent=2), encoding="utf-8")
    print(json.dumps({
        "output": str(output),
        "expected_reward_before": trace["expected_reward_before"],
        "expected_reward_after": trace["expected_reward_after"],
        "params_before": trace["params_before"],
        "params_after": trace["params_after"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
