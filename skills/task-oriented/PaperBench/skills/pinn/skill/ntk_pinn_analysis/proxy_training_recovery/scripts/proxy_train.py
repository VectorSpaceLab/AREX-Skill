#!/usr/bin/env python3
"""Run a deterministic proxy training comparison for NTK-weighted PINNs."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def component_losses(params: dict[str, float]) -> dict[str, float]:
    boundary_error = params["boundary"] - 1.0
    residual_error = 10.0 * params["residual"] - 1.0
    return {
        "boundary_loss": 0.5 * boundary_error * boundary_error,
        "residual_loss": 0.5 * residual_error * residual_error,
        "boundary_error": boundary_error,
        "residual_error": residual_error,
    }


def weighted_step(params: dict[str, float], lambda_b: float, lambda_r: float, learning_rate: float) -> dict[str, float]:
    losses = component_losses(params)
    grad_boundary = lambda_b * losses["boundary_error"]
    grad_residual = lambda_r * losses["residual_error"] * 10.0
    return {
        "boundary": params["boundary"] - learning_rate * grad_boundary,
        "residual": params["residual"] - learning_rate * grad_residual,
    }


def imbalance_gap(losses: dict[str, float]) -> float:
    boundary = losses["boundary_loss"]
    residual = losses["residual_loss"]
    return abs(math.log((boundary + 1e-12) / (residual + 1e-12)))


def run_proxy(lambda_b: float = 101.0, lambda_r: float = 1.01, learning_rate: float = 0.005) -> dict:
    initial = {"boundary": 0.0, "residual": 0.0}
    before = component_losses(initial)
    equal_after_params = weighted_step(initial, 1.0, 1.0, learning_rate)
    adaptive_after_params = weighted_step(initial, lambda_b, lambda_r, learning_rate)
    equal_after = component_losses(equal_after_params)
    adaptive_after = component_losses(adaptive_after_params)
    equal_gap = imbalance_gap(equal_after)
    adaptive_gap = imbalance_gap(adaptive_after)
    improvement = max(0.0, equal_gap - adaptive_gap)
    return {
        "schema_version": 1,
        "params_before": initial,
        "params_after": adaptive_after_params,
        "parameters_before": initial,
        "parameters_after": adaptive_after_params,
        "loss_before": before["boundary_loss"] + before["residual_loss"],
        "loss_after": adaptive_after["boundary_loss"] + adaptive_after["residual_loss"],
        "equal_weight": {"params_after": equal_after_params, "losses_after": equal_after, "imbalance_gap": equal_gap},
        "adaptive_weight": {"lambda_b": lambda_b, "lambda_r": lambda_r, "losses_after": adaptive_after, "imbalance_gap": adaptive_gap},
        "adaptive_loss_ratio_improvement": improvement,
        "optimizer_state_changed": initial != adaptive_after_params,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", required=True, help="JSON weights file")
    parser.add_argument("--output", required=True, help="Training trace output")
    parser.add_argument("--learning-rate", type=float, default=0.005)
    args = parser.parse_args()
    weights = json.loads(Path(args.weights).read_text(encoding="utf-8"))
    trace = run_proxy(weights["lambda_b"], weights["lambda_r"], args.learning_rate)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "improvement": trace["adaptive_loss_ratio_improvement"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
