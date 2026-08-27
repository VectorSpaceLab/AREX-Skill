#!/usr/bin/env python3
"""Validate a Flow Forecast time-series CSV before training or inference.

The script checks for required columns, window lengths, optional timezone normalization,
series-id coverage, and NaN counts. It is intentionally lightweight so it can be used as a
preflight check in a private inspection environment or on a small local CSV.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd

from flood_forecast.preprocessing.pytorch_loaders import to_tz_naive_datetime


@dataclass(frozen=True)
class ValidationReport:
    """Summarize the results of one CSV validation run."""

    ok: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def _split_csv_list(value: str | None) -> list[str]:
    """Split a comma-separated CLI value into trimmed column names.

    :param value: Comma-separated list or ``None``.
    :type value: str | None
    :return: Parsed list of non-empty column names.
    :rtype: list[str]
    """
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _build_smoke_frame() -> pd.DataFrame:
    """Create a tiny synthetic dataframe for parser and smoke checks.

    :return: A dataframe with the canonical Flow Forecast columns.
    :rtype: pandas.DataFrame
    """
    stamps = pd.date_range("2020-01-01", periods=40, freq="h")
    return pd.DataFrame(
        {
            "datetime": stamps,
            "cfs": range(40),
            "precip": [0.1 * idx for idx in range(40)],
            "temp": [20.0 + 0.1 * idx for idx in range(40)],
            "series_id": [0] * 20 + [1] * 20,
            "label": [0] * 20 + [1] * 20,
        }
    )


def _load_frame(csv_path: Path | None, smoke: bool) -> pd.DataFrame:
    """Load the dataframe to validate.

    :param csv_path: CSV path supplied by the user.
    :type csv_path: pathlib.Path | None
    :param smoke: Whether to use the built-in synthetic frame.
    :type smoke: bool
    :return: The dataframe to validate.
    :rtype: pandas.DataFrame
    """
    if smoke:
        return _build_smoke_frame()
    if csv_path is None:
        raise ValueError("Either --csv or --smoke must be provided.")
    return pd.read_csv(csv_path)


def validate_frame(
    frame: pd.DataFrame,
    *,
    forecast_history: int,
    forecast_length: int,
    target_cols: Sequence[str],
    relevant_cols: Sequence[str],
    sort_column: str | None = None,
    series_id_col: str | None = None,
    min_rows: int | None = None,
) -> ValidationReport:
    """Validate the dataframe shape and the required loader columns.

    :param frame: The dataframe to validate.
    :type frame: pandas.DataFrame
    :param forecast_history: Number of historical steps required by the loader.
    :type forecast_history: int
    :param forecast_length: Number of future steps required by the loader.
    :type forecast_length: int
    :param target_cols: Target column names.
    :type target_cols: Sequence[str]
    :param relevant_cols: Feature column names.
    :type relevant_cols: Sequence[str]
    :param sort_column: Optional datetime column to normalize and sort.
    :type sort_column: str | None
    :param series_id_col: Optional series ID column for grouped data.
    :type series_id_col: str | None
    :param min_rows: Optional lower bound on total rows.
    :type min_rows: int | None
    :return: A validation report.
    :rtype: ValidationReport
    """
    errors: list[str] = []
    warnings: list[str] = []

    if forecast_history < 1:
        errors.append("forecast_history must be positive.")
    if forecast_length < 1:
        errors.append("forecast_length must be positive.")

    required_columns = set(target_cols) | set(relevant_cols)
    if sort_column:
        required_columns.add(sort_column)
    if series_id_col:
        required_columns.add(series_id_col)
    missing = [column for column in sorted(required_columns) if column not in frame.columns]
    if missing:
        errors.append("missing required columns: " + ", ".join(missing))

    if sort_column and sort_column in frame.columns:
        normalized = to_tz_naive_datetime(frame[sort_column])
        if normalized.isna().any():
            errors.append(f"column {sort_column!r} contains values that could not be parsed as datetimes.")
        frame = frame.copy()
        frame[sort_column] = normalized
        frame = frame.sort_values(sort_column)

    if min_rows is not None and len(frame) < min_rows:
        errors.append(f"row count {len(frame)} is below the requested minimum {min_rows}.")

    if len(frame) < forecast_history + forecast_length + 1:
        errors.append(
            "the dataframe is too short for forecast_history + forecast_length + 1 rows; "
            f"need at least {forecast_history + forecast_length + 1}, found {len(frame)}"
        )

    if series_id_col and series_id_col in frame.columns:
        unique_count = frame[series_id_col].nunique(dropna=True)
        if unique_count < 1:
            errors.append(f"series ID column {series_id_col!r} has no non-null groups.")
        elif unique_count == 1:
            warnings.append(f"series ID column {series_id_col!r} has only one unique group.")

    selected = frame[list(required_columns)].copy() if required_columns else frame
    nan_counts = selected.isna().sum()
    noisy = {column: int(count) for column, count in nan_counts.items() if int(count) > 0}
    if noisy:
        warnings.append("NaN counts by selected column: " + ", ".join(f"{k}={v}" for k, v in noisy.items()))

    return ValidationReport(ok=not errors, errors=tuple(errors), warnings=tuple(warnings))


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the command-line parser.

    :return: The argument parser.
    :rtype: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(description="Validate a Flow Forecast time-series CSV.")
    parser.add_argument("--csv", type=Path, help="Path to the CSV file to validate.")
    parser.add_argument("--smoke", action="store_true", help="Validate a built-in synthetic fixture instead of a file.")
    parser.add_argument("--forecast-history", type=int, required=False, default=48)
    parser.add_argument("--forecast-length", type=int, required=False, default=12)
    parser.add_argument("--target-col", required=True, help="Comma-separated target column names.")
    parser.add_argument("--relevant-cols", required=True, help="Comma-separated feature column names.")
    parser.add_argument("--sort-column", help="Optional datetime column to normalize and sort.")
    parser.add_argument("--series-id-col", help="Optional series-ID column for grouped data.")
    parser.add_argument("--min-rows", type=int, help="Optional minimum row count.")
    parser.add_argument("--show-head", action="store_true", help="Print the top rows after validation.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CSV validator.

    :param argv: Optional argument vector.
    :type argv: list[str] | None
    :return: Process exit status.
    :rtype: int
    """
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    frame = _load_frame(args.csv, args.smoke)
    report = validate_frame(
        frame,
        forecast_history=args.forecast_history,
        forecast_length=args.forecast_length,
        target_cols=_split_csv_list(args.target_col),
        relevant_cols=_split_csv_list(args.relevant_cols),
        sort_column=args.sort_column,
        series_id_col=args.series_id_col,
        min_rows=args.min_rows,
    )

    print("CSV validation result:", "OK" if report.ok else "FAILED")
    for warning in report.warnings:
        print("WARN:", warning)
    for error in report.errors:
        print("ERROR:", error)
    if args.show_head:
        print(frame.head().to_string(index=False))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
