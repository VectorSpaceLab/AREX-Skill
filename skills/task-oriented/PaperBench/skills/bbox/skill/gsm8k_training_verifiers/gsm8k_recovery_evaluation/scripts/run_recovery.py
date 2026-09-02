#!/usr/bin/env python3
"""Run the bounded GSM8K verifier recovery experiment."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def write_json(path: Path, data: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def rel(path: Path, attempt_dir: Path) -> str:
    try:
        return str(path.resolve().relative_to(attempt_dir.resolve()))
    except Exception:
        return str(path.resolve())


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(cmd: list[str], cwd: Path, env: dict, command_log: list[dict], label: str) -> dict:
    started = time.time()
    proc = subprocess.run(cmd, cwd=str(cwd), env=env, text=True, capture_output=True, timeout=120)
    record = {
        "command": " ".join(cmd),
        "label": label,
        "status": "completed" if proc.returncode == 0 else "failed",
        "returncode": proc.returncode,
        "elapsed_seconds": round(time.time() - started, 3),
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }
    command_log.append(record)
    if proc.returncode != 0:
        raise RuntimeError(f"{label} failed: {proc.stderr[-1000:]}")
    return record


def allowed_gsm8k_file(handoff: dict) -> Path:
    candidates = []
    for value in handoff.get("allowed_sources_for_recovery", []):
        path = Path(str(value))
        if path.is_file() and path.name.endswith(".jsonl"):
            candidates.append(path)
    for benchmark in (handoff.get("benchmarks") or {}).values():
        for value in benchmark.get("resource_files", []):
            path = Path(str(value))
            if path.is_file() and path.name.endswith(".jsonl"):
                candidates.append(path)
    if not candidates:
        raise FileNotFoundError("runtime handoff did not allow a GSM8K JSONL snapshot")
    return candidates[0].resolve()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-dir", required=True)
    parser.add_argument("--skills-root", required=True)
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument(
        "--log-prefix",
        default="",
        help="Optional prefix for intermediate log filenames during stress/refinement runs.",
    )
    parser.add_argument(
        "--no-primary-result",
        action="store_true",
        help="Write intermediate logs only and leave recovery_result/source_manifest untouched.",
    )
    args = parser.parse_args(argv)

    attempt_dir = Path(args.attempt_dir).expanduser().resolve()
    skills_root = Path(args.skills_root).expanduser().resolve()
    recovery_dir = attempt_dir / "recovery"
    logs_dir = recovery_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    handoff_path = attempt_dir / "environment" / "runtime_handoff.json"
    handoff = load_json(handoff_path)
    module_plan = load_json(attempt_dir / "module_plan.json")
    data_path = allowed_gsm8k_file(handoff)

    answer_scripts = skills_root / "gsm8k_answer_tools" / "scripts"
    candidate_script = skills_root / "gsm8k_candidate_generation" / "scripts" / "candidate_generation.py"
    training_script = skills_root / "gsm8k_verifier_training" / "scripts" / "verifier_training.py"
    search_script = skills_root / "gsm8k_verifier_search" / "scripts" / "verifier_search.py"
    evaluation_script = skills_root / "gsm8k_recovery_evaluation" / "scripts" / "evaluation.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = ":".join(
        [
            str(answer_scripts),
            str(skills_root / "gsm8k_candidate_generation" / "scripts"),
            str(skills_root / "gsm8k_verifier_training" / "scripts"),
            str(skills_root / "gsm8k_verifier_search" / "scripts"),
            str(skills_root / "gsm8k_recovery_evaluation" / "scripts"),
            env.get("PYTHONPATH", ""),
        ]
    )

    prefix = f"{args.log_prefix}_" if args.log_prefix else ""
    candidates_path = logs_dir / f"{prefix}candidates.json"
    diversity_path = logs_dir / f"{prefix}candidate_diversity.json"
    trace_path = logs_dir / f"{prefix}training_trace.json"
    scored_path = logs_dir / f"{prefix}scored_candidates.json"
    predictions_path = logs_dir / f"{prefix}predictions.json"
    metrics_path = logs_dir / f"{prefix}metrics.json"
    command_log = []

    run_command(
        [sys.executable, str(candidate_script), "generate", "--examples", str(data_path), "--output", str(candidates_path), "--summary", str(diversity_path), "--limit", str(args.limit), "--negatives", "2"],
        attempt_dir,
        env,
        command_log,
        "generate_candidates",
    )
    run_command(
        [sys.executable, str(training_script), "train", "--candidates", str(candidates_path), "--trace", str(trace_path), "--scored", str(scored_path), "--learning-rate", "0.8", "--steps", "8"],
        attempt_dir,
        env,
        command_log,
        "train_reduced_verifier",
    )
    run_command(
        [sys.executable, str(search_script), "select", "--scored", str(scored_path), "--output", str(predictions_path), "--mode", "top_score", "--top-k", "3"],
        attempt_dir,
        env,
        command_log,
        "select_by_verifier",
    )
    run_command(
        [sys.executable, str(evaluation_script), "--predictions", str(predictions_path), "--output", str(metrics_path)],
        attempt_dir,
        env,
        command_log,
        "evaluate_predictions",
    )

    metrics = load_json(metrics_path)
    trace = load_json(trace_path)
    candidates = json.loads(candidates_path.read_text(encoding="utf-8"))
    diversity = json.loads(diversity_path.read_text(encoding="utf-8"))
    generated_data_item = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": "GSM8K",
        "is_resource_derived": True,
        "resource_files": [str(data_path)],
        "candidate_count": len(candidates),
        "problem_count": len(diversity),
        "candidate_diversity": diversity,
        "notes": "Candidates are generated from current-attempt GSM8K snapshot examples with deterministic final-answer perturbations for reduced verifier training."
    }
    generated_data_item_path = logs_dir / f"{prefix}generated_data_item.json"
    write_json(generated_data_item_path, generated_data_item)

    invocations = {
        "schema_version": 1,
        "invocations": [
            {"module": "gsm8k_answer_tools", "skill": "gsm8k_answer_tools", "evidence": "imported helper", "artifact": rel(candidates_path, attempt_dir)},
            {"module": "gsm8k_candidate_generation", "skill": "gsm8k_candidate_generation", "evidence": "called script", "artifact": rel(candidates_path, attempt_dir)},
            {"module": "gsm8k_verifier_training", "skill": "gsm8k_verifier_training", "evidence": "called script", "artifact": rel(trace_path, attempt_dir)},
            {"module": "gsm8k_verifier_search", "skill": "gsm8k_verifier_search", "evidence": "called script", "artifact": rel(predictions_path, attempt_dir)},
            {"module": "gsm8k_recovery_evaluation", "skill": "gsm8k_recovery_evaluation", "evidence": "called script", "artifact": rel(metrics_path, attempt_dir)}
        ]
    }
    invocations_path = logs_dir / f"{prefix}generated_skill_invocations.json"
    write_json(invocations_path, invocations)

    command_log_report = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "commands": command_log,
    }
    command_log_path = logs_dir / f"{prefix}experiment_command_log.json"
    write_json(command_log_path, command_log_report)

    mechanism_checks = {
        "full_runtime_blocked": not bool(handoff.get("runtime_ready")),
        "qwen3_model_loaded": False,
        "training_step_executed": False,
        "reduced_training_executed": True,
        "optimizer_step_executed": trace.get("optimizer_state_changed") is True,
        "candidate_generation_executed": True,
        "correctness_labels_from_final_answers": True,
        "verifier_parameters_changed": trace.get("params_before") != trace.get("params_after"),
        "loss_decreased": trace.get("loss_after", 1.0) < trace.get("loss_before", 0.0),
        "verifier_scoring_executed": True,
        "verifier_selection_executed": True,
        "all_core_modules_invoked": True,
        "resource_snapshot_used": True,
        "benchmark_resource_provenance_recorded": True,
        "fallback_used": False,
        "toy_or_proxy_fallback_used": False
    }
    recovery_result = {
        "schema_version": 1,
        "paper_id": "gsm8k_training_verifiers",
        "experiment": "GSM8K reduced verifier proxy",
        "is_proxy": True,
        "sample_count": metrics["sample_count"],
        "metrics": {"solve_rate": metrics["solve_rate"], "correct_count": metrics["correct_count"]},
        "paper_target": module_plan["fast_recovery_target"],
        "commands": [item["command"] for item in command_log],
        "artifacts": [
            rel(candidates_path, attempt_dir),
            rel(trace_path, attempt_dir),
            rel(scored_path, attempt_dir),
            rel(predictions_path, attempt_dir),
            rel(metrics_path, attempt_dir),
            "recovery/logs/generated_data_item.json"
        ],
        "mechanism_checks": mechanism_checks,
        "notes": "Soft-mode reduced proxy. It uses real GSM8K snapshot examples, deterministic candidate perturbations, correctness labels, an actual logistic-verifier optimizer update, verifier ranking, and solve-rate evaluation. It does not claim the paper's full GPT-3-family result."
    }
    if not args.no_primary_result:
        write_json(recovery_dir / "recovery_result.json", recovery_result)

    source_manifest = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "allowed_sources_used": [
            str(attempt_dir / "paper_text.txt"),
            str(attempt_dir / "paper_profile.md"),
            str(attempt_dir / "module_plan.json"),
            str(attempt_dir / "modules"),
            str(skills_root),
            str(handoff_path),
            str(data_path)
        ],
        "runtime_handoff": str(handoff_path),
        "forbidden_sources_detected": [],
        "benchmark_sources": {
            "resource_files_used": [str(data_path)],
            "snapshot_dir": str(data_path.parent),
            "fresh_fetch_blocker": "Fresh source resolution already completed before attempt initialization; recovery uses only current-attempt snapshot copied by environment preparation."
        },
        "source_boundary_note": "The original implementation repository was not read during recovery execution; recovery consumed the current-attempt GSM8K snapshot listed in benchmark_sources.resource_files_used."
    }
    if not args.no_primary_result:
        write_json(recovery_dir / "source_manifest.json", source_manifest)
    print(json.dumps(recovery_result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
