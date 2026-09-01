#!/usr/bin/env python3
import argparse
import json
import math
import random


def _as_list(value):
    if isinstance(value, (int, float)):
        return [float(value)]
    return [float(item) for item in value]


def accumulated_variances(t, beta=1.0):
    if not 0.0 <= t <= 1.0:
        raise ValueError("t must be in [0, 1]")
    if beta <= 0.0:
        raise ValueError("beta must be positive")
    return beta * t, beta * (1.0 - t)


def posterior_stats(x0, x1, t, beta=1.0):
    clean = _as_list(x0)
    degraded = _as_list(x1)
    if len(clean) != len(degraded):
        raise ValueError("x0 and x1 must have the same length")
    sigma2_t, barsigma2_t = accumulated_variances(float(t), float(beta))
    denominator = sigma2_t + barsigma2_t
    if denominator <= 0.0:
        raise ValueError("variance denominator must be positive")
    weight_clean = barsigma2_t / denominator
    weight_degraded = sigma2_t / denominator
    mean = [weight_clean * a + weight_degraded * b for a, b in zip(clean, degraded)]
    variance = sigma2_t * barsigma2_t / denominator
    return {
        "sigma2_t": sigma2_t,
        "barsigma2_t": barsigma2_t,
        "mean": mean,
        "variance": variance,
        "weight_clean": weight_clean,
        "weight_degraded": weight_degraded,
    }


def sample_xt(x0, x1, t, beta=1.0, seed=0, noise=None):
    stats = posterior_stats(x0, x1, t, beta)
    if noise is None:
        rng = random.Random(seed)
        noise_values = [rng.gauss(0.0, 1.0) for _ in stats["mean"]]
    else:
        noise_values = _as_list(noise)
    if len(noise_values) != len(stats["mean"]):
        raise ValueError("noise length must match endpoint length")
    scale = math.sqrt(max(stats["variance"], 0.0))
    stats["sample"] = [mean + scale * eps for mean, eps in zip(stats["mean"], noise_values)]
    stats["noise"] = noise_values
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--x0", default="[0.0, 1.0]")
    parser.add_argument("--x1", default="[2.0, 3.0]")
    parser.add_argument("--t", type=float, default=0.5)
    parser.add_argument("--beta", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    x0 = json.loads(args.x0)
    x1 = json.loads(args.x1)
    print(json.dumps(sample_xt(x0, x1, args.t, args.beta, args.seed), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
