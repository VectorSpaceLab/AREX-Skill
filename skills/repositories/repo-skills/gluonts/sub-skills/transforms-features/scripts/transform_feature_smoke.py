#!/usr/bin/env python3
"""Smoke-test GluonTS transforms, time features, lags, and splitters.

This script imports the installed ``gluonts`` package only. It builds a tiny
in-memory dataset with a NaN target value, adds an observed-values indicator and
time features, creates one prediction instance, asserts the resulting fields and
shapes, and prints a short success summary.
"""

from __future__ import annotations

import argparse
import warnings
from typing import Sequence

import numpy as np

warnings.filterwarnings(
    "ignore",
    message=r"Using `json`-module for json-handling.*",
    category=UserWarning,
)

from gluonts.dataset.common import ListDataset
from gluonts.dataset.field_names import FieldName
from gluonts.time_feature import (
    Constant,
    get_lags_for_frequency,
    time_features_from_frequency_str,
)
from gluonts.transform import (
    AddObservedValuesIndicator,
    AddTimeFeatures,
    AsNumpyArray,
    Chain,
    InstanceSplitter,
    TestSplitSampler,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic GluonTS transform/time-feature smoke test "
            "against the installed package."
        )
    )
    parser.add_argument(
        "--freq",
        default="D",
        help="Pandas/GluonTS frequency string for the tiny dataset (default: D).",
    )
    parser.add_argument(
        "--context-length",
        type=int,
        default=4,
        help="Past window length used by InstanceSplitter (default: 4).",
    )
    parser.add_argument(
        "--prediction-length",
        type=int,
        default=2,
        help="Future horizon for time features and splitting (default: 2).",
    )
    return parser


def make_dataset(freq: str) -> ListDataset:
    # The NaN is inside the final context window selected by TestSplitSampler,
    # so both imputation and observed-value splitting are asserted below.
    target = [1.0, 2.0, 3.0, 4.0, 5.0, float("nan"), 7.0, 8.0]
    return ListDataset([{"start": "2024-01-01", "target": target}], freq=freq)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.context_length <= 0:
        raise SystemExit("--context-length must be positive")
    if args.prediction_length <= 0:
        raise SystemExit("--prediction-length must be positive")
    if args.context_length > 8:
        raise SystemExit("--context-length must be <= 8 for the built-in fixture")

    time_features = time_features_from_frequency_str(args.freq)
    used_constant_fallback = False
    if not time_features:
        time_features = [Constant(value=0.0)]
        used_constant_fallback = True

    chain = Chain(
        [
            AsNumpyArray(field=FieldName.TARGET, expected_ndim=1),
            AddObservedValuesIndicator(
                target_field=FieldName.TARGET,
                output_field=FieldName.OBSERVED_VALUES,
            ),
            AddTimeFeatures(
                start_field=FieldName.START,
                target_field=FieldName.TARGET,
                output_field=FieldName.FEAT_TIME,
                time_features=time_features,
                pred_length=args.prediction_length,
            ),
            InstanceSplitter(
                target_field=FieldName.TARGET,
                is_pad_field=FieldName.IS_PAD,
                start_field=FieldName.START,
                forecast_start_field=FieldName.FORECAST_START,
                instance_sampler=TestSplitSampler(min_past=args.context_length),
                past_length=args.context_length,
                future_length=args.prediction_length,
                time_series_fields=[FieldName.FEAT_TIME, FieldName.OBSERVED_VALUES],
            ),
        ]
    )

    outputs = list(chain(iter(make_dataset(args.freq)), is_train=False))
    assert len(outputs) == 1, f"expected one prediction instance, got {len(outputs)}"
    entry = outputs[0]

    past_target = entry[f"past_{FieldName.TARGET}"]
    future_target = entry[f"future_{FieldName.TARGET}"]
    past_observed = entry[f"past_{FieldName.OBSERVED_VALUES}"]
    past_time_feat = entry[f"past_{FieldName.FEAT_TIME}"]
    future_time_feat = entry[f"future_{FieldName.FEAT_TIME}"]
    past_is_pad = entry[f"past_{FieldName.IS_PAD}"]

    expected_past_target = np.asarray(
        [1.0, 2.0, 3.0, 4.0, 5.0, 0.0, 7.0, 8.0], dtype=np.float32
    )[-args.context_length :]
    expected_past_observed = np.asarray(
        [1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0], dtype=np.float32
    )[-args.context_length :]

    assert FieldName.TARGET not in entry, "InstanceSplitter should remove target"
    assert past_target.shape == (args.context_length,)
    assert np.allclose(past_target, expected_past_target)
    assert future_target.shape == (0,), "prediction future_target should be empty"
    assert past_observed.shape == (args.context_length,)
    assert np.allclose(past_observed, expected_past_observed)
    assert np.allclose(past_is_pad, np.zeros(args.context_length, dtype=past_is_pad.dtype))
    assert past_time_feat.shape == (args.context_length, len(time_features))
    assert future_time_feat.shape == (args.prediction_length, len(time_features))
    assert FieldName.FORECAST_START in entry

    lags_head = get_lags_for_frequency(args.freq, num_lags=5)
    assert lags_head[: min(5, len(lags_head))] == list(range(1, min(5, len(lags_head)) + 1))

    fallback_note = " with Constant fallback" if used_constant_fallback else ""
    print(
        "OK transform_feature_smoke: "
        f"freq={args.freq!r}{fallback_note}, "
        f"past_target={past_target.tolist()}, "
        f"past_observed={past_observed.tolist()}, "
        f"past_time_feat_shape={tuple(past_time_feat.shape)}, "
        f"future_time_feat_shape={tuple(future_time_feat.shape)}, "
        f"lags_head={lags_head}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
