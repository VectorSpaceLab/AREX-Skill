#!/usr/bin/env python3
"""Validate a small Recommenders interaction CSV before splitting or modeling.

This helper performs no network access and does not modify inputs. It checks the
common long-form interaction schema used by Recommenders examples and APIs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a Recommenders long-form interactions CSV.")
    parser.add_argument("--input", required=True, help="CSV file with one row per user-item interaction.")
    parser.add_argument("--user-col", default="userID")
    parser.add_argument("--item-col", default="itemID")
    parser.add_argument("--rating-col", default="rating")
    parser.add_argument("--timestamp-col", default="timestamp")
    parser.add_argument("--require-rating", action="store_true", help="Require the rating/feedback column.")
    parser.add_argument("--require-timestamp", action="store_true", help="Require a timestamp column for chronological workflows.")
    parser.add_argument("--min-interactions-per-user", type=positive_int, default=1)
    parser.add_argument("--min-interactions-per-item", type=positive_int, default=1)
    parser.add_argument("--allow-duplicates", action="store_true", help="Allow duplicate user-item rows.")
    parser.add_argument("--max-null-rate", type=float, default=0.0, help="Maximum allowed null fraction in required columns.")
    args = parser.parse_args()
    if not 0.0 <= args.max_null_rate <= 1.0:
        parser.error("--max-null-rate must be between 0 and 1")
    return args


def fail(message: str, details: dict | None = None) -> int:
    payload = {"status": "fail", "message": message}
    if details:
        payload.update(details)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 1


def main() -> int:
    args = parse_args()
    path = Path(args.input)
    if not path.exists():
        return fail("input file does not exist", {"input": str(path)})
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        return fail("could not read CSV", {"error": str(exc)})

    required = [args.user_col, args.item_col]
    if args.require_rating:
        required.append(args.rating_col)
    if args.require_timestamp:
        required.append(args.timestamp_col)
    missing = [col for col in required if col not in df.columns]
    if missing:
        return fail("missing required columns", {"missing_columns": missing, "columns": list(df.columns)})
    if df.empty:
        return fail("input dataframe is empty")

    null_rates = {col: float(df[col].isna().mean()) for col in required}
    too_null = {col: rate for col, rate in null_rates.items() if rate > args.max_null_rate}
    if too_null:
        return fail("required columns exceed allowed null rate", {"null_rates": too_null})

    duplicate_count = int(df.duplicated([args.user_col, args.item_col]).sum())
    if duplicate_count and not args.allow_duplicates:
        return fail(
            "duplicate user-item rows found",
            {"duplicate_count": duplicate_count, "hint": "aggregate or pass --allow-duplicates if the model supports repeated events"},
        )

    if args.require_rating and not pd.api.types.is_numeric_dtype(df[args.rating_col]):
        return fail("rating column is not numeric", {"rating_col": args.rating_col, "dtype": str(df[args.rating_col].dtype)})
    if args.require_timestamp and not pd.api.types.is_numeric_dtype(df[args.timestamp_col]):
        # Sortable strings can be valid timestamps, so warn rather than fail.
        timestamp_warning = f"timestamp column dtype is {df[args.timestamp_col].dtype}; confirm chronological ordering"
    else:
        timestamp_warning = None

    user_counts = df.groupby(args.user_col).size()
    item_counts = df.groupby(args.item_col).size()
    sparse_users = int((user_counts < args.min_interactions_per_user).sum())
    sparse_items = int((item_counts < args.min_interactions_per_item).sum())
    warnings = []
    if sparse_users:
        warnings.append(f"{sparse_users} users have fewer than {args.min_interactions_per_user} interactions")
    if sparse_items:
        warnings.append(f"{sparse_items} items have fewer than {args.min_interactions_per_item} interactions")
    if timestamp_warning:
        warnings.append(timestamp_warning)

    result = {
        "status": "ok",
        "rows": int(len(df)),
        "columns": list(df.columns),
        "unique_users": int(df[args.user_col].nunique()),
        "unique_items": int(df[args.item_col].nunique()),
        "duplicate_user_item_rows": duplicate_count,
        "required_columns": required,
        "null_rates": null_rates,
        "warnings": warnings,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
