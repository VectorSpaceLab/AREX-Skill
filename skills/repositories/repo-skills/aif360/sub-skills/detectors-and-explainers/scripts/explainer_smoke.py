#!/usr/bin/env python3
"""Run a safe MetricTextExplainer/MetricJSONExplainer smoke check."""
from __future__ import annotations

import argparse
import json
import logging
from typing import Any

import pandas as pd


def to_builtin(value: Any) -> Any:
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def run_explainer(show_import_warnings: bool = False) -> dict:
    if not show_import_warnings:
        logging.disable(logging.WARNING)
    try:
        from aif360.datasets import BinaryLabelDataset
        from aif360.explainers import MetricJSONExplainer, MetricTextExplainer
        from aif360.metrics import BinaryLabelDatasetMetric
    finally:
        if not show_import_warnings:
            logging.disable(logging.NOTSET)

    dataset = BinaryLabelDataset(
        df=pd.DataFrame(
            {
                "feature": [0.0, 1.0, 0.5, 1.5],
                "protected": [0.0, 0.0, 1.0, 1.0],
                "label": [0.0, 1.0, 1.0, 1.0],
            }
        ),
        label_names=["label"],
        protected_attribute_names=["protected"],
        favorable_label=1.0,
        unfavorable_label=0.0,
    )
    metric = BinaryLabelDatasetMetric(
        dataset,
        unprivileged_groups=[{"protected": 0.0}],
        privileged_groups=[{"protected": 1.0}],
    )
    text = MetricTextExplainer(metric).statistical_parity_difference()
    json_payload = MetricJSONExplainer(metric).statistical_parity_difference()
    parsed = json.loads(json_payload)
    return {
        "status": "ok",
        "text_contains_metric": "Statistical parity difference" in text,
        "json_metric": parsed.get("metric"),
        "json_keys": sorted(parsed.keys()),
        "json_message_prefix": str(parsed.get("message", ""))[:120],
        "json_value": to_builtin(parsed.get("value")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a deterministic AIF360 metric explainer smoke check.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output instead of key=value lines.")
    parser.add_argument("--show-import-warnings", action="store_true", help="Show optional dependency import warnings.")
    args = parser.parse_args()
    result = run_explainer(show_import_warnings=args.show_import_warnings)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0 if result["status"] == "ok" and result["text_contains_metric"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
