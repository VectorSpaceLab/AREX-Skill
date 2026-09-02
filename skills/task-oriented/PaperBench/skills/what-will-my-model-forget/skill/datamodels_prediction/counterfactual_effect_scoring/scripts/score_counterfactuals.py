#!/usr/bin/env python3
import argparse
import json
import math


def pearson(xs, ys):
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denom_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denom_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if denom_x == 0 or denom_y == 0:
        return 0.0
    return numerator / (denom_x * denom_y)


def validate_removal_sets(weights, removal_sets):
    d = len(weights)
    for removal_set in removal_sets:
        seen = set()
        for index in removal_set:
            if not isinstance(index, int):
                raise ValueError("removal indices must be integers")
            if index < 0 or index >= d:
                raise ValueError("removal index out of range")
            if index in seen:
                raise ValueError("duplicate index in removal set")
            seen.add(index)


def score_removal_sets(weights, removal_sets, actual_effects=None):
    validate_removal_sets(weights, removal_sets)
    predicted = [sum(weights[index] for index in removal_set) for removal_set in removal_sets]
    result = {"predicted_effects": predicted, "ranked_indices_desc": rank_indices(weights, absolute=False), "ranked_indices_abs": rank_indices(weights, absolute=True)}
    if actual_effects is not None:
        if len(actual_effects) != len(predicted):
            raise ValueError("actual_effects length mismatch")
        result["effect_correlation"] = pearson(predicted, actual_effects)
    return result


def rank_indices(weights, absolute=False):
    return sorted(range(len(weights)), key=lambda index: abs(weights[index]) if absolute else weights[index], reverse=True)


def demo():
    weights = [0.5, -0.2, 0.9, 0.1]
    removal_sets = [[0, 2], [1], [], [2, 3]]
    actual = [1.42, -0.18, 0.0, 1.02]
    return score_removal_sets(weights, removal_sets, actual)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="JSON with weights, removal_sets, optional actual_effects")
    parser.add_argument("--output")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if args.demo:
        result = demo()
    else:
        with open(args.input, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        result = score_removal_sets(payload["weights"], payload["removal_sets"], payload.get("actual_effects"))
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    else:
        print(text)


if __name__ == "__main__":
    main()
