#!/usr/bin/env python3
import argparse
import json
import random


def subset_size_for_alpha(d, alpha):
    if d <= 0:
        raise ValueError("d must be positive")
    if not (0 < alpha <= 1):
        raise ValueError("alpha must be in (0, 1]")
    return max(1, int(round(alpha * d)))


def generate_alpha_subsets(d, alpha, num_subsets, seed):
    if num_subsets <= 0:
        raise ValueError("num_subsets must be positive")
    subset_size = subset_size_for_alpha(d, alpha)
    rng = random.Random(seed)
    matrix = []
    for _ in range(num_subsets):
        chosen = set(rng.sample(range(d), subset_size))
        matrix.append([1 if index in chosen else 0 for index in range(d)])
    metadata = {"d": d, "alpha": alpha, "subset_size": subset_size, "num_subsets": num_subsets, "seed": seed}
    validate_membership_matrix(matrix, d, subset_size)
    return {"matrix": matrix, "metadata": metadata}


def validate_membership_matrix(matrix, d, subset_size):
    if not matrix:
        raise ValueError("matrix must contain at least one row")
    for row in matrix:
        if len(row) != d:
            raise ValueError("row length does not match d")
        if any(value not in (0, 1) for value in row):
            raise ValueError("membership matrix must be binary")
        if sum(row) != subset_size:
            raise ValueError("row cardinality does not match subset_size")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--d", type=int, required=True)
    parser.add_argument("--alpha", type=float, required=True)
    parser.add_argument("--num-subsets", type=int, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = generate_alpha_subsets(args.d, args.alpha, args.num_subsets, args.seed)
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    else:
        print(text)


if __name__ == "__main__":
    main()
