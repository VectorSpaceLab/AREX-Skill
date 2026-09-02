#!/usr/bin/env python3
import argparse
import json
import math


def _as_floats(values, name):
    if not isinstance(values, list) or not values:
        raise ValueError(f"{name} must be a non-empty list")
    out = [float(value) for value in values]
    if not all(math.isfinite(value) for value in out):
        raise ValueError(f"{name} contains non-finite values")
    return out


def compute_clipped_surrogate(old_log_probs, new_log_probs, advantages, clip_epsilon=0.2):
    old_log_probs = _as_floats(old_log_probs, "old_log_probs")
    new_log_probs = _as_floats(new_log_probs, "new_log_probs")
    advantages = _as_floats(advantages, "advantages")
    if not (len(old_log_probs) == len(new_log_probs) == len(advantages)):
        raise ValueError("old_log_probs, new_log_probs, and advantages must have equal length")
    clip_epsilon = float(clip_epsilon)
    if not math.isfinite(clip_epsilon) or clip_epsilon <= 0:
        raise ValueError("clip_epsilon must be positive and finite")

    ratios = [math.exp(new - old) for old, new in zip(old_log_probs, new_log_probs)]
    lower = 1.0 - clip_epsilon
    upper = 1.0 + clip_epsilon
    clipped_ratios = [min(max(ratio, lower), upper) for ratio in ratios]
    unclipped = [ratio * advantage for ratio, advantage in zip(ratios, advantages)]
    clipped = [ratio * advantage for ratio, advantage in zip(clipped_ratios, advantages)]
    objective_terms = [min(raw, bounded) for raw, bounded in zip(unclipped, clipped)]
    mean_objective = sum(objective_terms) / len(objective_terms)
    approx_kl = sum(old - new for old, new in zip(old_log_probs, new_log_probs)) / len(old_log_probs)
    clipped_flags = [abs(ratio - 1.0) > clip_epsilon for ratio in ratios]
    return {
        "ratios": ratios,
        "clipped_ratios": clipped_ratios,
        "unclipped": unclipped,
        "clipped": clipped,
        "objective_terms": objective_terms,
        "mean_objective": mean_objective,
        "loss": -mean_objective,
        "clip_fraction": sum(1 for flag in clipped_flags if flag) / len(clipped_flags),
        "approx_kl": approx_kl,
        "sample_count": len(old_log_probs),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-log-probs", required=True)
    parser.add_argument("--new-log-probs", required=True)
    parser.add_argument("--advantages", required=True)
    parser.add_argument("--clip-epsilon", type=float, default=0.2)
    args = parser.parse_args()
    result = compute_clipped_surrogate(
        json.loads(args.old_log_probs),
        json.loads(args.new_log_probs),
        json.loads(args.advantages),
        args.clip_epsilon,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
