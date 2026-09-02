#!/usr/bin/env python3
"""Pure-Python helpers for a compact SBI benchmark task protocol."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from typing import Iterable


def as_vector(value: object, length: int, name: str) -> list[float]:
    if isinstance(value, (int, float)):
        return [float(value)] * length
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a number or list")
    result = [float(item) for item in value]
    if len(result) != length:
        raise ValueError(f"{name} length {len(result)} does not match expected {length}")
    return result


def validate_dimension(value: int, name: str) -> int:
    value = int(value)
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def normalize_task(
    task_name: str,
    dim_parameters: int,
    dim_data: int,
    prior_mean: Iterable[float],
    prior_variance: float,
    simulator_variance: float,
    observation: Iterable[float],
    num_simulations: int,
) -> dict:
    dim_parameters = validate_dimension(dim_parameters, "dim_parameters")
    dim_data = validate_dimension(dim_data, "dim_data")
    if dim_parameters != dim_data:
        raise ValueError("gaussian_linear helper requires dim_parameters == dim_data")
    prior_mean = [float(item) for item in prior_mean]
    observation = [float(item) for item in observation]
    if len(prior_mean) != dim_parameters:
        raise ValueError("prior_mean length does not match dim_parameters")
    if len(observation) != dim_data:
        raise ValueError("observation length does not match dim_data")
    prior_variance = float(prior_variance)
    simulator_variance = float(simulator_variance)
    if prior_variance <= 0.0 or simulator_variance <= 0.0:
        raise ValueError("variances must be positive")
    num_simulations = int(num_simulations)
    if num_simulations <= 0:
        raise ValueError("num_simulations must be positive")
    return {
        "schema_version": 1,
        "task_name": task_name,
        "task_family": "gaussian_linear",
        "dim_parameters": dim_parameters,
        "dim_data": dim_data,
        "prior": {
            "distribution": "diagonal_gaussian",
            "mean": prior_mean,
            "variance": prior_variance,
        },
        "simulator": {
            "distribution": "gaussian_linear",
            "noise_variance": simulator_variance,
        },
        "observation": observation,
        "num_simulations": num_simulations,
    }


def sample_diagonal_gaussian(rng: random.Random, mean: list[float], variance: float) -> list[float]:
    std = math.sqrt(variance)
    return [rng.gauss(mu, std) for mu in mean]


def simulate(task: dict, seed: int, num_samples: int) -> dict:
    rng = random.Random(seed)
    num_samples = int(num_samples)
    if num_samples <= 0:
        raise ValueError("num_samples must be positive")
    mean = task["prior"]["mean"]
    prior_variance = float(task["prior"]["variance"])
    simulator_variance = float(task["simulator"]["noise_variance"])
    noise_std = math.sqrt(simulator_variance)
    theta_samples = []
    observation_samples = []
    for _ in range(num_samples):
        theta = sample_diagonal_gaussian(rng, mean, prior_variance)
        x = [value + rng.gauss(0.0, noise_std) for value in theta]
        theta_samples.append(theta)
        observation_samples.append(x)
    return {
        "schema_version": 1,
        "seed": int(seed),
        "num_samples": num_samples,
        "theta": theta_samples,
        "x": observation_samples,
    }


def gaussian_linear_reference_posterior(task: dict) -> dict:
    prior_mean = [float(item) for item in task["prior"]["mean"]]
    prior_variance = float(task["prior"]["variance"])
    simulator_variance = float(task["simulator"]["noise_variance"])
    observation = [float(item) for item in task["observation"]]
    posterior_variance = 1.0 / (1.0 / prior_variance + 1.0 / simulator_variance)
    posterior_mean = [
        posterior_variance * (obs / simulator_variance + mu / prior_variance)
        for obs, mu in zip(observation, prior_mean)
    ]
    return {
        "schema_version": 1,
        "distribution": "diagonal_gaussian",
        "mean": posterior_mean,
        "variance": posterior_variance,
    }


def sample_reference(task: dict, seed: int, num_samples: int) -> dict:
    posterior = gaussian_linear_reference_posterior(task)
    rng = random.Random(seed)
    samples = [
        sample_diagonal_gaussian(rng, posterior["mean"], posterior["variance"])
        for _ in range(int(num_samples))
    ]
    return {
        "schema_version": 1,
        "seed": int(seed),
        "num_samples": int(num_samples),
        "posterior": posterior,
        "samples": samples,
    }


def read_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str, data: dict) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def self_test() -> dict:
    task = normalize_task(
        task_name="gaussian_linear_proxy",
        dim_parameters=1,
        dim_data=1,
        prior_mean=[0.0],
        prior_variance=1.0,
        simulator_variance=0.25,
        observation=[0.4],
        num_simulations=8,
    )
    posterior = gaussian_linear_reference_posterior(task)
    simulations = simulate(task, seed=3, num_samples=5)
    reference = sample_reference(task, seed=4, num_samples=6)
    ok = (
        posterior["variance"] < task["prior"]["variance"]
        and len(simulations["theta"]) == 5
        and len(reference["samples"]) == 6
    )
    return {"ok": ok, "posterior": posterior, "simulation_count": len(simulations["theta"])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    normalize = sub.add_parser("normalize-task")
    normalize.add_argument("--task-name", required=True)
    normalize.add_argument("--dim-parameters", type=int, required=True)
    normalize.add_argument("--dim-data", type=int, required=True)
    normalize.add_argument("--prior-mean", required=True)
    normalize.add_argument("--prior-variance", type=float, required=True)
    normalize.add_argument("--simulator-variance", type=float, required=True)
    normalize.add_argument("--observation", required=True)
    normalize.add_argument("--num-simulations", type=int, required=True)
    normalize.add_argument("--output", required=True)

    simulate_cmd = sub.add_parser("simulate")
    simulate_cmd.add_argument("--task-json", required=True)
    simulate_cmd.add_argument("--seed", type=int, default=0)
    simulate_cmd.add_argument("--num-samples", type=int, required=True)
    simulate_cmd.add_argument("--output", required=True)

    posterior_cmd = sub.add_parser("posterior")
    posterior_cmd.add_argument("--task-json", required=True)
    posterior_cmd.add_argument("--output", required=True)

    sample_cmd = sub.add_parser("sample-reference")
    sample_cmd.add_argument("--task-json", required=True)
    sample_cmd.add_argument("--seed", type=int, default=0)
    sample_cmd.add_argument("--num-samples", type=int, required=True)
    sample_cmd.add_argument("--output", required=True)

    sub.add_parser("self-test")
    args = parser.parse_args()

    if args.command == "normalize-task":
        task = normalize_task(
            args.task_name,
            args.dim_parameters,
            args.dim_data,
            as_vector(args.prior_mean, args.dim_parameters, "prior_mean"),
            args.prior_variance,
            args.simulator_variance,
            as_vector(args.observation, args.dim_data, "observation"),
            args.num_simulations,
        )
        write_json(args.output, task)
    elif args.command == "simulate":
        write_json(args.output, simulate(read_json(args.task_json), args.seed, args.num_samples))
    elif args.command == "posterior":
        write_json(args.output, gaussian_linear_reference_posterior(read_json(args.task_json)))
    elif args.command == "sample-reference":
        write_json(args.output, sample_reference(read_json(args.task_json), args.seed, args.num_samples))
    elif args.command == "self-test":
        print(json.dumps(self_test(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
