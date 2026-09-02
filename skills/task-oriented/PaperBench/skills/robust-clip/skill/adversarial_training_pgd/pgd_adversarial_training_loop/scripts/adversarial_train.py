#!/usr/bin/env python3
import argparse
import json
import math
import os
import sys

ATTACK_SCRIPT_DIR = os.environ.get("LINF_PGD_SCRIPT_DIR")
if ATTACK_SCRIPT_DIR:
    sys.path.insert(0, ATTACK_SCRIPT_DIR)
else:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "linf_pgd_first_order_adversary", "scripts"))
from linf_pgd import LogisticModel, demo_data, pgd_attack


def clone_model(model):
    return LogisticModel(list(model.weights), model.bias)


def average_loss(model, examples, labels):
    return sum(model.loss(x, y) for x, y in zip(examples, labels)) / len(examples)


def parameter_gradients(model, examples, labels):
    grad_w = [0.0 for _ in model.weights]
    grad_b = 0.0
    for x, y in zip(examples, labels):
        error = model.probability(x) - y
        for i, xi in enumerate(x):
            grad_w[i] += error * xi
        grad_b += error
    scale = 1.0 / len(examples)
    return [g * scale for g in grad_w], grad_b * scale


def adversarial_examples(model, examples, labels, attack_config):
    result = pgd_attack(model, examples, labels, **attack_config)
    return result["adversarial_examples"], result


def train(model, examples, labels, attack_config=None, learning_rate=0.8, epochs=12):
    if attack_config is None:
        attack_config = {"epsilon": 0.18, "step_size": 0.06, "steps": 4, "restarts": 2, "seed": 11}
    trace = []
    params_before_all = {"weights": list(model.weights), "bias": model.bias}
    for epoch in range(epochs):
        epoch_attack_config = dict(attack_config)
        epoch_attack_config["seed"] = attack_config.get("seed", 0) + epoch
        adv_before, attack_before = adversarial_examples(model, examples, labels, epoch_attack_config)
        loss_before = average_loss(model, adv_before, labels)
        before = {"weights": list(model.weights), "bias": model.bias}
        grad_w, grad_b = parameter_gradients(model, adv_before, labels)
        model.weights = [w - learning_rate * g for w, g in zip(model.weights, grad_w)]
        model.bias -= learning_rate * grad_b
        adv_after, attack_after = adversarial_examples(model, examples, labels, epoch_attack_config)
        loss_after = average_loss(model, adv_after, labels)
        after = {"weights": list(model.weights), "bias": model.bias}
        trace.append({
            "epoch": epoch,
            "loss_before": loss_before,
            "loss_after": loss_after,
            "params_before": before,
            "params_after": after,
            "gradient": {"weights": grad_w, "bias": grad_b},
            "attack_before_best_losses": [item["best_loss"] for item in attack_before["trajectories"]],
            "attack_after_best_losses": [item["best_loss"] for item in attack_after["trajectories"]],
        })
    params_after_all = {"weights": list(model.weights), "bias": model.bias}
    return {
        "model": params_after_all,
        "training_trace": trace,
        "params_before": params_before_all,
        "params_after": params_after_all,
        "loss_before": trace[0]["loss_before"],
        "loss_after": trace[-1]["loss_after"],
        "mechanism_checks": {
            "pgd_adversarial_examples_generated": True,
            "outer_minimization_executed": True,
            "optimizer_step_executed": params_before_all != params_after_all,
            "reduced_training_executed": True,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    examples, labels = demo_data()
    model = LogisticModel([0.4, 0.4], -0.4)
    result = train(model, examples, labels)
    if args.self_test:
        assert result["mechanism_checks"]["optimizer_step_executed"]
        assert result["loss_after"] < result["loss_before"]
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
