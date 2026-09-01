#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def quadratic_loss_and_grad(vector, target):
    diff = [value - goal for value, goal in zip(vector, target)]
    loss = sum(item * item for item in diff) / max(1, len(diff))
    grad = [2.0 * item / max(1, len(diff)) for item in diff]
    return loss, grad


def project_linf(vector, base, epsilon):
    if epsilon is None:
        return list(vector)
    projected = []
    for value, center in zip(vector, base):
        low = center - epsilon
        high = center + epsilon
        projected.append(min(high, max(low, value)))
    return projected


def optimize_visual_prompt(initial, target, steps=20, step_size=0.2, epsilon=None, value_bounds=None):
    if len(initial) != len(target):
        raise ValueError("initial and target must have the same length")
    vector = [float(value) for value in initial]
    base = list(vector)
    target = [float(value) for value in target]
    losses = []
    for _ in range(int(steps) + 1):
        loss, grad = quadratic_loss_and_grad(vector, target)
        losses.append(loss)
        if len(losses) == int(steps) + 1:
            break
        vector = [value - step_size * g for value, g in zip(vector, grad)]
        vector = project_linf(vector, base, epsilon)
        if value_bounds is not None:
            low, high = value_bounds
            vector = [min(high, max(low, value)) for value in vector]
    max_linf = max(abs(value - center) for value, center in zip(vector, base)) if vector else 0.0
    return {
        "params_before": base,
        "params_after": vector,
        "parameters_before": base,
        "parameters_after": vector,
        "loss_before": losses[0],
        "loss_after": losses[-1],
        "losses": losses,
        "optimizer_state_changed": vector != base,
        "constraint": {"epsilon": epsilon, "max_linf_delta": max_linf, "within_linf": epsilon is None or max_linf <= epsilon + 1e-9},
    }


def _self_test():
    result = optimize_visual_prompt([0.0, 0.0], [1.0, -1.0], steps=10, step_size=0.5, epsilon=0.25)
    assert result["loss_after"] < result["loss_before"]
    assert result["params_before"] != result["params_after"]
    assert result["constraint"]["within_linf"] is True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="JSON with initial, target, steps, step_size, epsilon")
    parser.add_argument("--output", help="Output trace JSON")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print(json.dumps({"ok": True}))
        return 0
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = optimize_visual_prompt(
        data["initial"],
        data["target"],
        steps=data.get("steps", 20),
        step_size=data.get("step_size", 0.2),
        epsilon=data.get("epsilon"),
        value_bounds=data.get("value_bounds"),
    )
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "loss_before": result["loss_before"], "loss_after": result["loss_after"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
