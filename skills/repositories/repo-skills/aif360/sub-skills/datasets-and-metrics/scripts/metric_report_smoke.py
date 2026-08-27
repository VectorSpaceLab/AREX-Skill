#!/usr/bin/env python3
"""Synthetic AIF360 legacy dataset/metric smoke.

Builds an in-memory BinaryLabelDataset, computes BinaryLabelDatasetMetric and
ClassificationMetric values, and prints a concise report. It never reads raw
benchmark data and never uses network access.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Iterable

# Keep optional algorithm import warnings/noise out of the smoke report.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
logging.basicConfig(level=logging.ERROR)
logging.getLogger().setLevel(logging.ERROR)

import numpy as np
import pandas as pd


def _round_float(value: Any, digits: int = 6) -> float:
    """Convert numpy scalars to finite rounded Python floats for JSON output."""
    as_float = float(value)
    if not math.isfinite(as_float):
        raise ValueError(f"Metric produced a non-finite value: {as_float!r}")
    return round(as_float, digits)


def _build_datasets():
    """Create a tiny numeric BinaryLabelDataset and a prediction copy."""
    from aif360.datasets import BinaryLabelDataset

    df = pd.DataFrame(
        {
            "risk_score": [0.10, 0.40, 0.75, 0.20, 0.90, 0.30, 0.65, 0.15],
            "sex": [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0],
            "approved": [1.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        }
    )

    dataset = BinaryLabelDataset(
        df=df,
        label_names=["approved"],
        protected_attribute_names=["sex"],
        favorable_label=1.0,
        unfavorable_label=0.0,
    )

    classified = dataset.copy(True)
    classified.labels = np.array(
        [[1.0], [0.0], [1.0], [0.0], [1.0], [0.0], [1.0], [0.0]],
        dtype=float,
    )
    classified.scores = np.array(
        [[0.90], [0.35], [0.70], [0.20], [0.85], [0.30], [0.65], [0.15]],
        dtype=float,
    )

    privileged_groups = [{"sex": 1.0}]
    unprivileged_groups = [{"sex": 0.0}]
    return dataset, classified, unprivileged_groups, privileged_groups


def _aif360_version() -> str:
    try:
        return version("aif360")
    except PackageNotFoundError:
        import aif360

        return getattr(aif360, "__version__", "unknown")


def compute_report() -> dict[str, Any]:
    """Compute the synthetic dataset and classification metric report."""
    from aif360.metrics import BinaryLabelDatasetMetric, ClassificationMetric

    dataset, classified, unprivileged_groups, privileged_groups = _build_datasets()

    dataset_metric = BinaryLabelDatasetMetric(
        dataset,
        unprivileged_groups=unprivileged_groups,
        privileged_groups=privileged_groups,
    )
    classification_metric = ClassificationMetric(
        dataset,
        classified,
        unprivileged_groups=unprivileged_groups,
        privileged_groups=privileged_groups,
    )

    return {
        "aif360_version": _aif360_version(),
        "dataset": {
            "rows": int(dataset.features.shape[0]),
            "feature_names": list(dataset.feature_names),
            "label_names": list(dataset.label_names),
            "protected_attribute_names": list(dataset.protected_attribute_names),
            "privileged_groups": privileged_groups,
            "unprivileged_groups": unprivileged_groups,
        },
        "binary_label_dataset_metric": {
            "base_rate": _round_float(dataset_metric.base_rate()),
            "base_rate_unprivileged": _round_float(dataset_metric.base_rate(privileged=False)),
            "base_rate_privileged": _round_float(dataset_metric.base_rate(privileged=True)),
            "statistical_parity_difference": _round_float(
                dataset_metric.statistical_parity_difference()
            ),
            "disparate_impact": _round_float(dataset_metric.disparate_impact()),
        },
        "classification_metric": {
            "true_positive_rate": _round_float(classification_metric.true_positive_rate()),
            "true_negative_rate": _round_float(classification_metric.true_negative_rate()),
            "balanced_accuracy": _round_float(
                0.5
                * (
                    classification_metric.true_positive_rate()
                    + classification_metric.true_negative_rate()
                )
            ),
            "statistical_parity_difference": _round_float(
                classification_metric.statistical_parity_difference()
            ),
            "disparate_impact": _round_float(classification_metric.disparate_impact()),
            "average_odds_difference": _round_float(
                classification_metric.average_odds_difference()
            ),
            "equal_opportunity_difference": _round_float(
                classification_metric.equal_opportunity_difference()
            ),
            "theil_index": _round_float(classification_metric.theil_index()),
        },
    }


def _flatten(prefix: str, value: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            new_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield from _flatten(new_prefix, child)
    else:
        yield prefix, value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run a no-data AIF360 BinaryLabelDatasetMetric and "
            "ClassificationMetric smoke report."
        )
    )
    parser.add_argument(
        "--format",
        choices=("json", "lines"),
        default="json",
        help="Output format. Default: json.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output with indentation.",
    )
    args = parser.parse_args(argv)

    report = compute_report()
    if args.format == "lines":
        for key, value in _flatten("", report):
            print(f"{key}={value}")
    else:
        print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
