#!/usr/bin/env python3
"""Validation utilities for agreement-on-the-line prediction tables."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate_prediction_table(table: dict, require_ood_labels: bool = False) -> dict:
    models = table.get("models")
    if not isinstance(models, list) or len(models) < 3:
        raise ValueError("ALine-D requires at least three models")
    if len(set(models)) != len(models):
        raise ValueError("model identifiers must be unique")

    id_labels = table.get("id_labels")
    if not isinstance(id_labels, list) or not id_labels:
        raise ValueError("id_labels must be a non-empty list")

    id_predictions = table.get("id_predictions")
    ood_predictions = table.get("ood_predictions")
    if not isinstance(id_predictions, dict) or not isinstance(ood_predictions, dict):
        raise ValueError("id_predictions and ood_predictions must be objects keyed by model id")

    ood_count = None
    for model in models:
        if model not in id_predictions or model not in ood_predictions:
            raise ValueError(f"missing predictions for model {model}")
        if len(id_predictions[model]) != len(id_labels):
            raise ValueError(f"ID prediction length mismatch for {model}")
        if ood_count is None:
            ood_count = len(ood_predictions[model])
            if ood_count == 0:
                raise ValueError("OOD predictions must be non-empty")
        elif len(ood_predictions[model]) != ood_count:
            raise ValueError(f"OOD prediction length mismatch for {model}")

    ood_labels = table.get("ood_labels")
    has_ood_labels = isinstance(ood_labels, list)
    if require_ood_labels and not has_ood_labels:
        raise ValueError("ood_labels are required for evaluation")
    if has_ood_labels and len(ood_labels) != ood_count:
        raise ValueError("OOD label length mismatch")

    return {
        "models": list(models),
        "id_labels": list(id_labels),
        "id_predictions": {model: list(id_predictions[model]) for model in models},
        "ood_predictions": {model: list(ood_predictions[model]) for model in models},
        "evaluation_only": {"ood_labels": list(ood_labels) if has_ood_labels else None},
        "metadata": {
            "model_count": len(models),
            "id_sample_count": len(id_labels),
            "ood_sample_count": ood_count,
            "has_evaluation_ood_labels": has_ood_labels,
            "ood_labels_allowed_for_estimator": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--output", required=True)
    parser.add_argument("--require-ood-labels", action="store_true")
    args = parser.parse_args()
    table = json.loads(Path(args.input).read_text())
    normalized = validate_prediction_table(table, args.require_ood_labels)
    Path(args.output).write_text(json.dumps(normalized, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
