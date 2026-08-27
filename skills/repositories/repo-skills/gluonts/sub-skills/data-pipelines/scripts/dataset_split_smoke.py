#!/usr/bin/env python3
"""Deterministic PandasDataset + split smoke check for GluonTS."""

from __future__ import annotations

import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a tiny pandas PeriodIndex dataset, convert it to "
            "PandasDataset, split off the trailing prediction horizon, and "
            "assert generated input/label fields."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--periods",
        type=int,
        default=12,
        help="Number of deterministic observations to create.",
    )
    parser.add_argument(
        "--prediction-length",
        type=int,
        default=3,
        help="Trailing horizon length split from the dataset.",
    )
    parser.add_argument(
        "--freq",
        default="D",
        help="Pandas period frequency for the synthetic index.",
    )
    parser.add_argument(
        "--start",
        default="2024-01-01",
        help="Start period for the synthetic index.",
    )
    return parser.parse_args()


def build_dataset(periods: int, freq: str, start: str):
    import numpy as np
    import pandas as pd
    from gluonts.dataset.pandas import PandasDataset

    index = pd.period_range(start=start, periods=periods, freq=freq)
    frame = pd.DataFrame(
        {
            "target": np.arange(periods, dtype=np.float32),
            "known_cov": np.linspace(0.0, 1.0, periods, dtype=np.float32),
        },
        index=index,
    )
    return PandasDataset(
        frame,
        target="target",
        feat_dynamic_real=["known_cov"],
    )


def assert_has_fields(entry: dict, fields: tuple[str, ...]) -> None:
    missing = [field for field in fields if field not in entry]
    assert not missing, f"entry missing required fields: {missing}"


def main() -> None:
    args = parse_args()
    if args.prediction_length <= 0:
        raise SystemExit("--prediction-length must be positive")
    if args.periods <= args.prediction_length:
        raise SystemExit("--periods must be greater than --prediction-length")

    import numpy as np
    from gluonts.dataset.field_names import FieldName
    from gluonts.dataset.split import split

    dataset = build_dataset(args.periods, args.freq, args.start)
    prediction_length = args.prediction_length
    expected_train_length = args.periods - prediction_length

    original_entry = next(iter(dataset))
    assert_has_fields(original_entry, (FieldName.START, FieldName.TARGET))
    assert original_entry[FieldName.TARGET].shape == (args.periods,)
    assert original_entry[FieldName.FEAT_DYNAMIC_REAL].shape == (1, args.periods)

    training_data, test_template = split(dataset, offset=-prediction_length)
    train_entries = list(training_data)
    assert len(train_entries) == 1
    train_entry = train_entries[0]
    assert_has_fields(train_entry, (FieldName.START, FieldName.TARGET))
    assert train_entry[FieldName.START] == original_entry[FieldName.START]
    assert train_entry[FieldName.TARGET].shape == (expected_train_length,)
    np.testing.assert_array_equal(
        train_entry[FieldName.TARGET],
        np.arange(expected_train_length, dtype=np.float32),
    )

    test_data = test_template.generate_instances(
        prediction_length=prediction_length,
        windows=1,
    )
    pairs = list(test_data)
    assert len(pairs) == 1
    assert len(list(test_data.input)) == 1
    assert len(list(test_data.label)) == 1

    input_entry, label_entry = pairs[0]
    assert_has_fields(input_entry, (FieldName.START, FieldName.TARGET))
    assert_has_fields(label_entry, (FieldName.START, FieldName.TARGET))

    assert input_entry[FieldName.START] == original_entry[FieldName.START]
    assert input_entry[FieldName.TARGET].shape == (expected_train_length,)
    assert label_entry[FieldName.START] == (
        original_entry[FieldName.START] + expected_train_length
    )
    assert label_entry[FieldName.TARGET].shape == (prediction_length,)
    np.testing.assert_array_equal(
        label_entry[FieldName.TARGET],
        np.arange(expected_train_length, args.periods, dtype=np.float32),
    )

    # Known-future dynamic features are extended on prediction inputs and
    # sliced to the label horizon for labels.
    assert input_entry[FieldName.FEAT_DYNAMIC_REAL].shape == (1, args.periods)
    assert label_entry[FieldName.FEAT_DYNAMIC_REAL].shape == (
        1,
        prediction_length,
    )

    print(
        "OK: PandasDataset split smoke passed "
        f"entries=1 prediction_length={prediction_length} "
        f"train_target_length={expected_train_length} "
        f"label_start={label_entry[FieldName.START]}"
    )


if __name__ == "__main__":
    main()
