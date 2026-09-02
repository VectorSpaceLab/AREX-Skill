#!/usr/bin/env python3
"""Tiny REINFORCE policy update for RLAIF reduced recovery."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def softmax(logits: list[float]) -> list[float]:
    offset = max(logits)
    exps = [math.exp(value - offset) for value in logits]
    denom = sum(exps)
    return [value / denom for value in exps]


def reinforce_step(
    logits: list[float],
    chosen_action: int,
    reward: float,
    *,
    baseline: float = 0.0,
    learning_rate: float = 0.4,
    reference_logits: list[float] | None = None,
    kl_coefficient: float = 0.05,
) -> dict:
    if chosen_action < 0 or chosen_action >= len(logits):
        raise ValueError("chosen_action is out of range")
    params_before = list(float(value) for value in logits)
    reference_logits = list(reference_logits) if reference_logits is not None else list(params_before)
    probs_before = softmax(params_before)
    ref_probs = softmax(reference_logits)
    advantage = float(reward) - float(baseline)
    loss_before = -math.log(max(1e-12, probs_before[chosen_action])) * advantage
    grad = []
    for idx, prob in enumerate(probs_before):
        indicator = 1.0 if idx == chosen_action else 0.0
        pg_grad = -(indicator - prob) * advantage
        kl_grad = kl_coefficient * (prob - ref_probs[idx])
        grad.append(pg_grad + kl_grad)
    params_after = [value - learning_rate * g for value, g in zip(params_before, grad)]
    probs_after = softmax(params_after)
    loss_after = -math.log(max(1e-12, probs_after[chosen_action])) * advantage
    return {
        "params_before": params_before,
        "params_after": params_after,
        "probabilities_before": probs_before,
        "probabilities_after": probs_after,
        "chosen_action": chosen_action,
        "reward": reward,
        "baseline": baseline,
        "advantage": advantage,
        "kl_coefficient": kl_coefficient,
        "loss_before": loss_before,
        "loss_after": loss_after,
        "optimizer_state_changed": params_before != params_after,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.smoke or not args.input:
        result = reinforce_step([0.0, 0.0], 1, 0.75, baseline=0.0)
    else:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        result = reinforce_step(
            data["logits"],
            int(data["chosen_action"]),
            float(data["reward"]),
            baseline=float(data.get("baseline", 0.0)),
            learning_rate=float(data.get("learning_rate", 0.4)),
            reference_logits=data.get("reference_logits"),
            kl_coefficient=float(data.get("kl_coefficient", 0.05)),
        )
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
