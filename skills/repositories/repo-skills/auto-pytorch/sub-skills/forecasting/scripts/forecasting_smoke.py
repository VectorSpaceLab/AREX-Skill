#!/usr/bin/env python3
"""Tiny forecasting smoke check for Auto-PyTorch.

This script validates the forecasting input validator on a synthetic fixture
without running a full search.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from autoPyTorch.data.time_series_forecasting_validator import TimeSeriesForecastingInputValidator


def _uni_variant_report() -> Dict[str, Any]:
    validator = TimeSeriesForecastingInputValidator(is_classification=False)
    y_train = [[0.0, 1.0, 2.0, 3.0], [10.0, 11.0, 12.0, 13.0]]
    y_test = [[4.0, 5.0], [14.0, 15.0]]
    validator.fit(X_train=None, y_train=y_train, X_test=None, y_test=y_test)
    x_transformed, y_transformed, sequence_lengths = validator.transform(None, y_train)
    return {
        "variant": "uni",
        "is_uni_variant": validator._is_uni_variant,
        "start_times": [str(ts) for ts in validator.start_times or []],
        "sequence_lengths": sequence_lengths.tolist(),
        "feature_names": validator.feature_names,
        "feature_shapes": validator.feature_shapes,
        "x_transformed": None if x_transformed is None else list(x_transformed.shape),
        "y_transformed": None if y_transformed is None else list(y_transformed.shape),
    }


def _multi_variant_report() -> Dict[str, Any]:
    validator = TimeSeriesForecastingInputValidator(is_classification=False)
    x_train: List[pd.DataFrame] = [
        pd.DataFrame(
            {
                "feat_num": [1.0, 2.0, 3.0, 4.0],
                "feat_cat": pd.Series(["a", "a", "b", "b"], dtype="category"),
            }
        ),
        pd.DataFrame(
            {
                "feat_num": [5.0, 6.0, 7.0, 8.0],
                "feat_cat": pd.Series(["a", "b", "b", "a"], dtype="category"),
            }
        ),
    ]
    y_train = [[0.0, 1.0, 2.0, 3.0], [10.0, 11.0, 12.0, 13.0]]
    start_times = [pd.Timestamp("2000-01-01"), pd.Timestamp("2001-01-01")]
    validator.fit(X_train=x_train, y_train=y_train, start_times=start_times)
    x_transformed, y_transformed, sequence_lengths = validator.transform(x_train, y_train)
    return {
        "variant": "multi",
        "is_uni_variant": validator._is_uni_variant,
        "start_times": [str(ts) for ts in validator.start_times or []],
        "sequence_lengths": sequence_lengths.tolist(),
        "feature_names": validator.feature_names,
        "feature_shapes": validator.feature_shapes,
        "x_transformed": None if x_transformed is None else list(x_transformed.shape),
        "y_transformed": None if y_transformed is None else list(y_transformed.shape),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    parser.add_argument(
        "--mode",
        choices=("uni", "multi", "both"),
        default="both",
        help="Which synthetic forecasting path to check.",
    )
    args = parser.parse_args()

    payload: Dict[str, Any] = {}
    if args.mode in {"uni", "both"}:
        payload["uni"] = _uni_variant_report()
    if args.mode in {"multi", "both"}:
        payload["multi"] = _multi_variant_report()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for name, report in payload.items():
            print(f"[{name}] lengths={report['sequence_lengths']} features={report['feature_names']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
