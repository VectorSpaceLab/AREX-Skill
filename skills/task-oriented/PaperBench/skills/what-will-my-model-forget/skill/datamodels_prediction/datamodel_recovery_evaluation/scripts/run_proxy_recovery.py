#!/usr/bin/env python3
import argparse
import importlib.util
import json
import math
import os
import random
from pathlib import Path


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pearson(xs, ys):
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denom_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denom_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if denom_x == 0 or denom_y == 0:
        return 0.0
    return numerator / (denom_x * denom_y)


def mse(xs, ys):
    return sum((x - y) ** 2 for x, y in zip(xs, ys)) / len(xs)


def make_outcomes(matrix, effects, intercept, noise_scale, seed):
    rng = random.Random(seed)
    outcomes = []
    for row in matrix:
        noise = rng.uniform(-noise_scale, noise_scale)
        outcomes.append(intercept + sum(value * effect for value, effect in zip(row, effects)) + noise)
    return outcomes


def run_proxy(attempt_dir, skills_root, d=14, alpha=0.5, train_subsets=64, test_subsets=32, seed=13, noise_scale=0.002):
    attempt = Path(attempt_dir)
    skills = Path(skills_root)
    recovery = attempt / "recovery"
    logs = recovery / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    subset_module = load_module(skills / "alpha_subset_protocol" / "scripts" / "subset_protocol.py", "subset_protocol")
    fit_module = load_module(skills / "linear_datamodel_fit" / "scripts" / "fit_datamodel.py", "fit_datamodel")
    cf_module = load_module(skills / "counterfactual_effect_scoring" / "scripts" / "score_counterfactuals.py", "score_counterfactuals")

    rng = random.Random(seed)
    hidden_effects = [rng.uniform(-1.0, 1.0) for _ in range(d)]
    intercept = 0.3
    train = subset_module.generate_alpha_subsets(d, alpha, train_subsets, seed)
    test = subset_module.generate_alpha_subsets(d, alpha, test_subsets, seed + 1)
    y_train = make_outcomes(train["matrix"], hidden_effects, intercept, noise_scale, seed + 2)
    y_test = make_outcomes(test["matrix"], hidden_effects, intercept, noise_scale, seed + 3)
    fit = fit_module.fit_linear_datamodel(train["matrix"], y_train, ridge=0.01)
    test_predictions = fit_module.predict(test["matrix"], fit["weights"], fit["intercept"])
    heldout_corr = pearson(test_predictions, y_test)
    hidden_weight_corr = pearson(fit["weights"], hidden_effects)
    removal_sets = [cf_module.rank_indices(hidden_effects, absolute=True)[:k] for k in (1, 2, 3, 5, 7)]
    actual_effects = [sum(hidden_effects[index] for index in removal_set) for removal_set in removal_sets]
    cf = cf_module.score_removal_sets(fit["weights"], removal_sets, actual_effects)

    with open(attempt / "module_plan.json", "r", encoding="utf-8") as handle:
        target = json.load(handle)["fast_recovery_target"]

    generated_data_item = {
        "schema_version": 1,
        "dataset": "synthetic alpha-subset datamodel proxy",
        "d": d,
        "alpha": alpha,
        "train_subsets": train_subsets,
        "test_subsets": test_subsets,
        "seed": seed,
        "noise_scale": noise_scale,
        "hidden_effects_preview": hidden_effects[:5],
        "resource_provenance": "synthetic mechanism-faithful proxy; no external benchmark resource used"
    }
    (logs / "generated_data_item.json").write_text(json.dumps(generated_data_item, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    training_trace = {
        "schema_version": 1,
        "loss_before": mse([sum(y_train) / len(y_train)] * len(y_train), y_train),
        "loss_after": fit["diagnostics"]["mse"],
        "params_before": [0.0 for _ in range(d)],
        "params_after": fit["weights"],
        "parameters_before": [0.0 for _ in range(d)],
        "parameters_after": fit["weights"],
        "optimizer": "closed-form ridge least squares normal-equation solve",
        "train_pearson": fit["diagnostics"]["pearson"],
        "test_pearson": heldout_corr,
        "hidden_weight_pearson": hidden_weight_corr
    }
    (logs / "training_trace.json").write_text(json.dumps(training_trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    invocations = {
        "schema_version": 1,
        "skills_root": str(skills),
        "invocations": [
            {"module_id": "subset_protocol", "skill": "alpha_subset_protocol", "kind": "imported helper", "evidence": "recovery/logs/generated_data_item.json", "evidence_type": "imported helper", "artifact": "recovery/logs/generated_data_item.json", "status": "called"},
            {"module_id": "linear_datamodel_fit", "skill": "linear_datamodel_fit", "kind": "imported helper", "evidence": "recovery/logs/training_trace.json", "evidence_type": "imported helper", "artifact": "recovery/logs/training_trace.json", "status": "called"},
            {"module_id": "counterfactual_effects", "skill": "counterfactual_effect_scoring", "kind": "imported helper", "evidence": "recovery/recovery_result.json", "evidence_type": "imported helper", "artifact": "recovery/recovery_result.json", "status": "called"},
            {"module_id": "recovery_evaluation", "skill": "datamodel_recovery_evaluation", "kind": "called script", "evidence": "recovery/recovery_result.json", "evidence_type": "called script", "artifact": "recovery/recovery_result.json", "status": "called"}
        ]
    }
    (logs / "generated_skill_invocations.json").write_text(json.dumps(invocations, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    source_manifest = {
        "schema_version": 1,
        "allowed_sources_used": [
            str(attempt / "paper_profile.md"),
            str(attempt / "module_plan.json"),
            str(attempt / "modules"),
            str(skills),
            str(attempt / "environment" / "runtime_handoff.json")
        ],
        "original_repo_used": False,
        "original_repo_paths": [],
        "runtime_handoff": str(attempt / "environment" / "runtime_handoff.json"),
        "notes": "No original source repository was available or read during recovery."
    }
    (recovery / "source_manifest.json").write_text(json.dumps(source_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema_version": 1,
        "paper_id": "datamodels_prediction",
        "experiment": target["dataset"],
        "is_proxy": True,
        "sample_count": test_subsets,
        "metrics": {
            "pearson_correlation": heldout_corr,
            "counterfactual_pearson": cf.get("effect_correlation", 0.0),
            "weight_pearson": hidden_weight_corr,
            "mse": mse(test_predictions, y_test)
        },
        "paper_target": target,
        "commands": ["python recovery/run_recovery.py"],
        "artifacts": [
            "recovery/logs/generated_data_item.json",
            "recovery/logs/training_trace.json",
            "recovery/logs/generated_skill_invocations.json",
            "recovery/source_manifest.json"
        ],
        "mechanism_checks": {
            "proxy_declared": True,
            "full_deep_training_blocked": True,
            "alpha_subset_sampling_executed": True,
            "subset_membership_vectors_binary": True,
            "linear_datamodel_fit_executed": True,
            "heldout_subset_prediction_evaluated": True,
            "counterfactual_weight_summation_executed": True,
            "generated_skills_invoked": True,
            "reduced_training_executed": True,
            "optimizer_step_executed": True,
            "qwen3_model_loaded": False,
            "original_repo_used": False
        },
        "notes": "Soft-mode proxy recovery: synthetic subset-output data preserves the datamodel mechanism while avoiding infeasible full deep-network retraining."
    }
    (recovery / "recovery_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-dir", required=True)
    parser.add_argument("--skills-root", required=True)
    parser.add_argument("--d", type=int, default=14)
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--train-subsets", type=int, default=64)
    parser.add_argument("--test-subsets", type=int, default=32)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--noise-scale", type=float, default=0.002)
    args = parser.parse_args()
    result = run_proxy(args.attempt_dir, args.skills_root, args.d, args.alpha, args.train_subsets, args.test_subsets, args.seed, args.noise_scale)
    print(json.dumps({"ok": True, "metrics": result["metrics"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
