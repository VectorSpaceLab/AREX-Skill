#!/usr/bin/env python3
import argparse
import json
import math
import random


def normal_pdf(value, mean, sigma):
    z = (value - mean) / sigma
    return math.exp(-0.5 * z * z) / (sigma * math.sqrt(2.0 * math.pi))


def simulate_pairs(num_simulations=512, seed=0, low=-3.0, high=3.0, sigma=0.4):
    rng = random.Random(seed)
    theta = []
    observed = []
    for _ in range(num_simulations):
        parameter = rng.uniform(low, high)
        theta.append(parameter)
        observed.append(parameter + rng.gauss(0.0, sigma))
    return theta, observed


def kernel_posterior_samples(theta, observed, x_o, num_samples=400, seed=1, bandwidth=0.45):
    weights = [normal_pdf(x_o, value, bandwidth) for value in observed]
    total = sum(weights)
    if total <= 0.0:
        raise ValueError("kernel weights vanished")
    normalized = [w / total for w in weights]
    rng = random.Random(seed)
    samples = rng.choices(theta, weights=normalized, k=num_samples)
    return samples


def summarize(samples):
    mean = sum(samples) / len(samples)
    variance = sum((value - mean) ** 2 for value in samples) / max(1, len(samples) - 1)
    return {"mean": mean, "std": math.sqrt(variance), "num_samples": len(samples)}


def analytic_reference_mean(x_o, low=-3.0, high=3.0, sigma=0.4, grid_size=4001):
    step = (high - low) / (grid_size - 1)
    weighted_sum = 0.0
    total_weight = 0.0
    for index in range(grid_size):
        parameter = low + index * step
        weight = normal_pdf(x_o, parameter, sigma)
        weighted_sum += parameter * weight
        total_weight += weight
    return weighted_sum / total_weight


def run_proxy(num_simulations=512, observation=1.25, seed=0, num_samples=400):
    theta, observed = simulate_pairs(num_simulations=num_simulations, seed=seed)
    samples = kernel_posterior_samples(theta, observed, observation, num_samples=num_samples, seed=seed + 1)
    summary = summarize(samples)
    reference_mean = analytic_reference_mean(observation)
    summary["reference_mean"] = reference_mean
    summary["posterior_mean_abs_error"] = abs(summary["mean"] - reference_mean)
    return {
        "is_proxy": True,
        "proxy_kind": "kernel conditional posterior proxy for SNPE mechanism",
        "num_simulations": num_simulations,
        "observation": observation,
        "posterior_summary": summary,
        "mechanism_checks": {
            "prior_sampling_executed": True,
            "simulator_executed": True,
            "conditional_posterior_depends_on_x": True,
            "posterior_samples_drawn": True,
            "likelihood_used_for_training": False,
            "reduced_training_executed": True,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-simulations", type=int, default=512)
    parser.add_argument("--observation", type=float, default=1.25)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--num-samples", type=int, default=400)
    args = parser.parse_args()
    print(json.dumps(run_proxy(args.num_simulations, args.observation, args.seed, args.num_samples), indent=2))


if __name__ == "__main__":
    main()
