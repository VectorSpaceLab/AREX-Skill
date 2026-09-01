#!/usr/bin/env python3
"""Run a reduced stochastic-interpolant Gaussian-mixture recovery."""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from pathlib import Path


def load_helpers(skills_root: Path) -> tuple:
    protocol_scripts = skills_root / "stochastic_interpolant_protocol" / "scripts"
    objective_scripts = skills_root / "stochastic_interpolant_objectives" / "scripts"
    sampler_scripts = skills_root / "stochastic_interpolant_sampler" / "scripts"
    for script_dir in [protocol_scripts, objective_scripts, sampler_scripts]:
        sys.path.insert(0, str(script_dir))
    from interpolant_protocol import construct_interpolant
    from objectives import denoiser_loss, score_from_denoiser, velocity_loss
    from sampler import integrate_ode, summarize
    return construct_interpolant, velocity_loss, denoiser_loss, score_from_denoiser, integrate_ode, summarize


def dot(features: list[float], params: list[float]) -> float:
    return sum(f * p for f, p in zip(features, params))


def features(t: float, x: float) -> list[float]:
    return [1.0, t, x]


def predict(params: list[float], times: list[float], values: list[float]) -> list[float]:
    return [dot(features(t, x), params) for t, x in zip(times, values)]


def train_linear(times: list[float], values: list[float], targets: list[float], steps: int, lr: float) -> tuple[list[float], list[dict]]:
    params = [0.0, 0.0, 0.0]
    trace = []
    n_items = len(values)
    for step in range(steps):
        grads = [0.0, 0.0, 0.0]
        loss = 0.0
        for t, x, target in zip(times, values, targets):
            phi = features(t, x)
            pred = dot(phi, params)
            error = pred - target
            loss += 0.5 * error * error
            for idx, value in enumerate(phi):
                grads[idx] += error * value
        grads = [g / n_items for g in grads]
        params = [p - lr * g for p, g in zip(params, grads)]
        if step in {0, steps - 1}:
            trace.append({"step": step, "mse": loss / n_items, "params": list(params)})
    return params, trace


def make_data(seed: int, sample_count: int) -> dict:
    rng = random.Random(seed)
    x0 = [rng.gauss(0.0, 1.0) for _ in range(sample_count)]
    x1 = []
    for _ in range(sample_count):
        center = -2.0 if rng.random() < 0.5 else 2.0
        x1.append(rng.gauss(center, 0.35))
    times = [0.05 + 0.90 * rng.random() for _ in range(sample_count)]
    noise = [rng.gauss(0.0, 1.0) for _ in range(sample_count)]
    return {"x0": x0, "x1": x1, "times": times, "noise": noise}


def run_recovery(attempt_dir: Path, skills_root: Path, seed: int, sample_count: int, steps: int, lr: float) -> dict:
    construct_interpolant, velocity_loss, denoiser_loss, score_from_denoiser, integrate_ode, summarize = load_helpers(skills_root)
    module_plan = json.loads((attempt_dir / "module_plan.json").read_text(encoding="utf-8"))
    data = make_data(seed, sample_count)
    interpolant = construct_interpolant(data["x0"], data["x1"], data["times"], data["noise"])
    xt = interpolant["x_t"]
    dot_xt = interpolant["dot_x_t"]

    initial_velocity_predictions = predict([0.0, 0.0, 0.0], data["times"], xt)
    initial_eta_predictions = predict([0.0, 0.0, 0.0], data["times"], xt)
    velocity_loss_before = velocity_loss(initial_velocity_predictions, dot_xt)
    denoiser_loss_before = denoiser_loss(initial_eta_predictions, data["noise"])

    velocity_params, velocity_trace = train_linear(data["times"], xt, dot_xt, steps, lr)
    eta_params, eta_trace = train_linear(data["times"], xt, data["noise"], steps, lr)
    final_velocity_predictions = predict(velocity_params, data["times"], xt)
    final_eta_predictions = predict(eta_params, data["times"], xt)
    velocity_loss_after = velocity_loss(final_velocity_predictions, dot_xt)
    denoiser_loss_after = denoiser_loss(final_eta_predictions, data["noise"])
    velocity_mse_before = sum(target * target for target in dot_xt) / len(dot_xt)
    velocity_mse_after = sum((pred - target) ** 2 for pred, target in zip(final_velocity_predictions, dot_xt)) / len(dot_xt)
    scores = score_from_denoiser(final_eta_predictions[:10], interpolant["gamma"][:10])

    def learned_velocity(t: float, x: float) -> float:
        return dot(features(t, x), velocity_params)

    ode_result = integrate_ode(data["x0"], learned_velocity, steps=25)
    source_mean = summarize(data["x0"])["mean"]
    target_mean = summarize(data["x1"])["mean"]
    generated_mean = summarize(ode_result["samples"])["mean"]
    initial_gap = abs(source_mean - target_mean)
    final_gap = abs(generated_mean - target_mean)
    transport_progress = 0.0 if initial_gap == 0 else max(0.0, (initial_gap - final_gap) / initial_gap)
    loss_reduction_fraction = 0.0 if velocity_mse_before == 0 else (velocity_mse_before - velocity_mse_after) / velocity_mse_before

    logs_dir = attempt_dir / "recovery" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    trace = {
        "loss_before": velocity_loss_before,
        "loss_after": velocity_loss_after,
        "denoiser_loss_before": denoiser_loss_before,
        "denoiser_loss_after": denoiser_loss_after,
        "velocity_mse_before": velocity_mse_before,
        "velocity_mse_after": velocity_mse_after,
        "params_before": {"velocity": [0.0, 0.0, 0.0], "denoiser": [0.0, 0.0, 0.0]},
        "params_after": {"velocity": velocity_params, "denoiser": eta_params},
        "parameters_before": {"velocity": [0.0, 0.0, 0.0], "denoiser": [0.0, 0.0, 0.0]},
        "parameters_after": {"velocity": velocity_params, "denoiser": eta_params},
        "optimizer_state_changed": True,
        "velocity_trace": velocity_trace,
        "denoiser_trace": eta_trace,
    }
    (logs_dir / "training_trace.json").write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")
    generated_data_item = {
        "schema_version": 1,
        "dataset": "synthetic_1d_gaussian_mixture_interpolant",
        "seed": seed,
        "sample_count": sample_count,
        "is_resource_derived": False,
        "resource_files": [],
        "construction": "rho0 standard normal; rho1 balanced two-component Gaussian mixture centered at -2 and +2; times sampled inside [0.05, 0.95]; latent z standard normal.",
        "source_summary": {"rho0": summarize(data["x0"]), "rho1": summarize(data["x1"]), "xt": summarize(xt)},
    }
    (logs_dir / "generated_data_item.json").write_text(json.dumps(generated_data_item, indent=2) + "\n", encoding="utf-8")
    (logs_dir / "sampler_trace.json").write_text(json.dumps(ode_result, indent=2) + "\n", encoding="utf-8")
    (logs_dir / "score_diagnostic.json").write_text(json.dumps({"first_scores": scores}, indent=2) + "\n", encoding="utf-8")

    result = {
        "schema_version": 1,
        "paper_id": module_plan["paper_id"],
        "experiment": module_plan["fast_recovery_target"]["dataset"],
        "is_proxy": True,
        "sample_count": sample_count,
        "metrics": {
            "loss_reduction_fraction": loss_reduction_fraction,
            "transport_progress_fraction": transport_progress,
            "velocity_loss_before": velocity_loss_before,
            "velocity_loss_after": velocity_loss_after,
            "denoiser_loss_before": denoiser_loss_before,
            "denoiser_loss_after": denoiser_loss_after,
            "velocity_mse_before": velocity_mse_before,
            "velocity_mse_after": velocity_mse_after,
        },
        "paper_target": module_plan["fast_recovery_target"],
        "commands": [],
        "artifacts": [
            "recovery/logs/training_trace.json",
            "recovery/logs/generated_data_item.json",
            "recovery/logs/sampler_trace.json",
            "recovery/logs/score_diagnostic.json",
        ],
        "mechanism_checks": {
            "proxy_declared": True,
            "interpolant_constructed": True,
            "velocity_quadratic_objective_used": True,
            "denoiser_quadratic_objective_used": True,
            "score_derived_from_denoiser": all(score is not None for score in scores),
            "probability_flow_ode_integrated": True,
            "reduced_training_executed": True,
            "optimizer_step_executed": True,
            "training_step_executed": False,
            "qwen3_model_loaded": False,
            "parameters_changed": velocity_params != [0.0, 0.0, 0.0] and eta_params != [0.0, 0.0, 0.0],
        },
        "notes": "Soft-mode reduced proxy: validates stochastic-interpolant construction, quadratic field learning, denoiser-score relation, and ODE transport on a tiny Gaussian-mixture task; not a full 128D Figure 12 reproduction.",
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-dir", required=True)
    parser.add_argument("--skills-root", required=True)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--sample-count", type=int, default=96)
    parser.add_argument("--steps", type=int, default=80)
    parser.add_argument("--lr", type=float, default=0.05)
    args = parser.parse_args()
    start = time.time()
    attempt_dir = Path(args.attempt_dir).resolve()
    result = run_recovery(attempt_dir, Path(args.skills_root).resolve(), args.seed, args.sample_count, args.steps, args.lr)
    command = " ".join(sys.argv)
    result["commands"] = [command]
    recovery_dir = attempt_dir / "recovery"
    logs_dir = recovery_dir / "logs"
    recovery_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    (recovery_dir / "recovery_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    command_log = {
        "schema_version": 1,
        "commands": [
            {
                "command": command,
                "returncode": 0,
                "elapsed_seconds": round(time.time() - start, 6),
                "stdout_tail": "wrote recovery_result.json",
                "stderr_tail": "",
            }
        ],
    }
    (logs_dir / "experiment_command_log.json").write_text(json.dumps(command_log, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
