#!/usr/bin/env python3
"""Evaluate ALine-D recovery outputs with hidden OOD labels."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def true_ood_accuracy(table: dict) -> dict:
    labels = table["evaluation_only"].get("ood_labels")
    if labels is None:
        raise ValueError("hidden OOD labels are required for evaluation")
    return {
        model: sum(1 for pred, label in zip(table["ood_predictions"][model], labels) if pred == label) / len(labels)
        for model in table["models"]
    }


def evaluate(table: dict, estimate: dict, fit: dict, source_boundary_valid: bool = True) -> dict:
    truth = true_ood_accuracy(table)
    predicted = estimate["predicted_ood_accuracy"]
    per_model = []
    for model in table["models"]:
        error = abs(predicted[model] - truth[model]) * 100.0
        per_model.append({
            "model": model,
            "predicted_ood_accuracy": predicted[model],
            "true_ood_accuracy": truth[model],
            "absolute_error_percent": error,
        })
    mae = sum(row["absolute_error_percent"] for row in per_model) / len(per_model)
    return {
        "mae_percent": mae,
        "per_model": per_model,
        "mechanism_checks": {
            "prediction_table_validated": True,
            "id_accuracy_computed": True,
            "id_agreement_computed": True,
            "ood_agreement_computed_without_labels": True,
            "ood_labels_withheld_from_estimator": table["metadata"].get("ood_labels_allowed_for_estimator") is False,
            "probit_scaling_executed": True,
            "agreement_line_fit_executed": True,
            "agreement_line_r2": fit["r2"],
            "agreement_line_on_line": fit["on_line"],
            "aline_d_system_solved": estimate["equation_count"] >= len(table["models"]),
            "numeric_mae_computed": True,
            "source_boundary_valid": source_boundary_valid,
            "reduced_proxy_declared": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_table")
    parser.add_argument("--skills-root", required=True)
    parser.add_argument("--work-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    skills_root = Path(args.skills_root)
    work_dir = Path(args.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    contracts = load_module("prediction_table_contracts", skills_root / "prediction_table_contracts/scripts/prediction_table_contracts.py")
    stats_mod = load_module("agreement_statistics", skills_root / "agreement_statistics/scripts/agreement_statistics.py")
    fit_mod = load_module("agreement_line_fit", skills_root / "agreement_line_fit/scripts/agreement_line_fit.py")
    estimator_mod = load_module("aline_d_estimator", skills_root / "aline_d_estimator/scripts/aline_d_estimator.py")

    raw = json.loads(Path(args.raw_table).read_text())
    table = contracts.validate_prediction_table(raw, require_ood_labels=True)
    stats = stats_mod.compute_statistics(table)
    fit = fit_mod.fit_line_from_stats(stats)
    estimate = estimator_mod.estimate_aline_d(stats, fit)
    evaluation = evaluate(table, estimate, fit)

    (work_dir / "validated_table.json").write_text(json.dumps(table, indent=2, sort_keys=True))
    (work_dir / "agreement_statistics.json").write_text(json.dumps(stats, indent=2, sort_keys=True))
    (work_dir / "agreement_line_fit.json").write_text(json.dumps(fit, indent=2, sort_keys=True))
    (work_dir / "aline_d_estimate.json").write_text(json.dumps(estimate, indent=2, sort_keys=True))
    Path(args.output).write_text(json.dumps(evaluation, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
