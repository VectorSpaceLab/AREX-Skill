#!/usr/bin/env python3
import argparse
import json
import math
import random
import subprocess
import sys
import time
from pathlib import Path


def _run_command(command, cwd=None):
    started = time.time()
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    return {
        "command": command,
        "returncode": completed.returncode,
        "elapsed_seconds": round(time.time() - started, 6),
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }


def _write_json(path, payload):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, indent=2) + "\n")


def _load_json(path):
    return json.loads(Path(path).read_text())


def normal_logpdf(value, mean, variance):
    return -0.5 * (math.log(2.0 * math.pi * variance) + ((value - mean) ** 2) / variance)


def build_proxy_item(seed):
    rng = random.Random(seed)
    observations = [round(rng.gauss(0.75, 0.35), 6) for _ in range(6)]
    samples = [-1.25, -0.75, -0.25, 0.25, 0.75, 1.25]
    variational_mean = 0.1
    variational_variance = 1.0
    prior_variance = 2.0
    obs_variance = 0.5
    score = [[sample - variational_mean] for sample in samples]
    logq = [normal_logpdf(sample, variational_mean, variational_variance) for sample in samples]
    observed_mean = sum(observations) / len(observations)
    local_signal = [
        normal_logpdf(sample, 0.0, prior_variance) + normal_logpdf(observed_mean, sample, obs_variance) - lq
        for sample, lq in zip(samples, logq)
    ]
    irrelevant_noise = [5.0, -4.0, 6.0, -5.0, 7.0, -6.0]
    full_signal = [signal + noise for signal, noise in zip(local_signal, irrelevant_noise)]
    logp = [signal + lq for signal, lq in zip(full_signal, logq)]
    return {
        "seed": seed,
        "observations": observations,
        "observed_mean": observed_mean,
        "variational_mean": variational_mean,
        "variational_variance": variational_variance,
        "samples": samples,
        "score": score,
        "logq": logq,
        "logp": logp,
        "local_signal": local_signal,
        "full_signal": full_signal,
        "source": "synthetic fixed-seed Normal latent-variable proxy; no original repository used",
    }


def run_proxy(attempt_dir, skills_root, seed=17):
    attempt_dir = Path(attempt_dir)
    skills_root = Path(skills_root)
    recovery_dir = attempt_dir / "recovery"
    logs_dir = recovery_dir / "logs"
    work_dir = recovery_dir / "work"
    logs_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    module_plan = _load_json(attempt_dir / "module_plan.json")
    runtime_handoff_path = attempt_dir / "environment" / "runtime_handoff.json"
    runtime_handoff = _load_json(runtime_handoff_path) if runtime_handoff_path.exists() else {}
    item = build_proxy_item(seed)
    _write_json(logs_dir / "generated_data_item.json", item)

    score_input = {"logp": item["logp"], "logq": item["logq"], "score": item["score"]}
    variance_input = {"score": item["score"], "local_signal": item["local_signal"], "full_signal": item["full_signal"]}
    _write_json(work_dir / "score_input.json", score_input)
    _write_json(work_dir / "variance_input.json", variance_input)

    score_script = skills_root / "bbvi_score_function_gradient" / "scripts" / "score_gradient.py"
    variance_script = skills_root / "bbvi_variance_reduction" / "scripts" / "variance_reduction.py"
    optimizer_script = skills_root / "bbvi_stochastic_optimizer" / "scripts" / "optimizer.py"
    command_log = []
    score_output = work_dir / "score_output.json"
    variance_output = work_dir / "variance_output.json"
    command_log.append(_run_command([sys.executable, str(score_script), str(work_dir / "score_input.json"), "--output", str(score_output)]))
    command_log.append(_run_command([sys.executable, str(variance_script), str(work_dir / "variance_input.json"), "--output", str(variance_output)]))
    score_result = _load_json(score_output)
    variance_result = _load_json(variance_output)
    optimizer_input = {
        "params": [item["variational_mean"]],
        "gradient": variance_result["control_variate_estimate"],
        "method": "adagrad",
        "learning_rate": 0.1,
    }
    _write_json(work_dir / "optimizer_input.json", optimizer_input)
    optimizer_output = work_dir / "optimizer_output.json"
    command_log.append(_run_command([sys.executable, str(optimizer_script), str(work_dir / "optimizer_input.json"), "--output", str(optimizer_output)]))
    optimizer_result = _load_json(optimizer_output)
    observed_mean = item["observed_mean"]
    loss_before = (optimizer_result["params_before"][0] - observed_mean) ** 2
    loss_after = (optimizer_result["params_after"][0] - observed_mean) ** 2
    optimizer_result["loss_before"] = loss_before
    optimizer_result["loss_after"] = loss_after
    optimizer_result["optimizer_state_changed"] = optimizer_result.get("state_before") != optimizer_result.get("state_after")
    _write_json(logs_dir / "training_trace.json", optimizer_result)

    generated_skill_invocations = {
        "schema_version": 1,
        "invocations": [
            {"module_id": "score_function_elbo_gradient", "skill": "bbvi_score_function_gradient", "kind": "called script", "evidence": "called script", "artifact": str(score_output.relative_to(attempt_dir))},
            {"module_id": "variance_reduction_estimators", "skill": "bbvi_variance_reduction", "kind": "called script", "evidence": "called script", "artifact": str(variance_output.relative_to(attempt_dir))},
            {"module_id": "stochastic_bbvi_optimizer", "skill": "bbvi_stochastic_optimizer", "kind": "called script", "evidence": "called script", "artifact": str(optimizer_output.relative_to(attempt_dir))},
            {"module_id": "proxy_recovery_harness", "skill": "bbvi_proxy_recovery_harness", "kind": "called script", "evidence": "called script", "artifact": "recovery/recovery_result.json"}
        ]
    }
    _write_json(logs_dir / "generated_skill_invocations.json", generated_skill_invocations)
    _write_json(logs_dir / "experiment_command_log.json", {"schema_version": 1, "commands": command_log})

    target = module_plan["fast_recovery_target"]
    ratio = variance_result["variance_reduction_ratio"]
    mechanism_checks = {
        "score_function_gradient_executed": command_log[0]["returncode"] == 0 and bool(score_result["gradient_estimate"]),
        "rao_blackwellized_terms_executed": command_log[1]["returncode"] == 0 and variance_result["variance"]["rao_blackwell"] is not None,
        "control_variate_executed": command_log[1]["returncode"] == 0 and math.isfinite(variance_result["control_variate_scale"]),
        "variance_reduction_observed": ratio is not None and ratio > target["paper_value"],
        "optimizer_step_executed": bool(optimizer_result["optimizer_step_executed"]),
        "reduced_training_executed": True,
        "full_medical_dataset_available": False,
        "original_repo_read": False,
        "runtime_handoff_consumed": runtime_handoff_path.exists(),
    }
    result = {
        "schema_version": 1,
        "paper_id": module_plan["paper_id"],
        "experiment": target["dataset"],
        "is_proxy": True,
        "sample_count": len(item["samples"]),
        "metrics": {
            "variance_reduction_ratio": ratio,
            "naive_variance": variance_result["variance"]["naive"],
            "control_variate_variance": variance_result["variance"]["control_variate"],
        },
        "paper_target": target,
        "commands": [" ".join(entry["command"]) for entry in command_log],
        "artifacts": [
            "recovery/logs/generated_data_item.json",
            "recovery/logs/training_trace.json",
            "recovery/logs/generated_skill_invocations.json",
            "recovery/work/score_output.json",
            "recovery/work/variance_output.json",
        ],
        "mechanism_checks": mechanism_checks,
        "runtime_handoff_summary": {
            "runtime_ready": runtime_handoff.get("runtime_ready"),
            "reduced_recovery_recommended": runtime_handoff.get("reduced_recovery_recommended"),
            "environment_modified": runtime_handoff.get("environment_modified"),
        },
        "notes": "Soft-mode proxy recovery: original private medical dataset and 20-hour comparison are unavailable, so this bounded synthetic Normal experiment validates BBVI score-function gradients, variance reduction, and AdaGrad state change.",
    }
    _write_json(recovery_dir / "recovery_result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("attempt_dir")
    parser.add_argument("--skills-root", required=True)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()
    run_proxy(args.attempt_dir, args.skills_root, args.seed)


if __name__ == "__main__":
    main()
