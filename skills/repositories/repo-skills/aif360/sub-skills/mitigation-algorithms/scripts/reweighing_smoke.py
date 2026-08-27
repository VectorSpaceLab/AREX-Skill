#!/usr/bin/env python3
"""Safe synthetic AIF360 Reweighing smoke.

This script creates an in-memory BinaryLabelDataset, runs Reweighing, and
prints before/after weighted fairness metrics. It performs no downloads, raw
file reads, model training, or network operations.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import logging
import math
from typing import Any, Dict

import numpy as np
import pandas as pd


UNPRIVILEGED_GROUPS = [{"group": 0.0}]
PRIVILEGED_GROUPS = [{"group": 1.0}]


@contextmanager
def quiet_optional_import_warnings():
    """Suppress unrelated optional-extra logging during AIF360 imports."""
    root_logger = logging.getLogger()
    previous_level = root_logger.level
    root_logger.setLevel(max(previous_level, logging.ERROR))
    try:
        yield
    finally:
        root_logger.setLevel(previous_level)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def build_dataset(replicates: int):
    """Build a tiny biased dataset with all group/label buckets populated."""
    with quiet_optional_import_warnings():
        from aif360.datasets import BinaryLabelDataset

    # group=0 is unprivileged with a lower favorable-label rate; group=1 is
    # privileged with a higher favorable-label rate. Counts are intentionally
    # nonzero in all four buckets so Reweighing has finite ratios.
    specs = [
        (0.0, 1.0, 2),
        (0.0, 0.0, 6),
        (1.0, 1.0, 6),
        (1.0, 0.0, 2),
    ]
    rows = []
    for group_value, label_value, base_count in specs:
        for idx in range(base_count * replicates):
            rows.append(
                {
                    "group": group_value,
                    "feature": float(idx) / max(1, base_count * replicates)
                    + group_value,
                    "label": label_value,
                }
            )
    df = pd.DataFrame(rows, columns=["feature", "group", "label"])
    return BinaryLabelDataset(
        df=df,
        label_names=["label"],
        protected_attribute_names=["group"],
        favorable_label=1.0,
        unfavorable_label=0.0,
    )


def summarize(dataset) -> Dict[str, float]:
    with quiet_optional_import_warnings():
        from aif360.metrics import BinaryLabelDatasetMetric

    metric = BinaryLabelDatasetMetric(
        dataset,
        unprivileged_groups=UNPRIVILEGED_GROUPS,
        privileged_groups=PRIVILEGED_GROUPS,
    )
    weights = np.asarray(dataset.instance_weights, dtype=float)
    return {
        "rows": float(dataset.features.shape[0]),
        "instance_weight_sum": float(weights.sum()),
        "unprivileged_base_rate": float(metric.base_rate(privileged=False)),
        "privileged_base_rate": float(metric.base_rate(privileged=True)),
        "mean_difference": float(metric.mean_difference()),
        "disparate_impact": float(metric.disparate_impact()),
    }


def finite_summary(summary: Dict[str, float]) -> bool:
    return all(math.isfinite(value) for value in summary.values())


def run_smoke(replicates: int, tolerance: float) -> Dict[str, Any]:
    original = build_dataset(replicates=replicates)
    before = summarize(original)

    with quiet_optional_import_warnings():
        from aif360.algorithms.preprocessing.reweighing import Reweighing

    reweigher = Reweighing(
        unprivileged_groups=UNPRIVILEGED_GROUPS,
        privileged_groups=PRIVILEGED_GROUPS,
    )
    transformed = reweigher.fit_transform(original)
    after = summarize(transformed)

    checks = {
        "finite_before": finite_summary(before),
        "finite_after": finite_summary(after),
        "weight_sum_preserved": math.isclose(
            before["instance_weight_sum"],
            after["instance_weight_sum"],
            rel_tol=tolerance,
            abs_tol=tolerance,
        ),
        "weighted_mean_difference_near_zero": abs(after["mean_difference"])
        <= tolerance,
        "weighted_disparate_impact_near_one": math.isclose(
            after["disparate_impact"], 1.0, rel_tol=tolerance, abs_tol=tolerance
        ),
    }
    return {"before": before, "after": after, "checks": checks}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a safe synthetic AIF360 Reweighing smoke with no downloads "
            "or model training."
        )
    )
    parser.add_argument(
        "--replicates",
        type=positive_int,
        default=1,
        help="positive replication factor for the 16-row synthetic pattern",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=1e-9,
        help="numeric tolerance for weight and metric checks",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of a text summary",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.tolerance <= 0:
        raise SystemExit("--tolerance must be positive")

    result = run_smoke(replicates=args.replicates, tolerance=args.tolerance)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("AIF360 Reweighing synthetic smoke")
        print("Before:")
        for key, value in result["before"].items():
            print(f"  {key}: {value:.12g}")
        print("After:")
        for key, value in result["after"].items():
            print(f"  {key}: {value:.12g}")
        print("Checks:")
        for key, value in result["checks"].items():
            print(f"  {key}: {value}")

    return 0 if all(result["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
