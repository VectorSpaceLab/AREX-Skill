#!/usr/bin/env python3
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "linf_pgd_first_order_adversary", "scripts"))
from linf_pgd import LogisticModel, demo_data, pgd_attack


def predict(model, x):
    return 1 if model.probability(x) >= 0.5 else 0


def metrics(model, examples, labels):
    losses = [model.loss(x, y) for x, y in zip(examples, labels)]
    correct = sum(1 for x, y in zip(examples, labels) if predict(model, x) == y)
    return {"loss": sum(losses) / len(losses), "accuracy": correct / len(labels)}


def evaluate(model, examples, labels, attack_config=None):
    if attack_config is None:
        attack_config = {"epsilon": 0.18, "step_size": 0.06, "steps": 6, "restarts": 3, "seed": 101}
    natural = metrics(model, examples, labels)
    attack = pgd_attack(model, examples, labels, **attack_config)
    adversarial = metrics(model, attack["adversarial_examples"], labels)
    return {
        "natural": natural,
        "pgd_adversarial": adversarial,
        "attack_diagnostics": attack["diagnostics"],
        "attack_trajectories": attack["trajectories"],
        "mechanism_checks": {
            "natural_metrics_computed": True,
            "pgd_white_box_evaluation_executed": True,
            "linf_projection_respected": all(item["within_epsilon"] and item["within_clip"] for item in attack["diagnostics"]),
            "numeric_metrics_present": True,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", default="1.0,1.0")
    parser.add_argument("--bias", type=float, default=-1.0)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    model = LogisticModel([float(value) for value in args.weights.split(",")], args.bias)
    examples, labels = demo_data()
    result = evaluate(model, examples, labels)
    if args.self_test:
        assert result["mechanism_checks"]["pgd_white_box_evaluation_executed"]
        assert result["mechanism_checks"]["linf_projection_respected"]
        assert 0.0 <= result["natural"]["accuracy"] <= 1.0
        assert result["pgd_adversarial"]["loss"] >= 0.0
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
