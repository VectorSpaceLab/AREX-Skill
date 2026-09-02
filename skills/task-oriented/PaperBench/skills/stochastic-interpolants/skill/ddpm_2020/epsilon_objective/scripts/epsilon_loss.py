#!/usr/bin/env python3
"""DDPM epsilon-prediction objective helpers."""

from __future__ import annotations

import argparse
import json


def _as_list(values):
    if isinstance(values, (int, float)):
        return [float(values)]
    return [float(value) for value in values]


def epsilon_loss(true_epsilon, predicted_epsilon) -> dict:
    true_values = _as_list(true_epsilon)
    pred_values = _as_list(predicted_epsilon)
    if not true_values:
        raise ValueError("epsilon lists must be non-empty")
    if len(true_values) != len(pred_values):
        raise ValueError("true and predicted epsilon must have the same length")
    residuals = [truth - pred for truth, pred in zip(true_values, pred_values)]
    squared = [value * value for value in residuals]
    return {
        "mse": sum(squared) / len(squared),
        "residuals": residuals,
        "squared_errors": squared,
        "count": len(squared),
    }


def weighted_epsilon_loss(true_epsilon, predicted_epsilon, schedule: dict, timesteps) -> dict:
    base = epsilon_loss(true_epsilon, predicted_epsilon)
    timestep_values = [int(value) for value in _as_list(timesteps)]
    if len(timestep_values) != base["count"]:
        raise ValueError("timesteps must match epsilon length")
    weights = []
    for t in timestep_values:
        if t < 1 or t > int(schedule["timesteps"]):
            raise ValueError("timestep is out of range")
        idx = t - 1
        beta = float(schedule["betas"][idx])
        alpha = float(schedule["alphas"][idx])
        alpha_bar = float(schedule["alpha_bars"][idx])
        sigma_sq = float(schedule.get("posterior_variances", [0.0] * int(schedule["timesteps"]))[idx])
        if sigma_sq <= 0.0:
            sigma_sq = beta
        weights.append((beta * beta) / (2.0 * sigma_sq * alpha * (1.0 - alpha_bar)))
    weighted_errors = [weight * err for weight, err in zip(weights, base["squared_errors"])]
    base.update({"weights": weights, "weighted_mse": sum(weighted_errors) / len(weighted_errors), "weighted_errors": weighted_errors})
    return base


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--true", required=True, help="JSON scalar or list")
    parser.add_argument("--pred", required=True, help="JSON scalar or list")
    parser.add_argument("--schedule-json", default="")
    parser.add_argument("--timesteps", default="")
    args = parser.parse_args()
    if args.schedule_json:
        result = weighted_epsilon_loss(json.loads(args.true), json.loads(args.pred), json.loads(args.schedule_json), json.loads(args.timesteps))
    else:
        result = epsilon_loss(json.loads(args.true), json.loads(args.pred))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
