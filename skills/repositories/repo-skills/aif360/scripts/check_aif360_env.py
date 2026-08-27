#!/usr/bin/env python3
"""Check that an AIF360 Python environment can run the skill's base workflows.

This helper is self-contained and uses only synthetic in-memory data. It does
not download datasets, import optional extras as workflow dependencies, or
require the original source checkout. Optional imports are probed after the base
smoke and reported as available/missing.
"""
from __future__ import annotations

import argparse
import importlib
import json
import logging
from contextlib import contextmanager
from importlib import metadata


@contextmanager
def quiet_aif360_optional_warnings(enabled: bool = True):
    if not enabled:
        yield
        return
    logging.disable(logging.WARNING)
    try:
        yield
    finally:
        logging.disable(logging.NOTSET)


def optional_status(module_name: str) -> str:
    try:
        importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - diagnostic output only
        return f"missing-or-unavailable: {type(exc).__name__}: {exc}"
    return "available"


def run_smoke(show_import_warnings: bool = False) -> dict:
    import pandas as pd

    with quiet_aif360_optional_warnings(not show_import_warnings):
        from aif360.datasets import BinaryLabelDataset
        from aif360.metrics import BinaryLabelDatasetMetric, ClassificationMetric
        from aif360.sklearn.metrics import disparate_impact_ratio, statistical_parity_difference

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
    pred = dataset.copy()
    pred.labels = pred.labels.copy()
    pred.labels[0, 0] = 1.0
    cls_metric = ClassificationMetric(
        dataset,
        pred,
        unprivileged_groups=[{"protected": 0.0}],
        privileged_groups=[{"protected": 1.0}],
    )

    y_true = pd.Series([0, 1, 1, 1], index=pd.Index([0, 0, 1, 1], name="protected"))
    y_pred = pd.Series([1, 1, 1, 1], index=y_true.index)

    try:
        version = metadata.version("aif360")
    except metadata.PackageNotFoundError:
        version = "unknown"

    with quiet_aif360_optional_warnings(not show_import_warnings):
        optional_modules = {
            "tensorflow": optional_status("tensorflow"),
            "fairlearn": optional_status("fairlearn"),
            "torch": optional_status("torch"),
            "cvxpy": optional_status("cvxpy"),
            "BlackBoxAuditing": optional_status("BlackBoxAuditing"),
            "mlxtend": optional_status("mlxtend"),
            "ot": optional_status("ot"),
            "rpy2": optional_status("rpy2"),
        }

    return {
        "status": "ok",
        "aif360_version": version,
        "base_rate": round(float(metric.base_rate()), 6),
        "statistical_parity_difference": round(float(metric.statistical_parity_difference()), 6),
        "classification_accuracy": round(float(cls_metric.accuracy()), 6),
        "sklearn_statistical_parity_difference": round(
            float(statistical_parity_difference(y_true, y_pred, prot_attr="protected", priv_group=1)), 6
        ),
        "sklearn_disparate_impact_ratio": round(
            float(disparate_impact_ratio(y_true, y_pred, prot_attr="protected", priv_group=1)), 6
        ),
        "optional_modules": optional_modules,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a safe AIF360 base package smoke check.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output instead of key=value lines.")
    parser.add_argument("--show-import-warnings", action="store_true", help="Show optional dependency warnings from AIF360 imports.")
    args = parser.parse_args()
    result = run_smoke(show_import_warnings=args.show_import_warnings)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for sub_key, sub_value in value.items():
                    print(f"  {sub_key}: {sub_value}")
            else:
                print(f"{key}: {value}")
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
