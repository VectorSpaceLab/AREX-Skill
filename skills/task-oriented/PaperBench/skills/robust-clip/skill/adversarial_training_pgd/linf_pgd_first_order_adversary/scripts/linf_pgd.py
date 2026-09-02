#!/usr/bin/env python3
import argparse
import json
import math
import random


def sigmoid(value):
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


class LogisticModel:
    def __init__(self, weights, bias):
        self.weights = list(weights)
        self.bias = float(bias)

    def logit(self, x):
        return sum(w * xi for w, xi in zip(self.weights, x)) + self.bias

    def probability(self, x):
        return sigmoid(self.logit(x))

    def loss(self, x, y):
        p = min(max(self.probability(x), 1e-12), 1.0 - 1e-12)
        return -(y * math.log(p) + (1 - y) * math.log(1 - p))

    def input_gradient(self, x, y):
        error = self.probability(x) - y
        return [error * w for w in self.weights]


def sign(value):
    if value > 0:
        return 1.0
    if value < 0:
        return -1.0
    return 0.0


def project_linf(candidate, original, epsilon, clip_min=0.0, clip_max=1.0):
    projected = []
    for value, base in zip(candidate, original):
        low = max(clip_min, base - epsilon)
        high = min(clip_max, base + epsilon)
        projected.append(min(max(value, low), high))
    return projected


def linf_distance(a, b):
    return max(abs(x - y) for x, y in zip(a, b)) if a else 0.0


def pgd_attack(model, examples, labels, epsilon=0.25, step_size=0.1, steps=5, restarts=3, seed=0, clip_min=0.0, clip_max=1.0):
    rng = random.Random(seed)
    adversarial = []
    trajectories = []
    diagnostics = []
    for index, (x, y) in enumerate(zip(examples, labels)):
        best_x = list(x)
        best_loss = model.loss(x, y)
        restart_logs = []
        for restart in range(restarts):
            current = [min(max(xi + rng.uniform(-epsilon, epsilon), clip_min), clip_max) for xi in x]
            current = project_linf(current, x, epsilon, clip_min, clip_max)
            losses = [model.loss(current, y)]
            for _ in range(steps):
                grad = model.input_gradient(current, y)
                current = [value + step_size * sign(g) for value, g in zip(current, grad)]
                current = project_linf(current, x, epsilon, clip_min, clip_max)
                losses.append(model.loss(current, y))
            final_loss = losses[-1]
            if final_loss > best_loss:
                best_loss = final_loss
                best_x = list(current)
            restart_logs.append({"restart": restart, "losses": losses, "final_loss": final_loss})
        adversarial.append(best_x)
        trajectories.append({"example_index": index, "natural_loss": model.loss(x, y), "best_loss": best_loss, "restarts": restart_logs})
        diagnostics.append({
            "example_index": index,
            "max_linf_perturbation": linf_distance(best_x, x),
            "within_epsilon": linf_distance(best_x, x) <= epsilon + 1e-12,
            "within_clip": all(clip_min - 1e-12 <= value <= clip_max + 1e-12 for value in best_x),
        })
    return {"adversarial_examples": adversarial, "trajectories": trajectories, "diagnostics": diagnostics}


def demo_data():
    return [[0.2, 0.25], [0.25, 0.2], [0.75, 0.8], [0.8, 0.75]], [0, 0, 1, 1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    model = LogisticModel([3.0, 3.0], -3.0)
    examples, labels = demo_data()
    result = pgd_attack(model, examples, labels)
    if args.self_test:
        assert all(item["within_epsilon"] for item in result["diagnostics"])
        assert all(item["within_clip"] for item in result["diagnostics"])
        assert all(item["best_loss"] >= item["natural_loss"] for item in result["trajectories"])
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
