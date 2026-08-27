#!/usr/bin/env python3
"""Compute aggregate relative scores for Chronos evaluation CSVs.

This helper compares one model result CSV against one baseline CSV,
validates that their dataset rows and metric columns match, then computes
geometric-mean relative scores per metric.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

METADATA_COLUMNS = {"dataset", "model"}


def geometric_mean(values: pd.Series) -> float:
    arr = values.to_numpy(dtype=float)
    if arr.size == 0:
        raise ValueError("Cannot compute a geometric mean over an empty series.")
    if np.any(arr <= 0):
        raise ValueError("Relative scores must be strictly positive to compute a geometric mean.")
    return float(np.exp(np.log(arr).mean()))


def load_score_table(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [col for col in METADATA_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")
    if df["dataset"].duplicated().any():
        duplicated = df.loc[df["dataset"].duplicated(), "dataset"].tolist()
        raise ValueError(f"{path} contains duplicate dataset names: {duplicated}")

    metric_columns = [col for col in df.columns if col not in METADATA_COLUMNS]
    if not metric_columns:
        raise ValueError(f"{path} does not contain any metric columns")

    df = df.set_index("dataset")
    df[metric_columns] = df[metric_columns].apply(pd.to_numeric, errors="raise")
    return df[metric_columns]


def compute_relative_scores(model_csv: Path, baseline_csv: Path) -> pd.DataFrame:
    model_df = load_score_table(model_csv)
    baseline_df = load_score_table(baseline_csv)

    if set(model_df.columns) != set(baseline_df.columns):
        model_only = sorted(set(model_df.columns) - set(baseline_df.columns))
        baseline_only = sorted(set(baseline_df.columns) - set(model_df.columns))
        raise ValueError(
            "Metric columns do not match between the model and baseline CSVs. "
            f"model_only={model_only}, baseline_only={baseline_only}"
        )

    if set(model_df.index) != set(baseline_df.index):
        model_only = sorted(set(model_df.index) - set(baseline_df.index))
        baseline_only = sorted(set(baseline_df.index) - set(model_df.index))
        raise ValueError(
            "Dataset rows do not match between the model and baseline CSVs. "
            f"model_only={model_only}, baseline_only={baseline_only}"
        )

    # Sort and align so the ratio is computed row-by-row on matching datasets.
    model_df = model_df.sort_index()
    baseline_df = baseline_df.sort_index().reindex(model_df.index)

    relative = model_df / baseline_df
    agg = relative.agg(geometric_mean).rename_axis("metric").reset_index(name="value")
    return agg


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compute aggregate relative scores for one model CSV against one baseline CSV.",
    )
    parser.add_argument("--model-csv", type=Path, required=True, help="Path to the model result CSV.")
    parser.add_argument("--baseline-csv", type=Path, required=True, help="Path to the baseline result CSV.")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output CSV path. If omitted, the result is printed to stdout.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    result = compute_relative_scores(args.model_csv, args.baseline_csv)
    csv_text = result.to_csv(index=False)

    if args.output is None:
        sys.stdout.write(csv_text)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(csv_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
