#!/usr/bin/env python3
"""Offline smoke checks for Lux semantic data type behavior.

The script creates tiny/local fixtures only. It verifies semantic inference,
`set_data_type` overrides, datetime conversion, and Period dtype handling.
"""

from __future__ import annotations

import argparse
import json
import warnings
from typing import Any, Dict


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run offline Lux semantic data-type smoke checks on local in-memory fixtures. "
            "Requires lux-api and pandas in the active Python environment."
        )
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print failures; suppress the success summary.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON summary instead of a human-readable success line.",
    )
    return parser


def _assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def _contains_temporal_warning(caught: list[warnings.WarningMessage]) -> bool:
    return any("may be temporal" in str(item.message) for item in caught)


def run_smoke() -> Dict[str, Any]:
    import lux  # noqa: F401  # Import first so Pandas DataFrames become Lux-aware.
    import pandas as pd

    row_count = 600
    df = pd.DataFrame(
        {
            "record_id": list(range(row_count)),
            "score": [float(i % 30) for i in range(row_count)],
            "segment": [["A", "B", "C"][i % 3] for i in range(row_count)],
            "state": [["CA", "NY", "TX", "WA", "MA"][i % 5] for i in range(row_count)],
            "date": [f"2020-01-{(i % 28) + 1:02d}" for i in range(row_count)],
        }
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        inferred = dict(df.data_type)

    _assert_equal(inferred["record_id"], "id", "ID-like numeric column inference")
    _assert_equal(inferred["score"], "quantitative", "numeric measure inference")
    _assert_equal(inferred["segment"], "nominal", "categorical string inference")
    _assert_equal(inferred["state"], "geographical", "state-name geographic inference")
    _assert_equal(inferred["date"], "temporal", "date-like string temporal inference")
    if not _contains_temporal_warning(caught):
        raise AssertionError("date-like string inference should emit a temporal conversion warning")

    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    with warnings.catch_warnings(record=True) as converted_warnings:
        warnings.simplefilter("always")
        converted = dict(df.data_type)
    _assert_equal(converted["date"], "temporal", "datetime64 conversion remains temporal")
    if _contains_temporal_warning(converted_warnings):
        raise AssertionError("converted datetime64 column should not emit the string-date warning")

    df.set_data_type({"state": "nominal", "record_id": "nominal"})
    overridden = dict(df.data_type)
    _assert_equal(overridden["state"], "nominal", "set_data_type geographic-to-nominal override")
    _assert_equal(overridden["record_id"], "nominal", "set_data_type ID-to-nominal override")

    period_df = pd.DataFrame(
        {
            "month": ["2021-01-01", "2021-02-01", "2021-03-01", "2021-04-01", "2021-05-01"],
            "value": [10, 14, 18, 15, 20],
        }
    )
    period_df["month"] = pd.to_datetime(period_df["month"], format="%Y-%m-%d")
    period_df["month"] = pd.DatetimeIndex(period_df["month"]).to_period(freq="M")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        period_type = period_df.data_type["month"]
    _assert_equal(period_type, "temporal", "Period dtype temporal inference")

    return {
        "inferred": inferred,
        "converted_date_type": converted["date"],
        "overridden_state_type": overridden["state"],
        "overridden_record_id_type": overridden["record_id"],
        "period_month_type": period_type,
    }


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    summary = run_smoke()
    if args.json:
        print(json.dumps(summary, sort_keys=True, indent=2))
    elif not args.quiet:
        print(
            "Lux data-type smoke passed: inferred quantitative/nominal/geographical/"
            "temporal/id types, verified overrides, datetime conversion, and Period dtype."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
