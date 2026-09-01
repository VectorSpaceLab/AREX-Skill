#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from typing import Any


def log_softmax_row(row: list[float]) -> list[float]:
    if not row:
        raise ValueError("logit rows must be non-empty")
    maximum = max(row)
    log_total = maximum + math.log(sum(math.exp(value - maximum) for value in row))
    return [value - log_total for value in row]


def compute_diayn_rewards(logits: list[list[float]], skills: list[int], log_prior: float) -> dict[str, Any]:
    if len(logits) != len(skills):
        raise ValueError("logits and skills must have the same batch length")
    if not logits:
        raise ValueError("batch must be non-empty")
    log_probs = [log_softmax_row(row) for row in logits]
    selected = []
    predictions = []
    for row, skill in zip(log_probs, skills):
        if skill < 0 or skill >= len(row):
            raise ValueError("skill id out of range for logits row")
        selected.append(row[skill])
        predictions.append(max(range(len(row)), key=lambda index: row[index]))
    rewards = [value - log_prior for value in selected]
    loss = -sum(selected) / len(selected)
    accuracy = sum(1 for pred, gold in zip(predictions, skills) if pred == gold) / len(skills)
    return {
        "log_probs": log_probs,
        "selected_log_probs": selected,
        "rewards": rewards,
        "mean_reward": sum(rewards) / len(rewards),
        "cross_entropy_loss": loss,
        "accuracy": accuracy,
        "predictions": predictions,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if not args.demo:
        parser.error("use --demo for the built-in smoke example")
    output = compute_diayn_rewards([[3.0, 0.0, -1.0], [0.1, 2.0, -0.5]], [0, 1], -math.log(3))
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
