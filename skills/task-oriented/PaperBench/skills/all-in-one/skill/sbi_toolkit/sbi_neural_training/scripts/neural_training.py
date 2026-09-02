#!/usr/bin/env python3
"""Reduced standard-library trainer for SBI-style posterior estimation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SUPPORTED_FAMILIES = {"SNPE", "SNLE", "SNRE"}


def _pairs(records: list[dict]) -> list[tuple[float, float]]:
    pairs: list[tuple[float, float]] = []
    for record in records:
        if record.get("status", "ok") != "ok":
            continue
        theta = record.get("theta")
        x = record.get("x")
        if not isinstance(theta, list) or not isinstance(x, list) or not theta or not x:
            continue
        pairs.append((float(x[0]), float(theta[0])))
    if not pairs:
        raise ValueError("at least one valid scalar theta/x pair is required")
    return pairs


def mse_loss(pairs: list[tuple[float, float]], a: float, b: float) -> float:
    total = 0.0
    for x_value, theta_value in pairs:
        prediction = a * x_value + b
        total += (prediction - theta_value) ** 2
    return total / float(len(pairs))


def train_conditional_gaussian_proxy(
    records: list[dict],
    *,
    family: str = "SNPE",
    learning_rate: float = 0.05,
    steps: int = 80,
    initial_a: float = 0.0,
    initial_b: float = 0.0,
    posterior_std: float = 0.75,
) -> dict:
    family = family.upper()
    if family not in SUPPORTED_FAMILIES:
        raise ValueError(f"unsupported SBI family: {family}")
    if steps <= 0:
        raise ValueError("steps must be positive")
    if learning_rate <= 0:
        raise ValueError("learning_rate must be positive")
    if posterior_std <= 0:
        raise ValueError("posterior_std must be positive")

    pairs = _pairs(records)
    a = float(initial_a)
    b = float(initial_b)
    params_before = {"a": a, "b": b, "posterior_std": float(posterior_std)}
    loss_before = mse_loss(pairs, a, b)
    loss_history = [loss_before]

    for _ in range(steps):
        grad_a = 0.0
        grad_b = 0.0
        for x_value, theta_value in pairs:
            error = (a * x_value + b) - theta_value
            grad_a += 2.0 * error * x_value / float(len(pairs))
            grad_b += 2.0 * error / float(len(pairs))
        a -= learning_rate * grad_a
        b -= learning_rate * grad_b
        loss_history.append(mse_loss(pairs, a, b))

    params_after = {"a": a, "b": b, "posterior_std": float(posterior_std)}
    loss_after = loss_history[-1]
    estimator = {
        "schema_version": 1,
        "family": family,
        "estimator_type": "reduced_conditional_gaussian_posterior",
        "a": a,
        "b": b,
        "posterior_std": float(posterior_std),
        "training_pair_count": len(pairs),
    }
    trace = {
        "schema_version": 1,
        "family": family,
        "loss_before": loss_before,
        "loss_after": loss_after,
        "loss_history": loss_history,
        "params_before": params_before,
        "params_after": params_after,
        "parameters_before": params_before,
        "parameters_after": params_after,
        "optimizer_state_changed": params_before != params_after,
        "steps": steps,
        "learning_rate": learning_rate,
    }
    return {"schema_version": 1, "estimator": estimator, "trace": trace}


def demo_records() -> list[dict]:
    return [
        {"theta": [-2.0], "x": [-1.8], "status": "ok"},
        {"theta": [-1.0], "x": [-0.9], "status": "ok"},
        {"theta": [0.0], "x": [0.1], "status": "ok"},
        {"theta": [1.0], "x": [1.1], "status": "ok"},
        {"theta": [2.0], "x": [1.9], "status": "ok"},
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Run a built-in deterministic training demo.")
    parser.add_argument("--records", default="", help="Optional JSON file containing records or valid_records.")
    parser.add_argument("--output", default="", help="Optional output JSON path.")
    parser.add_argument("--family", default="SNPE", help="SBI family label.")
    parser.add_argument("--steps", type=int, default=80)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    args = parser.parse_args()

    if args.records:
        data = json.loads(Path(args.records).read_text(encoding="utf-8"))
        records = data.get("valid_records", data.get("records", data))
    elif args.demo:
        records = demo_records()
    else:
        parser.error("provide --demo or --records")

    result = train_conditional_gaussian_proxy(
        records,
        family=args.family,
        learning_rate=args.learning_rate,
        steps=args.steps,
    )
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        path = Path(args.output).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
