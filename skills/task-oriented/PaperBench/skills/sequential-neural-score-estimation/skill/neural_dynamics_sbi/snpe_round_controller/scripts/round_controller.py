#!/usr/bin/env python3
import random


def sample_uniform(prior_bounds, rng):
    return [rng.uniform(low, high) for low, high in prior_bounds]


def sample_clipped_gaussian(center, scales, prior_bounds, rng):
    values = []
    for mean, scale, (low, high) in zip(center, scales, prior_bounds):
        value = rng.gauss(mean, scale)
        values.append(max(low, min(high, value)))
    return values


def run_rounds(prior_bounds, observed_summary, simulate_summary, infer_posterior, rounds=2, simulations_per_round=32, seed=0, shrink=0.5):
    rng = random.Random(seed)
    summaries = []
    parameters = []
    round_logs = []
    prior_scales = [(high - low) / 2.0 for low, high in prior_bounds]
    center = [(low + high) / 2.0 for low, high in prior_bounds]
    scales = list(prior_scales)
    posterior = None
    for round_index in range(rounds):
        proposal = "prior" if round_index == 0 else "posterior_guided"
        for _ in range(simulations_per_round):
            if round_index == 0:
                theta = sample_uniform(prior_bounds, rng)
            else:
                theta = sample_clipped_gaussian(center, scales, prior_bounds, rng)
            parameters.append(theta)
            summaries.append(simulate_summary(theta, rng))
        posterior = infer_posterior(summaries, parameters, observed_summary)
        center = posterior["posterior_mean"]
        scales = [max(scale * shrink, 1e-6) for scale in scales]
        round_logs.append({"round": round_index + 1, "proposal": proposal, "simulation_count": simulations_per_round, "proposal_center": center, "proposal_scale": list(scales)})
    return {
        "summaries": summaries,
        "parameters": parameters,
        "round_logs": round_logs,
        "posterior": posterior,
        "mechanism_flags": {
            "prior_simulations_executed": True,
            "posterior_guided_round_executed": rounds > 1,
            "proposal_narrowed": rounds > 1 and round_logs[-1]["proposal_scale"][0] < prior_scales[0],
            "likelihood_evaluated": False,
        },
    }
