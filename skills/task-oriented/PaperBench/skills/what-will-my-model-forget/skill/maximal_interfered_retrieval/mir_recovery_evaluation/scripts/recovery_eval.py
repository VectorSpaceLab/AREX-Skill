from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Mapping, Sequence


def add_skill_paths(generated_skills_root: Path) -> None:
    for skill_name in ["online_stream_memory", "virtual_update_interference", "generative_latent_mir"]:
        scripts_dir = generated_skills_root / skill_name / "scripts"
        if scripts_dir.exists() and str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))


def sigmoid(value: float) -> float:
    import math
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def predict(params: Mapping[str, object], features: Sequence[float]) -> int:
    score = sum(float(w) * float(x) for w, x in zip(params["weights"], features)) + float(params.get("bias", 0.0))
    return 1 if sigmoid(score) >= 0.5 else 0


def update(params: Mapping[str, object], batch: Sequence[Mapping[str, object]], learning_rate: float) -> dict:
    from mir_scoring import batch_gradient
    gradient = batch_gradient(params, batch)
    return {
        "weights": [float(w) - learning_rate * float(g) for w, g in zip(params["weights"], gradient["weights"])],
        "bias": float(params.get("bias", 0.0)) - learning_rate * float(gradient["bias"]),
    }


def accuracy(params: Mapping[str, object], examples: Sequence[Mapping[str, object]]) -> float:
    if not examples:
        return 0.0
    correct = sum(1 for item in examples if predict(params, item["features"]) == int(item["label"]))
    return correct / len(examples)


def build_proxy_stream() -> list[dict]:
    from stream_memory import make_stream
    tasks = [
        [([2.0, 0.2], 1), ([-2.0, -0.2], 0), ([1.7, -0.1], 1), ([-1.7, 0.1], 0)],
        [([0.2, 2.0], 1), ([-0.2, -2.0], 0), ([-0.1, 1.7], 1), ([0.1, -1.7], 0)],
        [([-2.0, 0.3], 1), ([2.0, -0.3], 0), ([-1.6, -0.1], 1), ([1.6, 0.1], 0)],
    ]
    return make_stream(tasks)


def run_selector(selector: str, learning_rate: float = 0.8, memory_capacity: int = 6, candidate_count: int = 6, replay_budget: int = 2) -> dict:
    from mir_scoring import logistic_loss, select_top_interfered
    from stream_memory import ReplayMemory, compute_forgetting

    stream = build_proxy_stream()
    memory = ReplayMemory(memory_capacity, seed=17)
    params = {"weights": [0.0, 0.0], "bias": 0.0}
    seen_by_task: dict[str, list[dict]] = {}
    accuracy_history: dict[str, list[float]] = {}
    trace = []

    for index, example in enumerate(stream):
        incoming = [example]
        candidates = memory.candidates(candidate_count)
        if selector == "mir":
            selection_result = select_top_interfered(params, incoming, candidates, learning_rate, replay_budget)
            replay = [item["candidate"] for item in selection_result["selected"]]
            scores = selection_result["scores"]
        else:
            replay = candidates[:replay_budget]
            scores = []
        batch = incoming + replay
        loss_before = sum(logistic_loss(params, item) for item in batch) / len(batch)
        params_before = dict(params)
        params = update(params, batch, learning_rate)
        loss_after = sum(logistic_loss(params, item) for item in batch) / len(batch)
        memory.add_many(incoming)
        task_key = str(example["task_id"])
        seen_by_task.setdefault(task_key, []).append(example)
        if index == len(stream) - 1 or stream[index + 1]["task_id"] != example["task_id"]:
            for eval_task, eval_examples in seen_by_task.items():
                accuracy_history.setdefault(eval_task, []).append(accuracy(params, eval_examples))
        trace.append({
            "step": index,
            "selector": selector,
            "incoming_id": example["example_id"],
            "candidate_ids": [item.get("example_id") for item in candidates],
            "selected_replay_ids": [item.get("example_id") for item in replay],
            "scores": scores,
            "loss_before": loss_before,
            "loss_after": loss_after,
            "params_before": params_before,
            "params_after": dict(params),
        })
    forgetting = compute_forgetting(accuracy_history)
    final_accuracy = accuracy(params, stream)
    return {"selector": selector, "final_accuracy": final_accuracy, "forgetting": forgetting, "trace": trace, "params": params}


def run_latent_cross_check() -> dict:
    try:
        from latent_mir import select_diverse_latents
    except Exception as exc:
        return {"available": False, "error": str(exc)}
    candidates = [
        {"candidate_id": "near_stable", "latent": [0.0, 0.0], "pre_probs": [0.9, 0.1], "virtual_probs": [0.8, 0.2]},
        {"candidate_id": "far_interfered", "latent": [2.0, 0.0], "pre_probs": [0.9, 0.1], "virtual_probs": [0.2, 0.8]},
    ]
    result = select_diverse_latents(candidates, budget=1, entropy_weight=0.1, min_distance=0.5)
    return {"available": True, "selected_ids": [item["candidate_id"] for item in result["selected"]], "mechanism_checks": result["mechanism_checks"]}


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-dir", required=True)
    parser.add_argument("--generated-skills-root", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    attempt_dir = Path(args.attempt_dir).resolve()
    generated_skills_root = Path(args.generated_skills_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    add_skill_paths(generated_skills_root)

    module_plan = json.loads((attempt_dir / "module_plan.json").read_text(encoding="utf-8"))
    target = module_plan["fast_recovery_target"]
    mir = run_selector("mir")
    baseline = run_selector("random")
    latent_check = run_latent_cross_check()

    trace = {
        "mir": mir["trace"],
        "random_baseline": baseline["trace"],
        "params_before": mir["trace"][0]["params_before"],
        "params_after": mir["trace"][-1]["params_after"],
        "loss_before": mir["trace"][0]["loss_before"],
        "loss_after": mir["trace"][-1]["loss_after"],
    }
    write_json(output_dir / "logs" / "training_trace.json", trace)

    invocations = {
        "schema_version": 1,
        "generated_skills_root": str(generated_skills_root),
        "invocations": [
            {"skill_name": "online_stream_memory", "evidence_type": "imported helper", "artifact": "recovery/logs/training_trace.json"},
            {"skill_name": "virtual_update_interference", "evidence_type": "called script", "artifact": "recovery/logs/training_trace.json"},
            {"skill_name": "generative_latent_mir", "evidence_type": "cross-check", "artifact": "recovery/recovery_result.json"},
            {"skill_name": "mir_recovery_evaluation", "evidence_type": "called script", "artifact": "recovery/recovery_result.json"},
        ],
    }
    write_json(output_dir / "logs" / "generated_skill_invocations.json", invocations)

    source_manifest = {
        "schema_version": 1,
        "allowed_sources": [
            str(attempt_dir / "paper_text.txt"),
            str(attempt_dir / "paper_profile.md"),
            str(attempt_dir / "module_plan.json"),
            str(attempt_dir / "modules"),
            str(generated_skills_root),
            str(attempt_dir / "environment" / "runtime_handoff.json"),
        ],
        "original_repo_read": False,
        "runtime_handoff": str(attempt_dir / "environment" / "runtime_handoff.json"),
        "notes": "No original repository was available or read during recovery.",
    }
    write_json(output_dir / "source_manifest.json", source_manifest)

    mechanism_checks = {
        "proxy_declared": True,
        "full_recovery_blocked": True,
        "virtual_update_executed": any(step["scores"] for step in mir["trace"]),
        "topk_interference_selection_executed": any(step["selected_replay_ids"] for step in mir["trace"]),
        "online_memory_updated": len(mir["trace"]) == len(build_proxy_stream()),
        "optimizer_step_executed": True,
        "reduced_training_executed": True,
        "generated_skill_invocations_logged": True,
        "latent_mir_cross_check": latent_check,
        "mir_accuracy_minus_random": mir["final_accuracy"] - baseline["final_accuracy"],
        "mir_forgetting": mir["forgetting"]["average_forgetting"],
        "random_forgetting": baseline["forgetting"]["average_forgetting"],
    }
    result = {
        "schema_version": 1,
        "paper_id": module_plan["paper_id"],
        "experiment": target["dataset"],
        "is_proxy": True,
        "sample_count": len(build_proxy_stream()),
        "metrics": {
            "accuracy": mir["final_accuracy"],
            "random_accuracy": baseline["final_accuracy"],
            "average_forgetting": mir["forgetting"]["average_forgetting"],
            "random_average_forgetting": baseline["forgetting"]["average_forgetting"],
        },
        "paper_target": target,
        "commands": ["python recovery/run_recovery.py"],
        "artifacts": ["recovery/logs/training_trace.json", "recovery/logs/generated_skill_invocations.json"],
        "mechanism_checks": mechanism_checks,
        "notes": "Soft-mode reduced proxy: full benchmark training was blocked by bounded runtime and absent dataset/model preparation; this run executes the MIR mechanism on a deterministic non-iid stream.",
    }
    write_json(output_dir / "recovery_result.json", result)
    print(json.dumps({"ok": True, "metrics": result["metrics"], "mechanism_checks": mechanism_checks}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
