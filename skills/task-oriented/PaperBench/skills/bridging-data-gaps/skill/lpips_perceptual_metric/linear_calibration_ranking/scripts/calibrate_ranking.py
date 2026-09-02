#!/usr/bin/env python3
import argparse
import json
import math


def _sigmoid(value):
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def _validate_items(items):
    if not items:
        raise ValueError("items must be non-empty")
    layer_count = None
    for item in items:
        if item.get("judge") not in (0, 1):
            raise ValueError("judge must be 0 or 1")
        layers0 = item.get("layers0")
        layers1 = item.get("layers1")
        if not isinstance(layers0, list) or not isinstance(layers1, list) or len(layers0) != len(layers1) or not layers0:
            raise ValueError("layers0 and layers1 must be non-empty equal-length lists")
        if layer_count is None:
            layer_count = len(layers0)
        if len(layers0) != layer_count:
            raise ValueError("all items must have the same number of layers")
    return layer_count


def score_layers(layers, weights):
    return sum(float(layer) * float(weight) for layer, weight in zip(layers, weights))


def metrics(items, weights):
    loss = 0.0
    correct = 0
    records = []
    for item in items:
        score0 = score_layers(item["layers0"], weights)
        score1 = score_layers(item["layers1"], weights)
        margin = score0 - score1
        target = 1.0 if item["judge"] == 1 else 0.0
        prob_p1 = _sigmoid(margin)
        loss += -(target * math.log(prob_p1 + 1e-12) + (1.0 - target) * math.log(1.0 - prob_p1 + 1e-12))
        prediction = 1 if score1 < score0 else 0
        is_correct = prediction == item["judge"]
        correct += int(is_correct)
        records.append({"id": item.get("id", ""), "score0": score0, "score1": score1, "prediction": prediction, "judge": item["judge"], "correct": is_correct, "prob_p1": prob_p1})
    return {"loss": loss / len(items), "accuracy": correct / float(len(items)), "records": records}


def calibrate(items, initial_weights=None, steps=25, learning_rate=0.1):
    layer_count = _validate_items(items)
    if initial_weights is None:
        weights = [1.0] * layer_count
    else:
        if len(initial_weights) != layer_count:
            raise ValueError("initial_weights length mismatch")
        weights = [max(0.0, float(weight)) for weight in initial_weights]
    params_before = list(weights)
    before = metrics(items, weights)
    history = []
    for step in range(int(steps)):
        gradients = [0.0] * layer_count
        for item in items:
            diff = [float(a) - float(b) for a, b in zip(item["layers0"], item["layers1"])]
            margin = sum(weight * value for weight, value in zip(weights, diff))
            target = 1.0 if item["judge"] == 1 else 0.0
            error = _sigmoid(margin) - target
            for index, value in enumerate(diff):
                gradients[index] += error * value / len(items)
        for index in range(layer_count):
            weights[index] = max(0.0, weights[index] - learning_rate * gradients[index])
        if step in {0, int(steps) - 1}:
            current = metrics(items, weights)
            history.append({"step": step + 1, "loss": current["loss"], "accuracy": current["accuracy"], "weights": list(weights)})
    after = metrics(items, weights)
    return {"params_before": params_before, "params_after": list(weights), "before": before, "after": after, "history": history, "optimizer_step_executed": params_before != list(weights)}


def _self_test():
    items = [
        {"id": "a", "layers0": [0.1, 0.9], "layers1": [0.5, 0.2], "judge": 0},
        {"id": "b", "layers0": [0.7, 0.2], "layers1": [0.2, 0.8], "judge": 1},
        {"id": "c", "layers0": [0.2, 0.8], "layers1": [0.6, 0.1], "judge": 0},
    ]
    result = calibrate(items, initial_weights=[0.1, 1.0], steps=20, learning_rate=0.5)
    assert all(weight >= 0.0 for weight in result["params_after"])
    assert result["after"]["loss"] <= result["before"]["loss"]
    assert result["optimizer_step_executed"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="JSON object with items and optional initial_weights")
    parser.add_argument("--output")
    parser.add_argument("--steps", type=int, default=25)
    parser.add_argument("--learning-rate", type=float, default=0.1)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print(json.dumps({"ok": True}))
        return
    with open(args.input, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    result = calibrate(payload["items"], payload.get("initial_weights"), steps=args.steps, learning_rate=args.learning_rate)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
