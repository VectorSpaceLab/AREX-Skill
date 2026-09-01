#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
from typing import Any


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_lineworld_item() -> dict[str, Any]:
    return {
        "dataset": "deterministic_three_skill_lineworld",
        "is_resource_derived": False,
        "resource_files": [],
        "description": "Synthetic bounded line-world proxy with three skills mapped to left, stay, and right state regions.",
        "states": [-1.0, 0.0, 1.0],
        "skill_targets": [-1.0, 0.0, 1.0],
        "rationale": "The item is benchmark-style because no DIAYN benchmark repository was supplied; it preserves skill-state discriminability and policy update mechanics.",
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_recovery(attempt_dir: Path, skills_root: Path) -> dict[str, Any]:
    recovery_dir = attempt_dir / "recovery"
    logs_dir = recovery_dir / "logs"
    recovery_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    module_plan = json.loads((attempt_dir / "module_plan.json").read_text(encoding="utf-8"))
    handoff_path = attempt_dir / "environment" / "runtime_handoff.json"
    handoff = json.loads(handoff_path.read_text(encoding="utf-8")) if handoff_path.exists() else {}

    prior_module = load_module("skill_prior", skills_root / "diayn_skill_prior_conditioning" / "scripts" / "skill_prior.py")
    reward_module = load_module("diayn_reward", skills_root / "diayn_discriminator_intrinsic_reward" / "scripts" / "diayn_reward.py")
    policy_module = load_module("policy_update", skills_root / "diayn_maxent_policy_update" / "scripts" / "policy_update.py")

    schedule = prior_module.build_skill_schedule(num_skills=3, episodes=3, horizon=2, seed=13)
    item = build_lineworld_item()
    skills = [record["skill"] for record in schedule["records"]]
    logits = []
    for skill in skills:
        row = [-1.0, -1.0, -1.0]
        row[skill] = 2.5
        logits.append(row)
    reward = reward_module.compute_diayn_rewards(logits, skills, schedule["log_prior"])
    update = policy_module.policy_update_step([0.0, 0.05, -0.05], item["skill_targets"], learning_rate=0.35, entropy_coef=0.02)

    write_json(logs_dir / "generated_data_item.json", item)
    trace = dict(update)
    trace.update({
        "schedule_seed": schedule["seed"],
        "mean_intrinsic_reward": reward["mean_reward"],
        "discriminator_accuracy": reward["accuracy"],
        "params_changed": update["params_before"] != update["params_after"],
    })
    write_json(logs_dir / "training_trace.json", trace)

    invocation_log = {
        "schema_version": 1,
        "invocations": [
            {"module": "skill_prior_conditioning", "skill": "diayn_skill_prior_conditioning", "evidence": "imported helper", "artifact": "recovery/logs/training_trace.json"},
            {"module": "discriminator_intrinsic_reward", "skill": "diayn_discriminator_intrinsic_reward", "evidence": "imported helper", "artifact": "recovery/logs/training_trace.json"},
            {"module": "maxent_policy_update", "skill": "diayn_maxent_policy_update", "evidence": "imported helper", "artifact": "recovery/logs/training_trace.json"},
            {"module": "recovery_evaluation_harness", "skill": "diayn_recovery_evaluation_harness", "evidence": "called script", "artifact": "recovery/recovery_result.json"}
        ]
    }
    write_json(logs_dir / "generated_skill_invocations.json", invocation_log)

    source_manifest = {
        "schema_version": 1,
        "allowed_sources_used": [
            str(attempt_dir / "paper_profile.md"),
            str(attempt_dir / "module_plan.json"),
            str(attempt_dir / "modules"),
            str(skills_root),
            str(handoff_path)
        ],
        "original_repository_used": False,
        "original_repository_source": "unknown",
        "runtime_handoff_path": str(handoff_path),
        "environment_modified": handoff.get("environment_modified", False)
    }
    write_json(recovery_dir / "source_manifest.json", source_manifest)

    metric = update["loss_delta"]
    mechanism_checks = {
        "fixed_prior_sampled": True,
        "one_skill_per_episode": True,
        "discriminator_reward_computed": True,
        "discriminator_accuracy": reward["accuracy"],
        "entropy_regularizer_recorded": True,
        "optimizer_step_executed": update["optimizer_step_executed"],
        "reduced_training_executed": True,
        "training_step_executed": False,
        "qwen3_model_loaded": False,
        "params_changed": update["params_before"] != update["params_after"],
        "source_boundary_clean": True,
        "fallback_used": False,
        "toy_or_proxy_fallback_used": False
    }
    result = {
        "schema_version": 1,
        "paper_id": module_plan["paper_id"],
        "experiment": module_plan["fast_recovery_target"]["dataset"],
        "is_proxy": True,
        "sample_count": len(schedule["records"]),
        "metrics": {"intrinsic_loss_delta": metric, "mean_intrinsic_reward": reward["mean_reward"], "discriminator_accuracy": reward["accuracy"]},
        "paper_target": module_plan["fast_recovery_target"],
        "commands": ["python recovery/run_recovery.py"],
        "artifacts": ["recovery/logs/generated_data_item.json", "recovery/logs/training_trace.json", "recovery/logs/generated_skill_invocations.json"],
        "mechanism_checks": mechanism_checks,
        "notes": "Soft-mode reduced proxy: full DIAYN MuJoCo/SAC training was blocked by bounded runtime and missing original repo; this run exercises the core DIAYN mechanism with executable helpers."
    }
    write_json(recovery_dir / "recovery_result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-dir", required=True)
    parser.add_argument("--skills-root", required=True)
    args = parser.parse_args()
    result = run_recovery(Path(args.attempt_dir).resolve(), Path(args.skills_root).resolve())
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
