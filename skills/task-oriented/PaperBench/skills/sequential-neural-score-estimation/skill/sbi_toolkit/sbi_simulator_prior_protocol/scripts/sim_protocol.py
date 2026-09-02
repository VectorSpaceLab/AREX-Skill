#!/usr/bin/env python3
import argparse
import json
import math
import random


def as_2d(values):
    rows = []
    for value in values:
        if isinstance(value, (list, tuple)):
            rows.append([float(v) for v in value])
        else:
            rows.append([float(value)])
    return rows


def gaussian_location_pairs(num_simulations=64, seed=0, low=-3.0, high=3.0, sigma=0.4):
    rng = random.Random(seed)
    theta = []
    observed = []
    failures = 0
    for _ in range(num_simulations):
        parameter = rng.uniform(low, high)
        noise = rng.gauss(0.0, sigma)
        simulation = parameter + noise
        if not (math.isfinite(parameter) and math.isfinite(simulation)):
            failures += 1
            continue
        theta.append([parameter])
        observed.append([simulation])
    return {
        "theta": theta,
        "x": observed,
        "metadata": {
            "num_requested": num_simulations,
            "num_accepted": len(theta),
            "theta_dim": 1,
            "x_dim": 1,
            "seed": seed,
            "failures": failures,
            "likelihood_evaluated": False,
        },
    }


def validate_pairs(payload):
    theta = payload["theta"]
    observed = payload["x"]
    if len(theta) != len(observed):
        raise ValueError("theta and x row counts differ")
    if not theta:
        raise ValueError("no accepted simulations")
    for row in theta + observed:
        if not isinstance(row, list) or not row:
            raise ValueError("all rows must be non-empty lists")
        if not all(math.isfinite(float(value)) for value in row):
            raise ValueError("non-finite value detected")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-simulations", type=int, default=64)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    payload = gaussian_location_pairs(args.num_simulations, args.seed)
    validate_pairs(payload)
    print(json.dumps({"ok": True, "metadata": payload["metadata"]}, indent=2))


if __name__ == "__main__":
    main()
