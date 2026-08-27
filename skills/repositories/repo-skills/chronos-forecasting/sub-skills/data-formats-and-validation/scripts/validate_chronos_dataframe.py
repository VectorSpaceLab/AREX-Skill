#!/usr/bin/env python3
"""Offline Chronos dataframe validator.

This script checks local CSV / parquet files for the Chronos-2 DataFrame
contract without importing Chronos or loading any model weights.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd
from pandas.api import types as ptypes

DEFAULT_ID_COLUMN = "item_id"
DEFAULT_TIMESTAMP_COLUMN = "timestamp"
DEFAULT_TARGET_COLUMNS = ("target",)
DEFAULT_DEMO_PREDICTION_LENGTH = 2


def split_values(values: list[str] | None, default: Iterable[str] | None = None) -> list[str]:
    items: list[str] = []
    for raw in values or []:
        for piece in str(raw).split(","):
            piece = piece.strip()
            if piece and piece not in items:
                items.append(piece)
    if not items and default is not None:
        return list(default)
    return items


def fmt_list(values: Iterable[object]) -> str:
    rendered = [repr(v) for v in values]
    return ", ".join(rendered) if rendered else "(none)"


def read_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if path.is_dir():
        raise IsADirectoryError(f"Expected a file, not a directory: {path}")

    if path.suffix.lower() in {".parquet", ".pq"}:
        try:
            return pd.read_parquet(path)
        except Exception as exc:  # pragma: no cover - exercised only when parquet engines are missing
            raise RuntimeError(
                f"Could not read parquet file {path}. Install pyarrow or fastparquet, or use CSV instead."
            ) from exc
    return pd.read_csv(path)


def classify_series(series: pd.Series) -> str:
    if ptypes.is_bool_dtype(series):
        return "categorical (bool)"
    if ptypes.is_numeric_dtype(series):
        return "numeric"
    return "categorical"


def parse_datetime_column(frame: pd.DataFrame, timestamp_column: str) -> tuple[pd.DataFrame | None, str | None]:
    parsed = frame.copy()
    try:
        parsed[timestamp_column] = pd.to_datetime(parsed[timestamp_column], errors="raise")
    except Exception as exc:
        return None, f"timestamp column {timestamp_column!r} could not be parsed as datetimes: {exc}"

    if parsed[timestamp_column].isna().any():
        return None, f"timestamp column {timestamp_column!r} contains missing values"
    return parsed, None


def validate_context(
    frame: pd.DataFrame,
    target_columns: list[str],
    id_column: str,
    timestamp_column: str,
    prediction_length: int,
    freq: str | None,
    known_covariates: list[str],
) -> tuple[
    pd.DataFrame | None,
    dict[object, pd.DatetimeIndex],
    object | None,
    list[str],
    list[str],
    list[str],
]:
    issues: list[str] = []
    notes: list[str] = []

    required = [id_column, timestamp_column, *target_columns]
    missing = [col for col in required if col not in frame.columns]
    if missing:
        issues.append(f"context is missing required columns: {fmt_list(missing)}")
        return None, {}, None, issues, notes, []

    for col in target_columns:
        if not ptypes.is_numeric_dtype(frame[col]):
            issues.append(f"Target column {col!r} must be numeric, got dtype {frame[col].dtype}")

    parsed, error = parse_datetime_column(frame, timestamp_column)
    if error is not None:
        issues.append(error)
        covariate_columns = [c for c in frame.columns if c not in {id_column, timestamp_column, *target_columns}]
        return None, {}, None, issues, notes, covariate_columns

    assert parsed is not None
    if parsed[id_column].isna().any():
        issues.append(f"id column {id_column!r} contains missing values")
    if parsed[timestamp_column].isna().any():
        issues.append(f"timestamp column {timestamp_column!r} contains missing values")

    covariate_columns = [c for c in parsed.columns if c not in {id_column, timestamp_column, *target_columns}]

    missing_known = [col for col in known_covariates if col not in covariate_columns]
    if missing_known:
        issues.append(f"known covariates are not present in the context frame: {fmt_list(missing_known)}")

    series_ids = list(pd.unique(parsed[id_column]))
    if len(series_ids) == 0:
        issues.append("context contains no rows")
        return parsed, {}, None, issues, notes, covariate_columns

    series_timestamps: dict[object, pd.DatetimeIndex] = {}
    inferred_freqs: list[object] = []
    explicit_freq: object | None = None
    if freq is not None:
        try:
            explicit_freq = pd.tseries.frequencies.to_offset(freq)
        except Exception as exc:
            issues.append(f"Could not parse explicit freq {freq!r}: {exc}")

    for series_id in series_ids:
        series = parsed.loc[parsed[id_column] == series_id, [timestamp_column]].copy()
        timestamps = pd.DatetimeIndex(series[timestamp_column].sort_values())
        series_timestamps[series_id] = timestamps

        if series[timestamp_column].duplicated().any():
            issues.append(f"Series {series_id!r} has duplicate timestamps")

        if len(timestamps) == 0:
            continue

        if explicit_freq is not None:
            expected = pd.DatetimeIndex(
                pd.date_range(start=timestamps[0], periods=len(timestamps), freq=explicit_freq)
            )
            if not expected.equals(timestamps):
                issues.append(
                    f"Series {series_id!r} does not follow explicit frequency {freq!r}"
                )
        else:
            if len(timestamps) >= 3:
                inferred = pd.infer_freq(timestamps)
                if inferred is None:
                    issues.append(
                        f"Series {series_id!r} has irregular timestamps and no regular frequency could be inferred"
                    )
                else:
                    inferred_freqs.append(pd.tseries.frequencies.to_offset(inferred))
            else:
                notes.append(f"Series {series_id!r} has fewer than 3 points; frequency inference was skipped")

    resolved_freq: object | None = explicit_freq
    if explicit_freq is None:
        if not inferred_freqs:
            issues.append(
                "Could not infer frequency from any series; provide --freq or at least one regular series with 3+ points"
            )
        else:
            resolved_freq = inferred_freqs[0]
            for other in inferred_freqs[1:]:
                if other != resolved_freq:
                    issues.append(
                        f"Time series disagree on frequency: {getattr(resolved_freq, 'freqstr', resolved_freq)} vs {getattr(other, 'freqstr', other)}"
                    )
                    break

    return parsed, series_timestamps, resolved_freq, issues, notes, covariate_columns


def validate_future(
    context_frame: pd.DataFrame | None,
    future_frame: pd.DataFrame,
    series_timestamps: dict[object, pd.DatetimeIndex],
    freq: object | None,
    target_columns: list[str],
    id_column: str,
    timestamp_column: str,
    prediction_length: int,
    known_covariates: list[str],
) -> tuple[pd.DataFrame | None, list[str], list[str]]:
    issues: list[str] = []
    notes: list[str] = []

    required = [id_column, timestamp_column]
    missing = [col for col in required if col not in future_frame.columns]
    if missing:
        issues.append(f"future_df is missing required columns: {fmt_list(missing)}")
        return None, issues, notes

    future_target_columns = [col for col in target_columns if col in future_frame.columns]
    if future_target_columns:
        issues.append(f"future_df cannot contain target columns: {fmt_list(future_target_columns)}")

    if context_frame is not None:
        extra = [col for col in future_frame.columns if col not in context_frame.columns]
        if extra:
            issues.append(f"future_df cannot contain columns not present in the context frame: {fmt_list(extra)}")

    future_missing_known = [col for col in known_covariates if col not in future_frame.columns]
    if future_missing_known:
        issues.append(f"future_df is missing declared known covariates: {fmt_list(future_missing_known)}")

    parsed, error = parse_datetime_column(future_frame, timestamp_column)
    if error is not None:
        issues.append(error)
        return None, issues, notes

    assert parsed is not None
    if parsed[id_column].isna().any():
        issues.append(f"id column {id_column!r} in future_df contains missing values")
    if parsed[timestamp_column].isna().any():
        issues.append(f"timestamp column {timestamp_column!r} in future_df contains missing values")

    if context_frame is None:
        return parsed, issues, notes

    context_ids = list(pd.unique(context_frame[id_column]))
    future_ids = list(pd.unique(parsed[id_column]))
    context_id_set = set(context_ids)
    future_id_set = set(future_ids)
    if context_id_set != future_id_set:
        missing_ids = [sid for sid in context_ids if sid not in future_id_set]
        extra_ids = [sid for sid in future_ids if sid not in context_id_set]
        if missing_ids:
            issues.append(f"future_df is missing series IDs: {fmt_list(missing_ids)}")
        if extra_ids:
            issues.append(f"future_df contains extra series IDs: {fmt_list(extra_ids)}")
    elif context_ids != future_ids:
        notes.append("future_df item order differs from the context frame; Chronos will normalize it")

    if freq is not None:
        for series_id in context_ids:
            if series_id not in series_timestamps:
                continue
            future_series = parsed.loc[parsed[id_column] == series_id, [timestamp_column]].copy()
            future_series = future_series.sort_values(timestamp_column)
            actual = pd.DatetimeIndex(future_series[timestamp_column])
            expected = pd.DatetimeIndex(
                pd.date_range(
                    start=series_timestamps[series_id][-1],
                    periods=prediction_length + 1,
                    freq=freq,
                )[1:]
            )
            if len(actual) != prediction_length:
                issues.append(
                    f"future_df must contain prediction_length={prediction_length} rows per item; series {series_id!r} has {len(actual)} rows"
                )
            if future_series[timestamp_column].duplicated().any():
                issues.append(f"future_df series {series_id!r} has duplicate timestamps")
            if len(actual) == prediction_length and not expected.equals(actual):
                issues.append(
                    f"future_df timestamps for series {series_id!r} do not match the expected prediction timestamps"
                )
    else:
        # Without a resolved frequency we can still check row counts and series IDs.
        counts = parsed[id_column].value_counts(sort=False)
        wrong_length = counts[counts != prediction_length]
        for series_id, count in wrong_length.items():
            issues.append(
                f"future_df must contain prediction_length={prediction_length} rows per item; series {series_id!r} has {int(count)} rows"
            )

    return parsed, issues, notes


def summarize_covariates(context_frame: pd.DataFrame | None, future_frame: pd.DataFrame | None, id_column: str, timestamp_column: str, target_columns: list[str]) -> tuple[list[str], list[str]]:
    if context_frame is None:
        return [], []

    covariates = [c for c in context_frame.columns if c not in {id_column, timestamp_column, *target_columns}]
    if future_frame is None:
        return covariates, []

    shared = [c for c in covariates if c in future_frame.columns]
    past_only = [c for c in covariates if c not in future_frame.columns]
    return shared, past_only


def print_summary(
    context_frame: pd.DataFrame,
    future_frame: pd.DataFrame | None,
    target_columns: list[str],
    known_covariates: list[str],
    series_timestamps: dict[object, pd.DatetimeIndex],
    freq: object | None,
    prediction_length: int,
    notes: list[str],
    shared_covariates: list[str],
    past_only_covariates: list[str],
) -> None:
    print("Chronos dataframe validation passed.")
    print(f"Series count: {len(series_timestamps)}")
    print(f"Context rows: {len(context_frame)}")
    print(f"Targets: {fmt_list(target_columns)}")
    if freq is not None:
        print(f"Frequency: {getattr(freq, 'freqstr', str(freq))}")
    else:
        print("Frequency: unavailable")

    if known_covariates:
        classified = [f"{col} ({classify_series(context_frame[col])})" for col in known_covariates if col in context_frame.columns]
        if future_frame is None:
            print(f"Declared known covariates (future values unavailable): {', '.join(classified)}")
        else:
            print(f"Declared known covariates: {', '.join(classified)}")
    if shared_covariates:
        classified = [f"{col} ({classify_series(context_frame[col])})" for col in shared_covariates]
        print(f"Shared future covariates: {', '.join(classified)}")
    if past_only_covariates:
        classified = [f"{col} ({classify_series(context_frame[col])})" for col in past_only_covariates]
        print(f"Past-only covariates: {', '.join(classified)}")

    if future_frame is None:
        print(f"Future frame: not supplied; expected horizon is {prediction_length} rows per series.")
    else:
        print(f"Future rows: {len(future_frame)}")
        print(f"Future horizon: {prediction_length} rows per series")

    for note in notes:
        print(f"Note: {note}")


def run_demo(prediction_length: int | None) -> int:
    demo_prediction_length = prediction_length or DEFAULT_DEMO_PREDICTION_LENGTH
    context = pd.DataFrame(
        {
            DEFAULT_ID_COLUMN: ["A", "A", "A", "B", "B", "B"],
            DEFAULT_TIMESTAMP_COLUMN: [
                "2024-01-01",
                "2024-01-02",
                "2024-01-03",
                "2024-01-01",
                "2024-01-02",
                "2024-01-03",
            ],
            "target": [10.0, 11.0, 12.0, 20.0, 21.0, 22.0],
            "temp": [1.2, 1.3, 1.4, 2.2, 2.3, 2.4],
            "promo": ["off", "on", "off", "off", "off", "on"],
        }
    )
    future = pd.DataFrame(
        {
            DEFAULT_ID_COLUMN: ["A", "A", "B", "B"],
            DEFAULT_TIMESTAMP_COLUMN: ["2024-01-04", "2024-01-05", "2024-01-04", "2024-01-05"],
            "temp": [1.5, 1.6, 2.5, 2.6],
            "promo": ["on", "off", "off", "on"],
        }
    )

    context_frame, series_timestamps, freq, issues, notes, _ = validate_context(
        context,
        ["target"],
        DEFAULT_ID_COLUMN,
        DEFAULT_TIMESTAMP_COLUMN,
        demo_prediction_length,
        "D",
        ["promo"],
    )
    if context_frame is None:
        for issue in issues:
            print(f"ERROR: {issue}", file=sys.stderr)
        return 1

    future_frame, future_issues, future_notes = validate_future(
        context_frame,
        future,
        series_timestamps,
        freq,
        ["target"],
        DEFAULT_ID_COLUMN,
        DEFAULT_TIMESTAMP_COLUMN,
        demo_prediction_length,
        ["promo"],
    )
    issues.extend(future_issues)
    notes.extend(future_notes)

    if issues:
        print("Chronos dataframe validation failed.", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    shared_covariates, past_only_covariates = summarize_covariates(
        context_frame,
        future_frame,
        DEFAULT_ID_COLUMN,
        DEFAULT_TIMESTAMP_COLUMN,
        ["target"],
    )
    print_summary(
        context_frame,
        future_frame,
        ["target"],
        ["promo"],
        series_timestamps,
        freq,
        demo_prediction_length,
        notes,
        shared_covariates,
        past_only_covariates,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Chronos DataFrame inputs offline.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--context",
        type=Path,
        help="Path to the context CSV or parquet file.",
    )
    parser.add_argument(
        "--future",
        type=Path,
        help="Optional path to the future CSV or parquet file.",
    )
    parser.add_argument(
        "--target",
        action="append",
        default=None,
        help="Target column name. Repeat the flag or use a comma-separated list for multiple targets.",
    )
    parser.add_argument(
        "--known-covariate",
        action="append",
        default=None,
        help="Known-future covariate column. Repeat the flag or use a comma-separated list for multiple columns.",
    )
    parser.add_argument(
        "--id-column",
        default=DEFAULT_ID_COLUMN,
        help="Column containing the series identifier.",
    )
    parser.add_argument(
        "--timestamp-column",
        default=DEFAULT_TIMESTAMP_COLUMN,
        help="Column containing timestamps.",
    )
    parser.add_argument(
        "--prediction-length",
        type=int,
        help="Forecast horizon used for future-row and timestamp checks.",
    )
    parser.add_argument(
        "--freq",
        default=None,
        help="Optional explicit frequency string. Use this when the context is too short for inference.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a tiny synthetic validation demo instead of reading files.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    target_columns = split_values(args.target, DEFAULT_TARGET_COLUMNS)
    known_covariates = split_values(args.known_covariate, ())

    if args.demo:
        return run_demo(args.prediction_length)

    if args.context is None:
        parser.error("--context is required unless --demo is used")
    if args.prediction_length is None:
        parser.error("--prediction-length is required unless --demo is used")
    if args.prediction_length <= 0:
        parser.error("--prediction-length must be a positive integer")

    try:
        context_frame = read_table(args.context)
        future_frame = read_table(args.future) if args.future is not None else None
    except Exception as exc:
        print(f"Chronos dataframe validation failed: {exc}", file=sys.stderr)
        return 1

    context_frame, series_timestamps, freq, issues, notes, _ = validate_context(
        context_frame,
        target_columns,
        args.id_column,
        args.timestamp_column,
        args.prediction_length,
        args.freq,
        known_covariates,
    )

    if context_frame is None and issues:
        print("Chronos dataframe validation failed.", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    if future_frame is not None:
        future_frame, future_issues, future_notes = validate_future(
            context_frame,
            future_frame,
            series_timestamps,
            freq,
            target_columns,
            args.id_column,
            args.timestamp_column,
            args.prediction_length,
            known_covariates,
        )
        issues.extend(future_issues)
        notes.extend(future_notes)

    if issues:
        print("Chronos dataframe validation failed.", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    shared_covariates, past_only_covariates = summarize_covariates(
        context_frame,
        future_frame,
        args.id_column,
        args.timestamp_column,
        target_columns,
    )
    print_summary(
        context_frame,
        future_frame,
        target_columns,
        known_covariates,
        series_timestamps,
        freq,
        args.prediction_length,
        notes,
        shared_covariates,
        past_only_covariates,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
