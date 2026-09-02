#!/usr/bin/env python3
"""ImageNet-C corruption metric equations."""
from __future__ import annotations

import argparse
import json
from typing import Dict, Mapping

SeverityTable = Mapping[str, Mapping[str, float]]


def _severity_keys(table: Mapping[str, float]) -> set[str]:
    return {str(key) for key in table.keys()}


def validate_error_tables(model_errors: SeverityTable, baseline_errors: SeverityTable) -> list[str]:
    errors = []
    if set(model_errors.keys()) != set(baseline_errors.keys()):
        errors.append("model and baseline corruption keys differ")
    for corruption in sorted(set(model_errors.keys()) & set(baseline_errors.keys())):
        model_keys = _severity_keys(model_errors[corruption])
        baseline_keys = _severity_keys(baseline_errors[corruption])
        expected = {"1", "2", "3", "4", "5"}
        if model_keys != expected:
            errors.append(f"{corruption}: model severities must be 1..5")
        if baseline_keys != expected:
            errors.append(f"{corruption}: baseline severities must be 1..5")
    return errors


def _sum_severities(table: Mapping[str, float]) -> float:
    return sum(float(table[str(severity)]) for severity in range(1, 6))


def compute_corruption_metrics(
    model_errors: SeverityTable,
    baseline_errors: SeverityTable,
    model_clean_error: float,
    baseline_clean_error: float,
    scale: float = 100.0,
) -> dict:
    validation_errors = validate_error_tables(model_errors, baseline_errors)
    if validation_errors:
        raise ValueError("; ".join(validation_errors))

    ce_by_corruption: Dict[str, float] = {}
    relative_ce_by_corruption: Dict[str, float] = {}
    for corruption in sorted(model_errors.keys()):
        model_sum = _sum_severities(model_errors[corruption])
        baseline_sum = _sum_severities(baseline_errors[corruption])
        if baseline_sum == 0.0:
            raise ValueError(f"{corruption}: baseline CE denominator is zero")
        ce_by_corruption[corruption] = scale * model_sum / baseline_sum

        model_relative_sum = sum(float(model_errors[corruption][str(severity)]) - model_clean_error for severity in range(1, 6))
        baseline_relative_sum = sum(float(baseline_errors[corruption][str(severity)]) - baseline_clean_error for severity in range(1, 6))
        if baseline_relative_sum == 0.0:
            raise ValueError(f"{corruption}: baseline relative CE denominator is zero")
        relative_ce_by_corruption[corruption] = scale * model_relative_sum / baseline_relative_sum

    mce = sum(ce_by_corruption.values()) / len(ce_by_corruption)
    relative_mce = sum(relative_ce_by_corruption.values()) / len(relative_ce_by_corruption)
    return {
        "ce_by_corruption": ce_by_corruption,
        "mce": mce,
        "relative_ce_by_corruption": relative_ce_by_corruption,
        "relative_mce": relative_mce,
        "scale": scale,
        "validation": {"ok": True, "errors": []},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="JSON with model_errors, baseline_errors, model_clean_error, baseline_clean_error")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.input, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    result = compute_corruption_metrics(
        payload["model_errors"],
        payload["baseline_errors"],
        float(payload["model_clean_error"]),
        float(payload["baseline_clean_error"]),
        float(payload.get("scale", 100.0)),
    )
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
