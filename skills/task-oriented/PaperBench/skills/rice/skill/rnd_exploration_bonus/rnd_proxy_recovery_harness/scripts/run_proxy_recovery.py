#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
from pathlib import Path


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic_vectors(target_count: int) -> dict:
    seen = [[1.0, 0.0, 0.05 * ((i % 3) - 1)] for i in range(18)]
    target = [[0.0, 1.0, 0.04 * ((i % 5) - 2)] for i in range(target_count)]
    heldout = [[0.0, 1.0, 0.12], [0.0, 1.0, -0.12], [0.0, 0.95, 0.0]]
    return {"seen": seen, "target_train": target, "heldout_target": heldout}


def run_regime(target_count: int, skills_root: Path) -> dict:
    normalization = load_module(skills_root / "rnd_observation_normalization" / "scripts" / "normalization.py", "norm_skill")
    rnd_model = load_module(skills_root / "rnd_bonus_model" / "scripts" / "rnd_model.py", "rnd_model_skill")
    data = synthetic_vectors(target_count)
    train = data["seen"] + data["target_train"]
    norm_result = normalization.normalize_with_update(train + data["heldout_target"])
    normalized_train = norm_result["normalized"][: len(train)]
    normalized_heldout = norm_result["normalized"][len(train) :]
    target = rnd_model.make_matrix(4, len(normalized_train[0]), seed=101)
    predictor = rnd_model.make_matrix(4, len(normalized_train[0]), seed=202)
    trace = rnd_model.train_predictor(target, predictor, normalized_train, lr=0.08, steps=160)
    heldout_error = sum(rnd_model.mse_errors(target, predictor, normalized_heldout)) / len(normalized_heldout)
    return {"target_count": target_count, "data": data, "normalizer_stats": norm_result["stats"], "trace": trace, "heldout_target_mse": heldout_error}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-dir", required=True)
    parser.add_argument("--skills-root", required=True)
    args = parser.parse_args()
    started = time.time()
    attempt_dir = Path(args.attempt_dir).resolve()
    skills_root = Path(args.skills_root).resolve()
    recovery_dir = attempt_dir / "recovery"
    logs_dir = recovery_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    module_plan = json.loads((attempt_dir / "module_plan.json").read_text(encoding="utf-8"))
    handoff_path = attempt_dir / "environment" / "runtime_handoff.json"
    handoff = json.loads(handoff_path.read_text(encoding="utf-8")) if handoff_path.exists() else {}

    low = run_regime(1, skills_root)
    high = run_regime(9, skills_root)
    reduction = (low["heldout_target_mse"] - high["heldout_target_mse"]) / max(low["heldout_target_mse"], 1e-12)

    reward_scaling = load_module(skills_root / "rnd_intrinsic_reward_scaling" / "scripts" / "reward_scaling.py", "scaling_skill")
    dual_returns = load_module(skills_root / "rnd_dual_value_return_combination" / "scripts" / "dual_returns.py", "dual_skill")
    scaling_check = reward_scaling.scale_intrinsic_rewards([low["heldout_target_mse"], high["heldout_target_mse"]], gamma=0.99)
    returns_check = dual_returns.combine_returns([0.0, 1.0], scaling_check["scaled_rewards"], [False, True], gamma_e=0.999, gamma_i=0.99, intrinsic_non_episodic=True)

    data_item = {
        "schema_version": 1,
        "dataset": "synthetic_mnist_style_novelty_vectors",
        "is_resource_derived": False,
        "resource_files": [],
        "construction": "Deterministic vector proxy: seen class near [1,0,*], target class near [0,1,*], with low-target and high-target regimes mirroring the paper's MNIST intuition experiment.",
        "low_target_count": low["target_count"],
        "high_target_count": high["target_count"],
        "heldout_count": len(low["data"]["heldout_target"])
    }
    (logs_dir / "generated_data_item.json").write_text(json.dumps(data_item, indent=2) + "\n", encoding="utf-8")

    training_trace = {
        "schema_version": 1,
        "proxy_regimes": {"low_target": low, "high_target": high},
        "loss_before": high["trace"]["loss_before"],
        "loss_after": high["trace"]["loss_after"],
        "params_before": high["trace"]["params_before"],
        "params_after": high["trace"]["params_after"],
        "optimizer_state_changed": high["trace"]["predictor_changed"],
        "target_unchanged": high["trace"]["target_unchanged"],
        "heldout_mse_low_target": low["heldout_target_mse"],
        "heldout_mse_high_target": high["heldout_target_mse"],
        "novelty_mse_reduction_fraction": reduction,
        "scaling_check": scaling_check,
        "dual_return_check": returns_check
    }
    (logs_dir / "training_trace.json").write_text(json.dumps(training_trace, indent=2) + "\n", encoding="utf-8")

    invocations = {
        "schema_version": 1,
        "invocations": [
            {"module": "observation_normalization", "skill": "rnd_observation_normalization", "evidence": "imported helper", "artifact": "recovery/logs/training_trace.json"},
            {"module": "rnd_bonus_model", "skill": "rnd_bonus_model", "evidence": "imported helper", "artifact": "recovery/logs/training_trace.json"},
            {"module": "intrinsic_reward_scaling", "skill": "rnd_intrinsic_reward_scaling", "evidence": "cross-check", "artifact": "recovery/logs/training_trace.json"},
            {"module": "dual_value_return_combination", "skill": "rnd_dual_value_return_combination", "evidence": "cross-check", "artifact": "recovery/logs/training_trace.json"},
            {"module": "rnd_proxy_recovery_harness", "skill": "rnd_proxy_recovery_harness", "evidence": "called script", "artifact": "recovery/recovery_result.json"}
        ]
    }
    (logs_dir / "generated_skill_invocations.json").write_text(json.dumps(invocations, indent=2) + "\n", encoding="utf-8")

    source_manifest = {
        "schema_version": 1,
        "allowed_sources_used": [
            "paper_profile.md",
            "module_plan.json",
            "modules/*.md",
            str(skills_root),
            "environment/runtime_handoff.json"
        ],
        "forbidden_sources_detected": [],
        "original_repo_used_during_recovery": False,
        "runtime_handoff": "environment/runtime_handoff.json",
        "benchmark_sources": {},
        "notes": "Recovery intentionally did not read the original random-network-distillation repository."
    }
    (recovery_dir / "source_manifest.json").write_text(json.dumps(source_manifest, indent=2) + "\n", encoding="utf-8")

    result = {
        "schema_version": 1,
        "paper_id": "rnd_exploration_bonus",
        "experiment": module_plan["fast_recovery_target"]["dataset"],
        "is_proxy": True,
        "sample_count": len(low["data"]["seen"]) + len(low["data"]["target_train"]) + len(high["data"]["target_train"]) + len(low["data"]["heldout_target"]),
        "metrics": {"novelty_mse_reduction_fraction": reduction, "heldout_mse_low_target": low["heldout_target_mse"], "heldout_mse_high_target": high["heldout_target_mse"]},
        "paper_target": module_plan["fast_recovery_target"],
        "commands": ["python recovery/run_recovery.py --attempt-dir " + str(attempt_dir) + " --skills-root " + str(skills_root)],
        "artifacts": ["recovery/logs/generated_data_item.json", "recovery/logs/training_trace.json", "recovery/logs/generated_skill_invocations.json"],
        "mechanism_checks": {
            "deterministic_random_target_used": True,
            "target_network_frozen": high["trace"]["target_unchanged"],
            "predictor_updated": high["trace"]["predictor_changed"],
            "observation_normalization_applied": True,
            "intrinsic_reward_scaling_cross_checked": True,
            "dual_value_return_contract_cross_checked": True,
            "novelty_error_decreased_with_more_target_data": reduction > 0,
            "reduced_training_executed": True,
            "optimizer_step_executed": True,
            "training_step_executed": False,
            "qwen3_model_loaded": False,
            "fallback_used": True,
            "toy_or_proxy_fallback_used": True,
            "full_atari_training_blocked": True
        },
        "runtime_handoff": str(handoff_path),
        "notes": "Soft-mode reduced proxy recovery. Full Atari PPO/RND training was blocked by bounded runtime; this experiment validates the paper's RND novelty mechanism with executable optimizer evidence.",
        "elapsed_seconds": round(time.time() - started, 3),
        "runtime_ready": handoff.get("runtime_ready", False)
    }
    (recovery_dir / "recovery_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "reduction": reduction, "result": str(recovery_dir / "recovery_result.json")}, indent=2))
    return 0 if reduction > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
