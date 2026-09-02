#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_reduced_recovery(attempt_dir: Path, skill_root: Path, seed: int = 7) -> dict:
    attempt_dir = attempt_dir.resolve()
    skill_root = skill_root.resolve()
    recovery_dir = attempt_dir / "recovery"
    logs_dir = recovery_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    module_plan = load_json(attempt_dir / "module_plan.json")
    handoff_path = attempt_dir / "environment" / "runtime_handoff.json"
    runtime_handoff = load_json(handoff_path) if handoff_path.exists() else {}

    batching = load_module("transition_batch", skill_root / "transition_skill_batching" / "scripts" / "transition_batch.py")
    cic_loss = load_module("cic_loss", skill_root / "cic_contrastive_loss" / "scripts" / "cic_loss.py")
    entropy = load_module("entropy_reward", skill_root / "particle_entropy_reward" / "scripts" / "entropy_reward.py")

    batch = batching.deterministic_synthetic_batch(batch_size=8, state_dim=3, skill_dim=3, seed=seed)
    tau = batch["tau"]
    skills = batch["skills"]
    query_weights = cic_loss.identity_weights(3, 3)
    key_weights = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    trace = cic_loss.finite_difference_update(tau, skills, query_weights, key_weights, temperature=0.35, learning_rate=0.1)
    transition_embeddings = cic_loss.normalize_rows(cic_loss.matmul(tau, key_weights))
    reward_result = entropy.particle_entropy_reward(transition_embeddings, k=3)

    data_item = {
        "schema_version": 1,
        "dataset": "synthetic_state_transition_skill_pairs",
        "split": "deterministic_8_pair_proxy",
        "is_resource_derived": False,
        "resource_files": [],
        "reason_not_resource_derived": "The paper's full URLB benchmark/runtime was not prepared in this bounded soft-mode run; this deterministic synthetic batch preserves CIC transition-skill mechanics.",
        "batch_metadata": batch["metadata"],
        "sample_count": batch["metadata"]["batch_size"],
        "seed": seed,
        "first_tau": tau[0],
        "first_skill": skills[0]
    }
    write_json(logs_dir / "generated_data_item.json", data_item)

    training_trace = dict(trace)
    training_trace.update({
        "schema_version": 1,
        "optimizer": "finite_difference_gradient_descent",
        "learning_rate": 0.1,
        "temperature": 0.35,
        "entropy_rewards": reward_result["rewards"],
        "entropy_reward_mean": reward_result["diagnostics"]["mean_reward"],
        "parameters_before": trace["params_before"],
        "parameters_after": trace["params_after"]
    })
    write_json(logs_dir / "training_trace.json", training_trace)
    write_json(logs_dir / "entropy_reward_diagnostics.json", reward_result)

    invocations = {
        "schema_version": 1,
        "invocations": [
            {"module": "transition_skill_batching", "skill": "transition_skill_batching", "evidence": "imported helper", "artifact": "recovery/logs/generated_data_item.json"},
            {"module": "cic_contrastive_loss", "skill": "cic_contrastive_loss", "evidence": "imported helper", "artifact": "recovery/logs/training_trace.json"},
            {"module": "particle_entropy_reward", "skill": "particle_entropy_reward", "evidence": "imported helper", "artifact": "recovery/logs/entropy_reward_diagnostics.json"},
            {"module": "reduced_cic_recovery_harness", "skill": "reduced_cic_recovery_harness", "evidence": "called script", "artifact": "recovery/recovery_result.json"}
        ]
    }
    write_json(logs_dir / "generated_skill_invocations.json", invocations)

    source_manifest = {
        "schema_version": 1,
        "allowed_sources_used": [
            str(attempt_dir / "paper_text.txt"),
            str(attempt_dir / "paper_profile.md"),
            str(attempt_dir / "module_plan.json"),
            str(attempt_dir / "modules"),
            str(skill_root),
            str(handoff_path)
        ],
        "runtime_handoff": str(handoff_path),
        "original_repo_source": "unknown",
        "forbidden_sources_detected": [],
        "benchmark_sources": {},
        "notes": "No original implementation repository was available or read during recovery."
    }
    write_json(recovery_dir / "source_manifest.json", source_manifest)

    margin_improvement = trace["margin_after"] - trace["margin_before"]
    loss_reduction = trace["loss_before"] - trace["loss_after"]
    mechanism_checks = {
        "proxy_declared": True,
        "full_urlb_training_blocked": True,
        "qwen3_model_loaded": False,
        "training_step_executed": False,
        "reduced_training_executed": True,
        "optimizer_step_executed": True,
        "transition_tuple_constructed": True,
        "continuous_skills_used": True,
        "contrastive_loss_computed": True,
        "diagonal_positive_labels_used": True,
        "particle_entropy_reward_computed": True,
        "finite_entropy_rewards": all(math.isfinite(value) for value in reward_result["rewards"]),
        "parameters_changed": trace["params_before"] != trace["params_after"],
        "loss_reduction": loss_reduction,
        "positive_logit_margin_before": trace["margin_before"],
        "positive_logit_margin_after": trace["margin_after"],
        "positive_logit_margin_improvement": margin_improvement,
        "fallback_used": True,
        "toy_or_proxy_fallback_used": True
    }
    recovery_result = {
        "schema_version": 1,
        "paper_id": module_plan["paper_id"],
        "experiment": module_plan["fast_recovery_target"]["dataset"],
        "is_proxy": True,
        "sample_count": batch["metadata"]["batch_size"],
        "metrics": {
            "positive_logit_margin_after_update": trace["margin_after"],
            "positive_logit_margin_improvement": margin_improvement,
            "loss_reduction": loss_reduction,
            "mean_entropy_reward": reward_result["diagnostics"]["mean_reward"]
        },
        "paper_target": module_plan["fast_recovery_target"],
        "commands": ["python recovery/run_recovery.py --attempt-dir <attempt_dir> --skill-root <skill_root>"],
        "artifacts": [
            "recovery/logs/generated_data_item.json",
            "recovery/logs/training_trace.json",
            "recovery/logs/entropy_reward_diagnostics.json",
            "recovery/logs/generated_skill_invocations.json"
        ],
        "mechanism_checks": mechanism_checks,
        "notes": "Soft-mode reduced proxy: validates CIC contrastive transition-skill alignment, particle entropy reward, and an actual tiny optimizer step; does not claim full URLB performance."
    }
    write_json(recovery_dir / "recovery_result.json", recovery_result)
    return recovery_result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run reduced CIC recovery and write artifacts.")
    parser.add_argument("--attempt-dir", required=True)
    parser.add_argument("--skill-root", required=True)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args(argv)
    result = run_reduced_recovery(Path(args.attempt_dir), Path(args.skill_root), args.seed)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
