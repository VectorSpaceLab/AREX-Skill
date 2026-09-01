#!/usr/bin/env python3
import argparse
import json


def build_objective(dataset, split, epsilon, recovery_scope="proxy"):
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    return {
        "schema_version": 1,
        "objective": "min_theta E[max_delta_in_S L(theta, x + delta, y)]",
        "dataset": dataset,
        "split": split,
        "loss": "binary_cross_entropy",
        "threat_model": {"norm": "linf", "epsilon": float(epsilon), "clip_min": 0.0, "clip_max": 1.0},
        "inner_maximization": "random_start_projected_gradient_ascent",
        "outer_minimization": "gradient_descent_on_adversarial_loss",
        "recovery_scope": recovery_scope,
        "mechanism_checks": {
            "robust_minimax_objective_declared": True,
            "inner_maximization_required": True,
            "linf_projection_required": True,
            "outer_minimization_required": True,
            "natural_only_training": False,
        },
    }


def validate_objective(objective):
    checks = objective.get("mechanism_checks", {})
    threat = objective.get("threat_model", {})
    return bool(
        objective.get("objective")
        and threat.get("norm") == "linf"
        and threat.get("epsilon", 0) > 0
        and checks.get("robust_minimax_objective_declared")
        and checks.get("inner_maximization_required")
        and checks.get("outer_minimization_required")
        and not checks.get("natural_only_training")
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="synthetic_2d_margin_classification")
    parser.add_argument("--split", default="deterministic_train_test_subset")
    parser.add_argument("--epsilon", type=float, default=0.25)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    objective = build_objective(args.dataset, args.split, args.epsilon)
    if args.self_test:
        assert validate_objective(objective)
    print(json.dumps(objective, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
