#!/usr/bin/env python3
"""Validate a CSV before constructing a PyTorch Forecasting TimeSeriesDataSet.

This helper intentionally avoids importing pytorch_forecasting or any local source
checkout. It checks the tabular contract that TimeSeriesDataSet expects and exits
nonzero when the CSV is invalid for the declared column roles.
"""

from __future__ import annotations

import argparse
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

try:
    import pandas as pd
except Exception as exc:  # pragma: no cover - depends on caller environment
    print(f"ERROR: pandas is required to read CSV files: {exc}", file=sys.stderr)
    raise SystemExit(2)


ROLE_OPTIONS = [
    "static_categoricals",
    "static_reals",
    "time_varying_known_categoricals",
    "time_varying_known_reals",
    "time_varying_unknown_categoricals",
    "time_varying_unknown_reals",
]

CATEGORICAL_ROLE_OPTIONS = {
    "static_categoricals",
    "time_varying_known_categoricals",
    "time_varying_unknown_categoricals",
}

REAL_ROLE_OPTIONS = {
    "static_reals",
    "time_varying_known_reals",
    "time_varying_unknown_reals",
}

PROTECTED_COLUMNS = {
    "__time_idx__",
    "relative_time_idx",
    "encoder_length",
}


class Findings:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.info.append(message)

    def emit(self) -> int:
        for message in self.errors:
            print(f"ERROR: {message}", file=sys.stderr)
        for message in self.warnings:
            print(f"WARNING: {message}")
        for message in self.info:
            print(f"OK: {message}")
        if self.errors:
            print(f"FAILED: {len(self.errors)} error(s), {len(self.warnings)} warning(s)", file=sys.stderr)
            return 1
        print(f"PASSED: 0 errors, {len(self.warnings)} warning(s)")
        return 0


def add_list_arg(parser: argparse.ArgumentParser, name: str, **kwargs) -> None:
    parser.add_argument(
        f"--{name.replace('_', '-')}",
        dest=name,
        action="append",
        default=[],
        metavar="COLS",
        **kwargs,
    )


def parse_columns(values: Iterable[str] | None) -> list[str]:
    columns: list[str] = []
    for value in values or []:
        for part in str(value).split(","):
            col = part.strip()
            if col:
                columns.append(col)
    return columns


def unique_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def format_group_key(key) -> str:
    if isinstance(key, tuple):
        return "(" + ", ".join(repr(v) for v in key) + ")"
    return repr(key)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a CSV for PyTorch Forecasting v1 TimeSeriesDataSet column "
            "roles without importing pytorch_forecasting. List options accept "
            "comma-separated values and may be repeated."
        )
    )
    parser.add_argument("csv", type=Path, help="CSV file to validate")
    parser.add_argument("--sep", default=",", help="CSV delimiter passed to pandas.read_csv (default: comma)")
    parser.add_argument("--encoding", default=None, help="Optional CSV encoding")
    parser.add_argument("--time-idx", required=True, help="Integer time index column name")
    add_list_arg(parser, "target", required=True, help="Target column(s); comma-separated or repeated")
    add_list_arg(parser, "group_ids", required=True, help="Group id column(s); comma-separated or repeated")
    parser.add_argument("--weight", default=None, help="Optional weight column")

    add_list_arg(parser, "static_categoricals", help="Static categorical covariate column(s)")
    add_list_arg(parser, "static_reals", help="Static real-valued covariate column(s)")
    add_list_arg(parser, "time_varying_known_categoricals", help="Known-future categorical covariate column(s)")
    add_list_arg(parser, "time_varying_known_reals", help="Known-future real covariate column(s)")
    add_list_arg(parser, "time_varying_unknown_categoricals", help="Unknown-future categorical covariate column(s)")
    add_list_arg(parser, "time_varying_unknown_reals", help="Unknown-future real covariate column(s)")

    parser.add_argument(
        "--allow-missing-timesteps",
        action="store_true",
        help="Treat gaps in integer time_idx as intentional TimeSeriesDataSet allow_missing_timesteps=True behavior",
    )
    parser.add_argument(
        "--strict-consecutive",
        action="store_true",
        help="Require consecutive time_idx values within each group even if --allow-missing-timesteps is set",
    )
    parser.add_argument(
        "--require-sorted",
        action="store_true",
        help="Return nonzero if rows are not already sorted by group_ids and time_idx",
    )
    parser.add_argument(
        "--require-monotonic",
        action="store_true",
        help="Return nonzero if input row order is not strictly increasing by time_idx within each group",
    )
    parser.add_argument(
        "--allow-categorical-nans",
        action="store_true",
        help="Warn instead of error for NaNs in declared categorical covariates; use only with matching NaNLabelEncoder(add_nan=True)",
    )
    parser.add_argument("--min-encoder-length", type=int, default=None, help="Optional min_encoder_length to check per-group length")
    parser.add_argument("--max-encoder-length", type=int, default=None, help="Optional max_encoder_length; used as min when min is omitted")
    parser.add_argument("--min-prediction-length", type=int, default=None, help="Optional min_prediction_length to check per-group length")
    parser.add_argument("--max-prediction-length", type=int, default=None, help="Optional max_prediction_length; default prediction length is 1")
    parser.add_argument("--max-lag", type=int, default=0, help="Maximum lag length used in TimeSeriesDataSet lags, if any")
    parser.add_argument(
        "--prediction-start-idx",
        type=int,
        default=None,
        help="Optional first future decoder time_idx for inference known-covariate coverage checks",
    )
    parser.add_argument(
        "--prediction-length",
        type=int,
        default=None,
        help="Optional future decoder horizon for --prediction-start-idx checks; defaults to max/min prediction length when available",
    )
    return parser


def collect_args(args: argparse.Namespace) -> dict[str, list[str]]:
    columns = {name: unique_preserve_order(parse_columns(getattr(args, name))) for name in ROLE_OPTIONS}
    columns["target"] = unique_preserve_order(parse_columns(args.target))
    columns["group_ids"] = unique_preserve_order(parse_columns(args.group_ids))
    return columns


def check_required_columns(df: pd.DataFrame, args: argparse.Namespace, columns: dict[str, list[str]], findings: Findings) -> None:
    required = [args.time_idx] + columns["target"] + columns["group_ids"]
    if args.weight:
        required.append(args.weight)
    for role in ROLE_OPTIONS:
        required.extend(columns[role])
    missing = [col for col in unique_preserve_order(required) if col not in df.columns]
    if missing:
        findings.error(f"Missing required column(s): {missing}")
    else:
        findings.note(f"all {len(unique_preserve_order(required))} declared column(s) are present")


def check_column_names(df: pd.DataFrame, columns: dict[str, list[str]], findings: Findings) -> None:
    dotted = [str(col) for col in df.columns if "." in str(col)]
    if dotted:
        findings.error(f"Column names containing '.' are invalid for TimeSeriesDataSet: {dotted[:20]}")

    protected = set(df.columns).intersection(PROTECTED_COLUMNS)
    protected.update(col for col in df.columns if str(col).startswith("__target__"))
    protected.update(col for col in df.columns if str(col).startswith("__group_id__"))
    generated_lag_style = [col for col in df.columns if "_lagged_by_" in str(col)]
    if protected:
        findings.warn(f"DataFrame contains protected/internal-style column names: {sorted(protected)}")
    if generated_lag_style:
        findings.warn(
            "Columns with '_lagged_by_' look like TimeSeriesDataSet-generated lag names; "
            f"ensure they do not collide with configured lags: {generated_lag_style[:20]}"
        )

    for target in columns["target"]:
        internal = f"__target__{target}"
        if internal in df.columns:
            findings.error(f"Protected target column {internal!r} is already present")


def check_role_overlap(args: argparse.Namespace, columns: dict[str, list[str]], findings: Findings) -> None:
    role_by_col: dict[str, list[str]] = defaultdict(list)
    for role in ROLE_OPTIONS:
        values = parse_columns(getattr(args, role))
        duplicates = sorted({col for col in values if values.count(col) > 1})
        if duplicates:
            findings.warn(f"Column(s) repeated within {role}: {duplicates}")
        for col in columns[role]:
            role_by_col[col].append(role)

    allowed_target_unknown_roles = {
        "time_varying_unknown_reals",
        "time_varying_unknown_categoricals",
    }
    allowed_group_static_roles = {"static_categoricals", "static_reals"}

    for col, roles in sorted(role_by_col.items()):
        if len(roles) <= 1:
            continue
        if col in columns["target"]:
            extra = [role for role in roles if role not in allowed_target_unknown_roles]
            if extra or len(roles) > 1:
                findings.error(
                    f"Target column {col!r} is declared in multiple covariate roles {roles}; "
                    "a target may appear only in the appropriate time_varying_unknown_* role"
                )
        elif col in columns["group_ids"] and set(roles).issubset(allowed_group_static_roles):
            findings.error(
                f"Group id column {col!r} is declared in multiple static covariate roles {roles}; "
                "group ids may be reused as static covariates, but choose exactly one static role per column"
            )
        else:
            findings.error(f"Column {col!r} is declared in multiple covariate roles: {roles}")

    for target in columns["target"]:
        for role in ["time_varying_known_reals", "time_varying_known_categoricals", "static_reals", "static_categoricals"]:
            if target in columns[role]:
                findings.error(f"Target column {target!r} must not be declared in {role}")

    if args.time_idx in columns["time_varying_known_reals"]:
        findings.note("time_idx is declared as a known real covariate, a common TimeSeriesDataSet pattern")
    elif args.time_idx in columns["time_varying_known_categoricals"]:
        findings.warn("time_idx is declared as a known categorical; this is uncommon unless intentionally bucketed")


def finite_mask(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.map(lambda x: math.isfinite(float(x)) if pd.notna(x) else False)


def check_nulls_and_dtypes(df: pd.DataFrame, args: argparse.Namespace, columns: dict[str, list[str]], findings: Findings) -> None:
    if args.time_idx not in df.columns:
        return
    time_series = df[args.time_idx]
    if time_series.isna().any():
        findings.error(f"time_idx column {args.time_idx!r} contains {int(time_series.isna().sum())} missing value(s)")
    if time_series.dtype.kind != "i":
        findings.error(
            f"time_idx column {args.time_idx!r} has dtype {time_series.dtype}; "
            "TimeSeriesDataSet expects a signed integer dtype"
        )

    for col in columns["group_ids"]:
        if col in df.columns and df[col].isna().any():
            findings.error(f"group id column {col!r} contains {int(df[col].isna().sum())} missing value(s)")

    for col in columns["target"]:
        if col not in df.columns:
            continue
        missing = int(df[col].isna().sum())
        if missing:
            findings.error(f"target column {col!r} contains {missing} NaN/missing value(s)")
        if df[col].dtype.kind in "fc":
            nonfinite = (~finite_mask(df[col])) & df[col].notna()
            if nonfinite.any():
                bad = int(nonfinite.sum())
                findings.error(f"target column {col!r} contains {bad} non-finite value(s)")

    if args.weight and args.weight in df.columns:
        if df[args.weight].isna().any():
            findings.error(f"weight column {args.weight!r} contains {int(df[args.weight].isna().sum())} missing value(s)")
        if df[args.weight].dtype.kind not in "iuf":
            findings.warn(f"weight column {args.weight!r} has non-numeric dtype {df[args.weight].dtype}")

    target_set = set(columns["target"])
    for role in REAL_ROLE_OPTIONS:
        for col in columns[role]:
            if col not in df.columns or col in target_set:
                continue
            if df[col].isna().any():
                findings.error(f"real-valued column {col!r} declared in {role} contains {int(df[col].isna().sum())} missing value(s)")
            if df[col].dtype.kind in "fc":
                nonfinite = (~finite_mask(df[col])) & df[col].notna()
                if nonfinite.any():
                    bad = int(nonfinite.sum())
                    findings.error(f"real-valued column {col!r} declared in {role} contains {bad} non-finite value(s)")
            if df[col].dtype.kind not in "iufc":
                findings.warn(f"real-valued column {col!r} declared in {role} has dtype {df[col].dtype}")

    for role in CATEGORICAL_ROLE_OPTIONS:
        for col in columns[role]:
            if col not in df.columns:
                continue
            missing = int(df[col].isna().sum())
            if missing and col not in target_set:
                msg = f"categorical column {col!r} declared in {role} contains {missing} missing value(s)"
                if args.allow_categorical_nans:
                    findings.warn(msg + "; ensure the TimeSeriesDataSet uses NaNLabelEncoder(add_nan=True)")
                else:
                    findings.error(msg + "; fill values or rerun with --allow-categorical-nans only if encoders handle them")
            if df[col].dtype.kind in "iufcb":
                findings.error(
                    f"categorical column {col!r} declared in {role} has numeric/bool dtype {df[col].dtype}; "
                    "convert categorical codes to strings before TimeSeriesDataSet construction"
                )


def existing_subset(df: pd.DataFrame, cols: list[str]) -> list[str]:
    return [col for col in cols if col in df.columns]


def check_group_time_structure(df: pd.DataFrame, args: argparse.Namespace, columns: dict[str, list[str]], findings: Findings) -> None:
    key_cols = columns["group_ids"] + [args.time_idx]
    if not all(col in df.columns for col in key_cols):
        return

    dup_mask = df.duplicated(key_cols, keep=False)
    if dup_mask.any():
        examples = df.loc[dup_mask, key_cols].head(10).to_dict(orient="records")
        findings.error(
            f"Found {int(dup_mask.sum())} row(s) with duplicate group/time keys; examples: {examples}"
        )

    sorted_df = df.sort_values(key_cols, kind="mergesort")
    if not df.index.equals(sorted_df.index):
        message = "Rows are not sorted by group_ids + time_idx; TimeSeriesDataSet sorts internally, but pre-sorting improves reproducibility"
        if args.require_sorted:
            findings.error(message)
        else:
            findings.warn(message)
    else:
        findings.note("rows are sorted by group_ids + time_idx")

    non_monotonic_groups: list[str] = []
    for key, group in df.groupby(columns["group_ids"], sort=False, dropna=False):
        diffs = group[args.time_idx].diff().dropna()
        if (diffs <= 0).any():
            non_monotonic_groups.append(format_group_key(key))
            if len(non_monotonic_groups) >= 10:
                break
    if non_monotonic_groups:
        message = f"Input row order is not strictly increasing by time_idx within group(s): {non_monotonic_groups}"
        if args.require_monotonic:
            findings.error(message)
        else:
            findings.warn(message)

    gap_examples: list[str] = []
    sorted_by_group = sorted_df.groupby(columns["group_ids"], sort=False, dropna=False)
    for key, group in sorted_by_group:
        diffs = group[args.time_idx].diff().dropna()
        gaps = diffs[diffs > 1]
        if not gaps.empty:
            gap_examples.append(f"{format_group_key(key)} max_gap={int(gaps.max())}")
            if len(gap_examples) >= 10:
                break
    if gap_examples:
        message = f"Missing timestep gaps detected within group(s): {gap_examples}"
        if args.strict_consecutive or not args.allow_missing_timesteps:
            findings.error(message + "; fill missing rows or construct TimeSeriesDataSet with allow_missing_timesteps=True")
        else:
            findings.warn(message + "; allowed because --allow-missing-timesteps was set")
    else:
        findings.note("no missing timestep gaps detected within groups")


def check_lengths(df: pd.DataFrame, args: argparse.Namespace, columns: dict[str, list[str]], findings: Findings) -> None:
    if args.min_encoder_length is None and args.max_encoder_length is None:
        return
    if not all(col in df.columns for col in columns["group_ids"] + [args.time_idx]):
        return

    min_encoder = args.min_encoder_length
    if min_encoder is None:
        min_encoder = args.max_encoder_length
    min_prediction = args.min_prediction_length
    if min_prediction is None:
        min_prediction = args.max_prediction_length if args.max_prediction_length is not None else 1
    if min_encoder is None or min_prediction is None:
        return
    if min_encoder < 0 or min_prediction <= 0 or args.max_lag < 0:
        findings.error("encoder/prediction lengths and max lag must be non-negative, with prediction length > 0")
        return

    needed = int(min_encoder) + int(min_prediction) + int(args.max_lag)
    too_short: list[str] = []
    group_count = 0
    for key, group in df.groupby(columns["group_ids"], sort=False, dropna=False):
        group_count += 1
        if len(group) < needed:
            too_short.append(f"{format_group_key(key)} count={len(group)}")
            if len(too_short) >= 10:
                break
    if too_short:
        message = (
            f"Some groups have fewer rows than min_encoder_length + min_prediction_length + max_lag = {needed}: "
            f"{too_short}"
        )
        if len(too_short) == group_count:
            findings.error(message)
        else:
            findings.warn(message + "; those groups may be absent from the dataset index")
    else:
        findings.note(f"all groups have at least {needed} rows for the supplied minimum lengths")


def check_future_known_covariates(df: pd.DataFrame, args: argparse.Namespace, columns: dict[str, list[str]], findings: Findings) -> None:
    if args.prediction_start_idx is None:
        return
    if not all(col in df.columns for col in columns["group_ids"] + [args.time_idx]):
        return
    horizon = args.prediction_length
    if horizon is None:
        horizon = args.max_prediction_length or args.min_prediction_length or 1
    if horizon <= 0:
        findings.error("--prediction-length must be positive")
        return

    known_cols = unique_preserve_order(
        columns["time_varying_known_categoricals"] + columns["time_varying_known_reals"]
    )
    known_cols = [col for col in known_cols if col != args.time_idx]
    if not known_cols:
        findings.warn("--prediction-start-idx was provided but no known-future covariate columns were declared")

    future_times = set(range(args.prediction_start_idx, args.prediction_start_idx + horizon))
    missing_rows: list[str] = []
    missing_values: list[str] = []
    for key, group in df.groupby(columns["group_ids"], sort=False, dropna=False):
        present_times = set(group[args.time_idx].tolist())
        absent = sorted(future_times - present_times)
        if absent:
            missing_rows.append(f"{format_group_key(key)} missing_time_idx={absent[:5]}")
        future = group[group[args.time_idx].isin(future_times)]
        for col in known_cols:
            if col in future.columns and future[col].isna().any():
                missing_values.append(f"{format_group_key(key)} col={col!r} missing={int(future[col].isna().sum())}")
        if len(missing_rows) >= 10 or len(missing_values) >= 10:
            break
    if missing_rows:
        findings.error(
            "Inference future rows are missing for declared horizon; examples: " + str(missing_rows[:10])
        )
    if missing_values:
        findings.error(
            "Known-future covariates contain missing values inside prediction horizon; examples: "
            + str(missing_values[:10])
        )
    if not missing_rows and not missing_values:
        findings.note(
            f"future horizon [{args.prediction_start_idx}, {args.prediction_start_idx + horizon - 1}] has declared known covariate coverage"
        )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    findings = Findings()

    if not args.csv.exists():
        findings.error(f"CSV file does not exist: {args.csv}")
        return findings.emit()

    try:
        df = pd.read_csv(args.csv, sep=args.sep, encoding=args.encoding)
    except Exception as exc:
        findings.error(f"Could not read CSV {args.csv}: {exc}")
        return findings.emit()

    columns = collect_args(args)
    if not columns["target"]:
        findings.error("at least one --target column is required")
    if not columns["group_ids"]:
        findings.error("at least one --group-ids column is required")

    findings.note(f"read {len(df)} row(s) and {len(df.columns)} column(s) from {args.csv.name}")
    check_required_columns(df, args, columns, findings)
    check_column_names(df, columns, findings)
    check_role_overlap(args, columns, findings)
    check_nulls_and_dtypes(df, args, columns, findings)
    check_group_time_structure(df, args, columns, findings)
    check_lengths(df, args, columns, findings)
    check_future_known_covariates(df, args, columns, findings)

    return findings.emit()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
