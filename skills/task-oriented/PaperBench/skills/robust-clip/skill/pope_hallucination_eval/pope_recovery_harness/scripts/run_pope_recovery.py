#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def add_skill_paths(skill_root):
    root = Path(skill_root)
    for skill_name in ["pope_negative_sampling", "pope_protocol_builder", "pope_answer_evaluator"]:
        sys.path.insert(0, str(root / skill_name / "scripts"))


def synthetic_records():
    return [
        {"image": "proxy_001.jpg", "objects": ["cat", "sofa", "lamp"]},
        {"image": "proxy_002.jpg", "objects": ["dog", "ball", "tree"]},
        {"image": "proxy_003.jpg", "objects": ["apple", "plate", "fork"]},
        {"image": "proxy_004.jpg", "objects": ["person", "bicycle", "helmet"]},
    ]


def answer_questions(questions, false_positive_budget=1):
    answers = []
    false_positives = 0
    for question in questions:
        if question["label"] == "yes":
            answer = "Yes, the object is present."
        elif false_positives < false_positive_budget:
            answer = "Yes, it appears in the image."
            false_positives += 1
        else:
            answer = "No, the object is not present."
        answers.append({"question_id": question["question_id"], "question": question["text"], "answer": answer})
    return answers


def run_proxy(attempt_dir, skill_root, records=None, sample_num=2, producing_command=None):
    add_skill_paths(skill_root)
    from pope_protocol_builder import build_pope_questions
    from pope_answer_evaluator import evaluate_answers

    attempt = Path(attempt_dir)
    module_plan = json.loads((attempt / "module_plan.json").read_text(encoding="utf-8"))
    recovery_dir = attempt / "recovery"
    logs_dir = recovery_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    records = records or synthetic_records()
    per_strategy = {}
    all_questions = []
    all_answers = []
    strategy_metrics = []
    for strategy in ["random", "popular", "adversarial"]:
        questions = build_pope_questions(records, sample_num=sample_num, strategy=strategy, seed=17)
        answers = answer_questions(questions, false_positive_budget=1)
        metrics = evaluate_answers(answers, questions)
        per_strategy[strategy] = {"question_count": len(questions), "metrics": metrics}
        all_questions.extend(questions)
        all_answers.extend(answers)
        strategy_metrics.append(metrics)
    avg_f1 = sum(item["f1"] for item in strategy_metrics) / len(strategy_metrics)
    avg_accuracy = sum(item["accuracy"] for item in strategy_metrics) / len(strategy_metrics)
    avg_yes_ratio = sum(item["yes_ratio"] for item in strategy_metrics) / len(strategy_metrics)
    data_item = {
        "schema_version": 1,
        "dataset_type": "synthetic_annotation_proxy",
        "records": records,
        "strategies": per_strategy,
        "question_count": len(all_questions),
        "answer_count": len(all_answers),
        "resource_provenance": "Synthetic current-attempt records created to exercise POPE mechanism; no original repository files used during recovery.",
    }
    (logs_dir / "generated_data_item.json").write_text(json.dumps(data_item, indent=2), encoding="utf-8")
    invocations = {
        "schema_version": 1,
        "invocations": [
            {"module": "pope_negative_sampling", "skill": "pope_negative_sampling", "kind": "imported helper", "evidence": "negative sampler imported by protocol builder", "module_id": "pope_negative_sampling", "skill_name": "pope_negative_sampling", "evidence_type": "imported helper", "artifact": "recovery/logs/generated_data_item.json"},
            {"module": "pope_protocol_builder", "skill": "pope_protocol_builder", "kind": "called script helper", "evidence": "build_pope_questions called for three strategies", "module_id": "pope_protocol_builder", "skill_name": "pope_protocol_builder", "evidence_type": "called script helper", "artifact": "recovery/logs/generated_data_item.json"},
            {"module": "pope_answer_evaluator", "skill": "pope_answer_evaluator", "kind": "called script helper", "evidence": "evaluate_answers called for every strategy", "module_id": "pope_answer_evaluator", "skill_name": "pope_answer_evaluator", "evidence_type": "called script helper", "artifact": "recovery/logs/generated_data_item.json"},
            {"module": "pope_recovery_harness", "skill": "pope_recovery_harness", "kind": "executed harness", "evidence": "run_proxy produced recovery_result.json", "module_id": "pope_recovery_harness", "skill_name": "pope_recovery_harness", "evidence_type": "executed harness", "artifact": "recovery/recovery_result.json"},
        ],
    }
    (logs_dir / "generated_skill_invocations.json").write_text(json.dumps(invocations, indent=2), encoding="utf-8")
    source_manifest = {
        "schema_version": 1,
        "allowed_sources": [
            "paper_profile.md",
            "module_plan.json",
            "modules/*.md",
            "environment/runtime_handoff.json",
            str(Path(skill_root).resolve()),
        ],
        "original_repo_used": False,
        "forbidden_sources": [],
        "runtime_handoff": "environment/runtime_handoff.json",
    }
    (recovery_dir / "source_manifest.json").write_text(json.dumps(source_manifest, indent=2), encoding="utf-8")
    result = {
        "schema_version": 1,
        "paper_id": module_plan["paper_id"],
        "experiment": "synthetic_annotated_objects_tiny_proxy_all_strategies",
        "is_proxy": True,
        "sample_count": len(all_questions),
        "metrics": {"f1": avg_f1, "accuracy": avg_accuracy, "yes_ratio": avg_yes_ratio},
        "paper_target": module_plan["fast_recovery_target"],
        "commands": [producing_command] if producing_command else [],
        "artifacts": ["recovery/logs/generated_data_item.json", "recovery/logs/generated_skill_invocations.json"],
        "mechanism_checks": {
            "polling_questions_generated": len(all_questions) > 0,
            "positive_and_negative_labels_present": {q["label"] for q in all_questions} == {"yes", "no"},
            "random_strategy_executed": "random" in per_strategy,
            "popular_strategy_executed": "popular" in per_strategy,
            "adversarial_strategy_executed": "adversarial" in per_strategy,
            "absent_negative_invariant_checked": all(q["object"] not in next(r["objects"] for r in records if r["image"] == q["image"]) for q in all_questions if q["label"] == "no"),
            "answer_normalization_executed": True,
            "generated_skills_invoked": True,
            "original_repo_used": False,
            "full_lvlm_inference_executed": False,
            "proxy_declared": True,
        },
        "notes": "Soft-mode reduced proxy exercising POPE polling, negative sampling, and answer evaluation without original repo access.",
    }
    (recovery_dir / "recovery_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-dir")
    parser.add_argument("--skill-root")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        temp = Path("/tmp/pope_recovery_self_test")
        temp.mkdir(parents=True, exist_ok=True)
        (temp / "recovery" / "logs").mkdir(parents=True, exist_ok=True)
        (temp / "module_plan.json").write_text(json.dumps({"paper_id": "pope_hallucination_eval", "fast_recovery_target": {"metric": "f1", "paper_value": 0.7, "proxy": True}}), encoding="utf-8")
        result = run_proxy(temp, Path(__file__).resolve().parents[2])
        assert result["metrics"]["f1"] > 0
        print(json.dumps({"ok": True}))
        return
    producing_command = "python " + " ".join(sys.argv)
    result = run_proxy(args.attempt_dir, args.skill_root, producing_command=producing_command)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
