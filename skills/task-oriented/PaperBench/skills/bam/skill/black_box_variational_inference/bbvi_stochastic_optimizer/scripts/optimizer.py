#!/usr/bin/env python3
import argparse
import json
import math
from pathlib import Path


def _as_vector(values, name):
    if not isinstance(values, list) or not values:
        raise ValueError(f"{name} must be a non-empty list")
    vector = [float(value) for value in values]
    if any(not math.isfinite(value) for value in vector):
        raise ValueError(f"{name} contains non-finite value")
    return vector


def optimizer_step(params, gradient, method="adagrad", learning_rate=1.0, state=None, epsilon=1e-8):
    params_before = _as_vector(params, "params")
    grad = _as_vector(gradient, "gradient")
    if len(params_before) != len(grad):
        raise ValueError("params and gradient must have the same length")
    learning_rate = float(learning_rate)
    if learning_rate <= 0 or not math.isfinite(learning_rate):
        raise ValueError("learning_rate must be positive and finite")
    state_before = None if state is None else _as_vector(state, "state")
    if method == "scalar":
        step = [learning_rate * value for value in grad]
        state_after = state_before
    elif method == "adagrad":
        if state_before is None:
            state_before = [0.0 for _ in grad]
        if len(state_before) != len(grad):
            raise ValueError("state and gradient must have the same length")
        state_after = [accum + value * value for accum, value in zip(state_before, grad)]
        step = [
            learning_rate * value / math.sqrt(accum + epsilon)
            for value, accum in zip(grad, state_after)
        ]
    else:
        raise ValueError("method must be 'scalar' or 'adagrad'")
    params_after = [value + delta for value, delta in zip(params_before, step)]
    return {
        "method": method,
        "learning_rate": learning_rate,
        "params_before": params_before,
        "gradient": grad,
        "step": step,
        "params_after": params_after,
        "state_before": state_before,
        "state_after": state_after,
        "optimizer_step_executed": params_after != params_before,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = json.loads(Path(args.input_json).read_text())
    result = optimizer_step(
        payload["params"],
        payload["gradient"],
        payload.get("method", "adagrad"),
        payload.get("learning_rate", 1.0),
        payload.get("state"),
        payload.get("epsilon", 1e-8),
    )
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
