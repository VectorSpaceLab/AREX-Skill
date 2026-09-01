#!/usr/bin/env python3
import argparse
import json
import math


def _floats(values, name):
    if not isinstance(values, list) or not values:
        raise ValueError(f"{name} must be a non-empty list")
    out = [float(value) for value in values]
    if not all(math.isfinite(value) for value in out):
        raise ValueError(f"{name} contains non-finite values")
    return out


def _terminals(values):
    if not isinstance(values, list) or not values:
        raise ValueError("terminal_flags must be a non-empty list")
    return [bool(value) for value in values]


def estimate_advantages(rewards, value_predictions, terminal_flags, next_value_prediction, gamma=0.99, gae_lambda=0.95):
    rewards = _floats(rewards, "rewards")
    values = _floats(value_predictions, "value_predictions")
    terminals = _terminals(terminal_flags)
    if not (len(rewards) == len(values) == len(terminals)):
        raise ValueError("rewards, value_predictions, and terminal_flags must have equal length")
    gamma = float(gamma)
    gae_lambda = float(gae_lambda)
    next_value_prediction = float(next_value_prediction)
    if not all(math.isfinite(value) for value in [gamma, gae_lambda, next_value_prediction]):
        raise ValueError("gamma, gae_lambda, and next_value_prediction must be finite")

    extended_values = values + [next_value_prediction]
    advantages = [0.0 for _ in rewards]
    last_gae = 0.0
    for index in range(len(rewards) - 1, -1, -1):
        nonterminal = 0.0 if terminals[index] else 1.0
        delta = rewards[index] + gamma * extended_values[index + 1] * nonterminal - extended_values[index]
        last_gae = delta + gamma * gae_lambda * nonterminal * last_gae
        advantages[index] = last_gae
    returns = [advantage + value for advantage, value in zip(advantages, values)]
    mean_advantage = sum(advantages) / len(advantages)
    variance = sum((value - mean_advantage) ** 2 for value in advantages) / len(advantages)
    std = math.sqrt(variance)
    if std < 1e-12:
        normalized = [0.0 for _ in advantages]
    else:
        normalized = [(value - mean_advantage) / std for value in advantages]
    return {
        "advantages": advantages,
        "returns": returns,
        "normalized_advantages": normalized,
        "mean_advantage": mean_advantage,
        "std_advantage": std,
        "sample_count": len(rewards),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rewards", required=True)
    parser.add_argument("--values", required=True)
    parser.add_argument("--terminals", required=True)
    parser.add_argument("--next-value", type=float, required=True)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--gae-lambda", type=float, default=0.95)
    args = parser.parse_args()
    result = estimate_advantages(
        json.loads(args.rewards),
        json.loads(args.values),
        json.loads(args.terminals),
        args.next_value,
        args.gamma,
        args.gae_lambda,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
