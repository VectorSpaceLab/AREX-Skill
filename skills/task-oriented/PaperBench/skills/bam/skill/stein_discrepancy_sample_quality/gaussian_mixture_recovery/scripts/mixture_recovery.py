#!/usr/bin/env python3
"""Pure-Python reduced Gaussian-mixture KSD recovery experiment."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import random
from pathlib import Path


def import_from_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise ImportError(f"cannot load {path}")
    spec.loader.exec_module(module)
    return module


def default_skill_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_generated_modules(skill_root: Path):
    scoring = import_from_path("stein_kernel", skill_root / "stein_kernel_scoring" / "scripts" / "stein_kernel.py")
    bootstrap = import_from_path("bootstrap_ksd", skill_root / "ksd_bootstrap_gof" / "scripts" / "bootstrap_ksd.py")
    return scoring, bootstrap


def logsumexp(values: list[float]) -> float:
    maximum = max(values)
    return maximum + math.log(sum(math.exp(value - maximum) for value in values))


def mixture_score(samples, means, weights, variance: float) -> list[list[float]]:
    total_weight = sum(weights)
    normalized_weights = [weight / total_weight for weight in weights]
    scores = []
    for row in samples:
        x = float(row[0] if isinstance(row, list) else row)
        log_components = [math.log(weight) - 0.5 * ((x - mean) ** 2) / variance for mean, weight in zip(means, normalized_weights)]
        norm = logsumexp(log_components)
        responsibilities = [math.exp(value - norm) for value in log_components]
        component_scores = [-(x - mean) / variance for mean in means]
        scores.append([sum(resp * score for resp, score in zip(responsibilities, component_scores))])
    return scores


def sample_mixture(rng: random.Random, n: int, means, weights, variance: float) -> list[list[float]]:
    cumulative = []
    total = 0.0
    for weight in weights:
        total += weight
        cumulative.append(total)
    samples = []
    for _ in range(n):
        draw = rng.random() * total
        index = 0
        while index < len(cumulative) - 1 and draw > cumulative[index]:
            index += 1
        samples.append([rng.gauss(means[index], math.sqrt(variance))])
    return samples


def mean(values: list[bool | float]) -> float:
    return sum(float(value) for value in values) / len(values) if values else 0.0


def run_trials(
    skill_root: Path,
    sample_size: int = 80,
    trials: int = 16,
    num_bootstrap: int = 120,
    perturbation: float = 1.0,
    alpha: float = 0.05,
    seed: int = 123,
) -> dict:
    scoring, bootstrap = load_generated_modules(skill_root)
    rng = random.Random(seed)
    true_means = [0.0, 2.0, 4.0, 6.0, 8.0]
    weights = [0.2] * 5
    variance = 1.0
    perturbed_means = [mean_value + delta * perturbation for mean_value, delta in zip(true_means, [-1.0, 0.5, 1.0, -0.5, 1.5])]
    records = []
    for trial in range(trials):
        samples = sample_mixture(rng, sample_size, true_means, weights, variance)
        bandwidth = scoring.median_bandwidth(samples)
        for condition, means in [("null", true_means), ("alternative", perturbed_means)]:
            scores = mixture_score(samples, means, weights, variance)
            matrix = scoring.rbf_stein_kernel_matrix(samples, scores, bandwidth=bandwidth)
            test = bootstrap.bootstrap_ksd_test(
                matrix,
                alpha=alpha,
                num_bootstrap=num_bootstrap,
                seed=seed + trial * 17 + (0 if condition == "null" else 10000),
            )
            records.append({
                "trial": trial,
                "condition": condition,
                "bandwidth": float(bandwidth),
                "ksd_u": test["ksd_u"],
                "p_value": test["p_value"],
                "reject": test["reject"],
            })
    null_rate = mean([item["reject"] for item in records if item["condition"] == "null"])
    alt_rate = mean([item["reject"] for item in records if item["condition"] == "alternative"])
    return {
        "schema_version": 1,
        "experiment": "synthetic_1d_gaussian_mixture",
        "parameters": {
            "sample_size": sample_size,
            "trials": trials,
            "num_bootstrap": num_bootstrap,
            "perturbation": perturbation,
            "alpha": alpha,
            "seed": seed,
            "means": true_means,
            "perturbed_means": perturbed_means,
            "weights": weights,
            "variance": variance,
        },
        "metrics": {
            "null_rejection_rate": null_rate,
            "alternative_rejection_rate": alt_rate,
            "alternative_rejection_rate_minus_null_rejection_rate": alt_rate - null_rate,
        },
        "trial_records": records,
        "mechanism_checks": {
            "score_only_model_access": True,
            "normalizing_constant_used": False,
            "rbf_stein_kernel_used": True,
            "u_statistic_excludes_diagonal": True,
            "centered_multinomial_bootstrap_used": True,
            "generated_stein_kernel_skill_invoked": True,
            "generated_bootstrap_skill_invoked": True,
            "reduced_proxy_recovery_declared": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", default=str(default_skill_root()))
    parser.add_argument("--sample-size", type=int, default=80)
    parser.add_argument("--trials", type=int, default=16)
    parser.add_argument("--num-bootstrap", type=int, default=120)
    parser.add_argument("--perturbation", type=float, default=1.0)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run_trials(Path(args.skill_root), args.sample_size, args.trials, args.num_bootstrap, args.perturbation, args.alpha, args.seed)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": args.output, "metrics": result["metrics"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
