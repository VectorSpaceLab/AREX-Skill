#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from typing import Any


def surrogate_loss(params: list[float], targets: list[float], entropy_coef: float) -> float:
    if len(params) != len(targets):
        raise ValueError("params and targets must have the same length")
    mse = sum((param - target) ** 2 for param, target in zip(params, targets)) / len(params)
    entropy_bonus = entropy_coef * sum(math.log1p(math.exp(-abs(param))) for param in params) / len(params)
    return mse - entropy_bonus


def policy_update_step(params: list[float], targets: list[float], learning_rate: float = 0.2, entropy_coef: float = 0.05) -> dict[str, Any]:
    if not params:
        raise ValueError("params must be non-empty")
    if learning_rate <= 0:
        raise ValueError("learning_rate must be positive")
    before = list(params)
    loss_before = surrogate_loss(before, targets, entropy_coef)
    gradients = []
    for param, target in zip(before, targets):
        mse_grad = 2.0 * (param - target) / len(before)
        entropy_grad = -entropy_coef * (1.0 / (1.0 + math.exp(abs(param)))) * (1.0 if param >= 0 else -1.0) / len(before)
        gradients.append(mse_grad - entropy_grad)
    after = [param - learning_rate * grad for param, grad in zip(before, gradients)]
    loss_after = surrogate_loss(after, targets, entropy_coef)
    return {
        "params_before": before,
        "params_after": after,
        "targets": targets,
        "gradients": gradients,
        "loss_before": loss_before,
        "loss_after": loss_after,
        "loss_delta": loss_before - loss_after,
        "entropy_coefficient": entropy_coef,
        "optimizer_step_executed": before != after,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if not args.demo:
        parser.error("use --demo for the built-in smoke example")
    output = policy_update_step([0.0, 0.1, -0.1], [-1.0, 0.0, 1.0])
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
