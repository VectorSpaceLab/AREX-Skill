#!/usr/bin/env python3
"""Deterministic Tent-style entropy adaptation for a tiny two-class proxy."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def entropy_from_margin(margin: float) -> float:
    p = sigmoid(margin)
    q = 1.0 - p
    return -(p * math.log(max(p, 1e-12)) + q * math.log(max(q, 1e-12)))


def mean_entropy(features: list[float], scale: float, bias: float) -> float:
    return sum(entropy_from_margin(scale * feature + bias) for feature in features) / len(features)


def accuracy(features: list[float], labels: list[int], scale: float, bias: float) -> float:
    correct = 0
    for feature, label in zip(features, labels):
        pred = 1 if scale * feature + bias >= 0.0 else 0
        correct += int(pred == label)
    return correct / len(labels)


def entropy_gradients(features: list[float], scale: float, bias: float) -> tuple[float, float]:
    grad_scale = 0.0
    grad_bias = 0.0
    for feature in features:
        margin = scale * feature + bias
        p = sigmoid(margin)
        # dH/dmargin for binary softmax margin is -margin * p * (1-p).
        grad_margin = -margin * p * (1.0 - p)
        grad_scale += grad_margin * feature
        grad_bias += grad_margin
    count = float(len(features))
    return grad_scale / count, grad_bias / count


def run_tent_proxy(features: list[float], labels: list[int] | None = None, scale: float = 0.25, bias: float = 0.0, lr: float = 1.0, steps: int = 1) -> dict:
    params_before = {"scale": scale, "bias": bias}
    loss_before = mean_entropy(features, scale, bias)
    acc_before = accuracy(features, labels, scale, bias) if labels is not None else None
    step_logs = []
    for step in range(steps):
        grad_scale, grad_bias = entropy_gradients(features, scale, bias)
        scale -= lr * grad_scale
        bias -= lr * grad_bias
        step_logs.append({"step": step + 1, "grad_scale": grad_scale, "grad_bias": grad_bias, "scale": scale, "bias": bias})
    loss_after = mean_entropy(features, scale, bias)
    acc_after = accuracy(features, labels, scale, bias) if labels is not None else None
    return {
        "loss_before": loss_before,
        "loss_after": loss_after,
        "params_before": params_before,
        "params_after": {"scale": scale, "bias": bias},
        "parameters_before": params_before,
        "parameters_after": {"scale": scale, "bias": bias},
        "optimizer_state_changed": params_before != {"scale": scale, "bias": bias},
        "steps": step_logs,
        "accuracy_before": acc_before,
        "accuracy_after": acc_after,
    }


def self_test() -> None:
    features = [-2.0, -1.5, 1.5, 2.0]
    labels = [0, 0, 1, 1]
    trace = run_tent_proxy(features, labels, lr=1.0, steps=3)
    assert trace["loss_after"] < trace["loss_before"]
    assert trace["params_after"] != trace["params_before"]
    assert trace["accuracy_after"] >= trace["accuracy_before"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", help="JSON with features, optional labels, lr, steps, scale, and bias.")
    parser.add_argument("--output", default="")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print(json.dumps({"ok": True, "self_test": True}))
        return 0
    payload = json.loads(Path(args.input).read_text(encoding="utf-8")) if args.input else {}
    trace = run_tent_proxy(
        payload.get("features", [-2.0, -1.5, 1.5, 2.0]),
        payload.get("labels"),
        scale=payload.get("scale", 0.25),
        bias=payload.get("bias", 0.0),
        lr=payload.get("lr", 1.0),
        steps=payload.get("steps", 3),
    )
    if args.output:
        Path(args.output).write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(trace, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
