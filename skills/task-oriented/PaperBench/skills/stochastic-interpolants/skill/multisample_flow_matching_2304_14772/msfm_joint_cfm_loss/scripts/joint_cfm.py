#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def _vectors(values, name):
    if not isinstance(values, list) or not values:
        raise ValueError(f"{name} must be a non-empty list")
    dim = None
    result = []
    for row in values:
        if not isinstance(row, list) or not row:
            raise ValueError(f"{name} rows must be non-empty vectors")
        vector = [float(x) for x in row]
        if dim is None:
            dim = len(vector)
        elif len(vector) != dim:
            raise ValueError(f"{name} dimensions differ")
        result.append(vector)
    return result


def validate_pairs(source, target):
    source = _vectors(source, "source")
    target = _vectors(target, "target")
    if len(source) != len(target):
        raise ValueError("source and target must have equal pair count")
    if len(source[0]) != len(target[0]):
        raise ValueError("source and target dimensions differ")
    return source, target


def normalize_times(times, count):
    if isinstance(times, (int, float)):
        return [float(times)] * count
    if not isinstance(times, list) or len(times) != count:
        raise ValueError("times must be a scalar or one value per pair")
    normalized = [float(t) for t in times]
    if any(t < 0.0 or t > 1.0 for t in normalized):
        raise ValueError("times must be in [0, 1]")
    return normalized


def interpolate(source, target, times):
    source, target = validate_pairs(source, target)
    times = normalize_times(times, len(source))
    states = []
    velocities = []
    for x0, x1, time in zip(source, target, times):
        states.append([(1.0 - time) * a + time * b for a, b in zip(x0, x1)])
        velocities.append([b - a for a, b in zip(x0, x1)])
    return states, velocities


def mean_squared_loss(predictions, targets):
    predictions = _vectors(predictions, "predictions")
    targets = _vectors(targets, "targets")
    if len(predictions) != len(targets) or len(predictions[0]) != len(targets[0]):
        raise ValueError("prediction and target shapes differ")
    total = 0.0
    count = 0
    for prediction, target in zip(predictions, targets):
        for pred_value, target_value in zip(prediction, target):
            total += (pred_value - target_value) ** 2
            count += 1
    return total / count


def variance_proxy(velocities):
    velocities = _vectors(velocities, "velocities")
    dim = len(velocities[0])
    means = [sum(row[j] for row in velocities) / len(velocities) for j in range(dim)]
    return sum((row[j] - means[j]) ** 2 for row in velocities for j in range(dim)) / (len(velocities) * dim)


def predict_linear(states, params):
    states = _vectors(states, "states")
    weights = [float(x) for x in params["weights"]]
    bias = [float(x) for x in params["bias"]]
    if len(weights) != len(states[0]) or len(bias) != len(states[0]):
        raise ValueError("parameter dimensions differ from state dimension")
    return [[weights[j] * row[j] + bias[j] for j in range(len(row))] for row in states]


def gradient_step(states, targets, params, learning_rate):
    states = _vectors(states, "states")
    targets = _vectors(targets, "targets")
    before = {"weights": [float(x) for x in params["weights"]], "bias": [float(x) for x in params["bias"]]}
    predictions = predict_linear(states, before)
    n = len(states)
    dim = len(states[0])
    grad_w = [0.0] * dim
    grad_b = [0.0] * dim
    for state, prediction, target in zip(states, predictions, targets):
        for j in range(dim):
            grad = 2.0 * (prediction[j] - target[j]) / (n * dim)
            grad_w[j] += grad * state[j]
            grad_b[j] += grad
    after = {
        "weights": [before["weights"][j] - learning_rate * grad_w[j] for j in range(dim)],
        "bias": [before["bias"][j] - learning_rate * grad_b[j] for j in range(dim)],
    }
    return {
        "params_before": before,
        "params_after": after,
        "loss_before": mean_squared_loss(predictions, targets),
        "loss_after": mean_squared_loss(predict_linear(states, after), targets),
        "optimizer_step_executed": before != after,
    }


def evaluate(payload):
    states, targets = interpolate(payload["source"], payload["target"], payload.get("times", 0.5))
    result = {"interpolated_states": states, "target_velocities": targets, "variance_proxy": variance_proxy(targets)}
    if "predictions" in payload:
        result["loss"] = mean_squared_loss(payload["predictions"], targets)
    if "params" in payload:
        result["optimizer"] = gradient_step(states, targets, payload["params"], float(payload.get("learning_rate", 0.1)))
    return result


def _self_test():
    payload = {"source": [[0.0], [2.0]], "target": [[2.0], [4.0]], "times": [0.0, 1.0], "predictions": [[2.0], [2.0]], "params": {"weights": [0.0], "bias": [0.0]}, "learning_rate": 0.1}
    result = evaluate(payload)
    assert result["interpolated_states"] == [[0.0], [4.0]]
    assert result["target_velocities"] == [[2.0], [2.0]]
    assert result["loss"] == 0.0
    assert result["optimizer"]["optimizer_step_executed"] is True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input")
    parser.add_argument("--output")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print(json.dumps({"ok": True}))
        return
    result = evaluate(json.loads(Path(args.input).read_text()))
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2))
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
