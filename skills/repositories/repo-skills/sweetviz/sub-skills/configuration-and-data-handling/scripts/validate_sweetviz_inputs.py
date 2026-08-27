#!/usr/bin/env python3
"""Preflight CSV inputs for Sweetviz without generating reports.

The checks mirror common Sweetviz validation failures: duplicate columns,
missing FeatureConfig names, skipped targets, target NaNs, target type issues,
mixed inferred types, and compare_intra condition problems. The script does not
import Sweetviz, open browsers, contact networks, or write output files.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence


NUMERIC_DISTINCT_TO_BE_CATEGORICAL = 10
BOOLEAN_TEXT_PAIRS = [
    {"y", "n"},
    {"yes", "no"},
    {"true", "false"},
    {"t", "f"},
]
CONDITION_TRUE = {"true", "t", "yes", "y", "1", "1.0"}
CONDITION_FALSE = {"false", "f", "no", "n", "0", "0.0"}


class Finding:
    def __init__(self, level: str, message: str):
        self.level = level
        self.message = message

    def __str__(self) -> str:
        return f"{self.level}: {self.message}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Preflight source/compare CSV inputs for Sweetviz data and "
            "configuration issues without creating a report."
        )
    )
    parser.add_argument("--source-csv", required=True, help="Source CSV path to inspect.")
    parser.add_argument("--compare-csv", help="Optional compare CSV path to inspect.")
    parser.add_argument("--target", help="Optional Sweetviz target feature name.")
    parser.add_argument(
        "--skip",
        action="append",
        default=[],
        metavar="FEATURE",
        help="Feature to skip; repeat for multiple features.",
    )
    parser.add_argument(
        "--force-cat",
        action="append",
        default=[],
        metavar="FEATURE",
        help="Feature to force categorical; repeat for multiple features.",
    )
    parser.add_argument(
        "--force-text",
        action="append",
        default=[],
        metavar="FEATURE",
        help="Feature to force text; repeat for multiple features.",
    )
    parser.add_argument(
        "--force-num",
        action="append",
        default=[],
        metavar="FEATURE",
        help="Feature to force numeric; repeat for multiple features.",
    )
    parser.add_argument(
        "--condition-column",
        help=(
            "Optional source CSV column intended for compare_intra(); must be "
            "boolean dtype for Sweetviz and split into non-empty groups."
        ),
    )
    return parser


def split_feature_values(values: Iterable[str]) -> list[str]:
    """Accept repeated flags and comma-separated convenience values."""
    features: list[str] = []
    for value in values:
        for item in str(value).split(","):
            stripped = item.strip()
            if stripped:
                features.append(stripped)
    return features


def normalize_feature(name: str | None) -> str | None:
    if name is None:
        return None
    return "df_index" if name == "index" else name


def normalize_features(values: Sequence[str]) -> list[str]:
    return [normalize_feature(value) or value for value in values]


def read_csv_header(path: Path) -> tuple[list[str], list[str]]:
    """Return raw CSV header and duplicate column names before pandas mangling."""
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            return [], []
    duplicates = sorted(name for name, count in Counter(header).items() if count > 1)
    return header, duplicates


def load_dataframe(pd, path: Path):  # noqa: ANN001 - pandas is imported lazily.
    return pd.read_csv(path)


def columns_after_sweetviz_index_rename(columns: Sequence[str]) -> list[str]:
    return ["df_index" if col == "index" else col for col in columns]


def non_null_unique_values(series) -> list:  # noqa: ANN001 - pandas Series.
    return list(series.dropna().unique())


def sweetviz_boolean_like(pd, series) -> bool:  # noqa: ANN001 - pandas objects.
    non_null = series.dropna()
    distinct = non_null.nunique(dropna=True)
    if distinct == 0:
        return False
    if pd.api.types.is_bool_dtype(series):
        return True
    if 1 <= distinct <= 2 and pd.api.types.is_numeric_dtype(series):
        try:
            return bool(non_null.between(0, 1).all())
        except TypeError:
            return False
    if 1 <= distinct <= 4:
        unique_values = {str(value).lower() for value in non_null_unique_values(series)}
        return len(unique_values) == 2 and any(unique_values == pair for pair in BOOLEAN_TEXT_PAIRS)
    return False


def sweetviz_numeric_target_like(pd, series, forced_numeric: bool) -> tuple[bool, str | None]:  # noqa: ANN001
    non_null = series.dropna()
    distinct = non_null.nunique(dropna=True)
    if distinct == 0:
        return False, "target has no non-missing values"
    if sweetviz_boolean_like(pd, series):
        return True, None
    if forced_numeric:
        if pd.api.types.is_numeric_dtype(series):
            return True, None
        return False, "target is forced numeric but pandas did not load it as a numeric dtype"
    if pd.api.types.is_numeric_dtype(series) and distinct > NUMERIC_DISTINCT_TO_BE_CATEGORICAL:
        return True, None
    if pd.api.types.is_numeric_dtype(series):
        return (
            False,
            "numeric target has at most 10 distinct non-null values and will infer as categorical unless forced numeric",
        )
    return False, "target is not numeric or boolean-like"


def maybe_mixed_inferred_type(series) -> str | None:  # noqa: ANN001 - pandas Series.
    try:
        inferred = series.value_counts(dropna=True).index.inferred_type
    except Exception:  # Defensive: pandas extension arrays can vary.
        return None
    if str(inferred).startswith("mixed"):
        return str(inferred)
    return None


def parse_condition_value(value) -> bool | None:  # noqa: ANN001 - CSV scalar.
    text = str(value).strip().lower()
    if text in CONDITION_TRUE:
        return True
    if text in CONDITION_FALSE:
        return False
    return None


def check_condition_column(pd, df, column: str, findings: list[Finding]) -> None:  # noqa: ANN001
    if column not in df.columns:
        findings.append(Finding("ERROR", f"condition column '{column}' is missing from source CSV"))
        return
    series = df[column]
    if series.isna().any():
        findings.append(Finding("ERROR", f"condition column '{column}' contains missing values"))
        return

    if pd.api.types.is_bool_dtype(series):
        true_count = int(series.sum())
        false_count = int((~series).sum())
        if true_count == 0:
            findings.append(Finding("ERROR", f"condition column '{column}' has no TRUE group"))
        if false_count == 0:
            findings.append(Finding("ERROR", f"condition column '{column}' has no FALSE group"))
        return

    parsed = [parse_condition_value(value) for value in series]
    if any(value is None for value in parsed):
        sample = sorted({str(value) for value, parsed_value in zip(series, parsed) if parsed_value is None})[:5]
        findings.append(
            Finding(
                "ERROR",
                f"condition column '{column}' is not boolean and has non-boolean values such as {sample}",
            )
        )
        return

    true_count = sum(1 for value in parsed if value is True)
    false_count = sum(1 for value in parsed if value is False)
    findings.append(
        Finding(
            "ERROR",
            f"condition column '{column}' is condition-like but pandas dtype is {series.dtype}; convert it to a boolean Series before compare_intra()",
        )
    )
    if true_count == 0:
        findings.append(Finding("ERROR", f"condition column '{column}' has no TRUE group after boolean conversion"))
    if false_count == 0:
        findings.append(Finding("ERROR", f"condition column '{column}' has no FALSE group after boolean conversion"))


def inspect_one_csv(pd, role: str, path: Path, findings: list[Finding]):  # noqa: ANN001
    if not path.exists():
        findings.append(Finding("ERROR", f"{role} CSV does not exist: {path}"))
        return None, [], []
    if not path.is_file():
        findings.append(Finding("ERROR", f"{role} CSV is not a file: {path}"))
        return None, [], []

    try:
        header, duplicates = read_csv_header(path)
    except OSError as exc:
        findings.append(Finding("ERROR", f"could not read {role} CSV header: {exc}"))
        return None, [], []

    if not header:
        findings.append(Finding("ERROR", f"{role} CSV has no header row"))
        return None, [], []
    if duplicates:
        findings.append(Finding("ERROR", f"duplicate columns in {role} CSV header: {duplicates}"))

    try:
        df = load_dataframe(pd, path)
    except Exception as exc:
        findings.append(Finding("ERROR", f"could not parse {role} CSV with pandas: {exc}"))
        return None, header, duplicates

    findings.append(Finding("OK", f"loaded {role} CSV with {len(df)} rows and {len(df.columns)} columns"))
    return df, header, duplicates


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        import pandas as pd  # type: ignore
    except ImportError as exc:
        print(f"ERROR: pandas is required to inspect CSV contents: {exc}", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    source_path = Path(args.source_csv)
    compare_path = Path(args.compare_csv) if args.compare_csv else None

    source_df, source_header, _ = inspect_one_csv(pd, "source", source_path, findings)
    compare_df = None
    compare_header: list[str] = []
    if compare_path is not None:
        compare_df, compare_header, _ = inspect_one_csv(pd, "compare", compare_path, findings)

    skip = normalize_features(split_feature_values(args.skip))
    force_cat = normalize_features(split_feature_values(args.force_cat))
    force_text = normalize_features(split_feature_values(args.force_text))
    force_num = normalize_features(split_feature_values(args.force_num))
    target = normalize_feature(args.target)
    condition_column = normalize_feature(args.condition_column)

    feature_sets = {
        "skip": set(skip),
        "force_cat": set(force_cat),
        "force_text": set(force_text),
        "force_num": set(force_num),
    }
    for left_name, left_values in feature_sets.items():
        for right_name, right_values in feature_sets.items():
            if left_name >= right_name:
                continue
            overlap = sorted(left_values & right_values)
            if overlap:
                findings.append(
                    Finding(
                        "WARN",
                        f"features listed in both {left_name} and {right_name}; Sweetviz uses skip > force_cat > force_text > force_num precedence: {overlap}",
                    )
                )

    if source_df is not None:
        normalized_source_columns = columns_after_sweetviz_index_rename(list(source_df.columns))
        normalized_source_set = set(normalized_source_columns)
        if "index" in source_df.columns and "df_index" in source_df.columns:
            findings.append(
                Finding(
                    "WARN",
                    "source has both 'index' and 'df_index'; Sweetviz renames 'index' to 'df_index', which can create ambiguity",
                )
            )

        mentioned = sorted(set(skip + force_cat + force_text + force_num))
        missing = [name for name in mentioned if name not in normalized_source_set]
        if missing:
            findings.append(Finding("ERROR", f"FeatureConfig names missing from source after index normalization: {missing}"))

        if target is not None:
            if target in set(skip):
                findings.append(Finding("ERROR", f"target '{target}' is also listed in skip"))
            if target not in normalized_source_set:
                findings.append(Finding("ERROR", f"target '{target}' is missing from source after index normalization"))
            else:
                source_lookup = dict(zip(normalized_source_columns, source_df.columns))
                target_series = source_df[source_lookup[target]]
                if target_series.isna().any():
                    findings.append(Finding("ERROR", f"target '{target}' contains missing values in source"))
                forced_numeric = target in set(force_num) and target not in set(force_cat) and target not in set(force_text)
                if target in set(force_cat):
                    findings.append(Finding("ERROR", f"target '{target}' is forced categorical; Sweetviz targets must be numeric or boolean"))
                if target in set(force_text):
                    findings.append(Finding("ERROR", f"target '{target}' is forced text; Sweetviz targets must be numeric or boolean"))
                ok_type, reason = sweetviz_numeric_target_like(pd, target_series, forced_numeric)
                if not ok_type:
                    findings.append(Finding("ERROR", f"target '{target}' may be invalid for Sweetviz: {reason}"))

        # Mixed inferred type checks are best-effort for CSV-loaded data.
        skipped = set(skip)
        source_lookup = dict(zip(normalized_source_columns, source_df.columns))
        for normalized_name, original_name in source_lookup.items():
            if normalized_name in skipped:
                continue
            inferred = maybe_mixed_inferred_type(source_df[original_name])
            if inferred:
                findings.append(
                    Finding(
                        "ERROR",
                        f"source column '{normalized_name}' has unsupported mixed inferred type '{inferred}'; clean dtype before Sweetviz",
                    )
                )

        if condition_column:
            check_condition_column(pd, source_df.rename(columns={"index": "df_index"}), condition_column, findings)

    if compare_df is not None:
        normalized_compare_columns = columns_after_sweetviz_index_rename(list(compare_df.columns))
        normalized_compare_set = set(normalized_compare_columns)
        if "index" in compare_df.columns and "df_index" in compare_df.columns:
            findings.append(
                Finding(
                    "WARN",
                    "compare has both 'index' and 'df_index'; Sweetviz renames 'index' to 'df_index', which can create ambiguity",
                )
            )
        if target is not None and target in normalized_compare_set:
            compare_lookup = dict(zip(normalized_compare_columns, compare_df.columns))
            compare_target_series = compare_df[compare_lookup[target]]
            if compare_target_series.isna().any():
                findings.append(Finding("ERROR", f"target '{target}' contains missing values in compare"))

        skipped = set(skip)
        compare_lookup = dict(zip(normalized_compare_columns, compare_df.columns))
        for normalized_name, original_name in compare_lookup.items():
            if normalized_name in skipped:
                continue
            inferred = maybe_mixed_inferred_type(compare_df[original_name])
            if inferred:
                findings.append(
                    Finding(
                        "ERROR",
                        f"compare column '{normalized_name}' has unsupported mixed inferred type '{inferred}'; clean dtype before Sweetviz",
                    )
                )

        if source_header and compare_header:
            source_names = set(columns_after_sweetviz_index_rename(source_header))
            compare_names = set(columns_after_sweetviz_index_rename(compare_header))
            compare_only = sorted(compare_names - source_names)
            if compare_only:
                findings.append(
                    Finding(
                        "WARN",
                        f"compare CSV has columns not present in source; Sweetviz summarizes the count but analyzes source-driven feature names: {compare_only}",
                    )
                )

    errors = sum(1 for finding in findings if finding.level == "ERROR")
    warnings = sum(1 for finding in findings if finding.level == "WARN")

    for finding in findings:
        print(str(finding))
    print(f"SUMMARY: {errors} error(s), {warnings} warning(s)")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
