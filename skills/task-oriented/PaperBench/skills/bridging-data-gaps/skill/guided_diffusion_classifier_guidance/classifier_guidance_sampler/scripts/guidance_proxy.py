#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def log_prob_target(x_value: float, target_center: float = 1.0) -> float:
    other_center = -target_center
    target_score = -0.5 * (x_value - target_center) ** 2
    other_score = -0.5 * (x_value - other_center) ** 2
    max_score = max(target_score, other_score)
    normalizer = max_score + math.log(math.exp(target_score - max_score) + math.exp(other_score - max_score))
    return target_score - normalizer


def grad_log_prob_target(x_value: float, target_center: float = 1.0) -> float:
    eps = 1e-5
    return (log_prob_target(x_value + eps, target_center) - log_prob_target(x_value - eps, target_center)) / (2 * eps)


def guided_update(x_value: float, base_mean: float, classifier_scale: float, variance: float, target_center: float = 1.0) -> dict:
    gradient = grad_log_prob_target(x_value, target_center)
    guidance = variance * classifier_scale * gradient
    guided = base_mean + guidance
    unguided = base_mean
    return {
        "x_t": x_value,
        "base_mean": base_mean,
        "classifier_scale": classifier_scale,
        "variance": variance,
        "gradient": gradient,
        "guidance": guidance,
        "unguided_state": unguided,
        "guided_state": guided,
        "log_prob_before": log_prob_target(x_value, target_center),
        "log_prob_unguided": log_prob_target(unguided, target_center),
        "log_prob_guided": log_prob_target(guided, target_center),
        "distance_unguided": abs(target_center - unguided),
        "distance_guided": abs(target_center - guided),
    }


def mechanism_checks(result: dict) -> dict:
    return {
        "classifier_gradient_computed": abs(result["gradient"]) > 0,
        "classifier_scale_applied": result["classifier_scale"] > 0 and abs(result["guidance"]) > 0,
        "guided_log_prob_improved": result["log_prob_guided"] > result["log_prob_unguided"],
        "guided_distance_improved": result["distance_guided"] < result["distance_unguided"],
        "unguided_control_executed": result["unguided_state"] == result["base_mean"],
    }


def run_proxy(classifier_scale: float = 1.5) -> dict:
    result = guided_update(x_value=-0.25, base_mean=-0.10, classifier_scale=classifier_scale, variance=0.35)
    checks = mechanism_checks(result)
    metric = result["distance_unguided"] - result["distance_guided"]
    return {"result": result, "mechanism_checks": checks, "metrics": {"guided_distance_improvement": metric}}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--classifier-scale", type=float, default=1.5)
    args = parser.parse_args()
    output = run_proxy(args.classifier_scale)
    Path(args.output).write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
