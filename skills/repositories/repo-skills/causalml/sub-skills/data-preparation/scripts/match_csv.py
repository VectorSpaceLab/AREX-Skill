#!/usr/bin/env python
"""CSV helper for CausalML propensity-score matching.

The helper reads a CSV, optionally estimates a propensity score from feature
columns, performs nearest-neighbor matching, prints balance tables when
possible, and writes a matched CSV.
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, Sequence

import pandas as pd

from causalml.features import load_data
from causalml.match import NearestNeighborMatch, create_table_one
from causalml.propensity import ElasticNetPropensityModel


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Match treated and control rows in a CSV with CausalML."
    )
    parser.add_argument("--input", "--input-file", required=True, dest="input_file")
    parser.add_argument("--output", "--output-file", required=True, dest="output_file")
    parser.add_argument(
        "--treatment-column",
        "--treatment-col",
        default="treatment",
        dest="treatment_col",
        help="Binary treatment column; values must be castable to 0/1.",
    )
    parser.add_argument(
        "--feature-columns",
        "--feature-cols",
        nargs="+",
        default=None,
        dest="feature_cols",
        help="Pre-treatment feature columns used to estimate a propensity score.",
    )
    parser.add_argument(
        "--matching-covariates",
        "--matching-cols",
        nargs="+",
        required=True,
        dest="matching_covariates",
        help="Numeric covariates printed in balance tables before and after matching.",
    )
    parser.add_argument(
        "--groupby-column",
        "--groupby-col",
        default=None,
        dest="groupby_col",
        help="Optional exact stratum column for match_by_group.",
    )
    parser.add_argument(
        "--score-column",
        "--score-col",
        default="score",
        dest="score_col",
        help="Propensity or distance score column. Existing values are reused unless --force-propensity is set.",
    )
    parser.add_argument("--caliper", type=float, default=0.2)
    parser.add_argument("--replace", action="store_true", help="Allow matching with replacement.")
    parser.add_argument("--ratio", type=int, default=1, help="Opposite-arm matches per source unit.")
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument(
        "--force-propensity",
        action="store_true",
        help="Estimate and overwrite --score-column from --feature-columns even if it already exists.",
    )
    parser.add_argument(
        "--use-matching-covariates",
        action="store_true",
        help=(
            "When --replace is set, match on --score-column plus matching "
            "covariates instead of score only."
        ),
    )
    return parser


def _require_columns(df: pd.DataFrame, columns: Iterable[str], role: str) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing {role} column(s): {', '.join(missing)}")


def _prepare_treatment(df: pd.DataFrame, treatment_col: str) -> None:
    _require_columns(df, [treatment_col], "treatment")
    try:
        df[treatment_col] = df[treatment_col].astype(int)
    except Exception as exc:  # pragma: no cover - message path
        raise ValueError(
            f"Treatment column {treatment_col!r} must be castable to binary integers 0/1"
        ) from exc

    values = set(df[treatment_col].dropna().unique().tolist())
    if values != {0, 1}:
        raise ValueError(
            f"Treatment column {treatment_col!r} must contain both 0 and 1; found {sorted(values)}"
        )


def _coerce_numeric(df: pd.DataFrame, columns: Sequence[str], role: str) -> None:
    for col in columns:
        try:
            df[col] = pd.to_numeric(df[col], errors="raise")
        except Exception as exc:  # pragma: no cover - message path
            raise ValueError(f"{role} column {col!r} must be numeric") from exc


def _print_balance(label: str, df: pd.DataFrame, treatment_col: str, features: Sequence[str]) -> None:
    print(f"\n{label}")
    try:
        table = create_table_one(
            data=df,
            treatment_col=treatment_col,
            features=list(features),
        )
    except Exception as exc:
        print(f"Could not compute balance table: {exc}", file=sys.stderr)
        return
    print(table.to_string())


def _ensure_score(df: pd.DataFrame, args: argparse.Namespace) -> None:
    score_exists = args.score_col in df.columns
    if score_exists and not args.force_propensity:
        _coerce_numeric(df, [args.score_col], "score")
        print(f"Using existing score column: {args.score_col}")
        return

    if not args.feature_cols:
        raise ValueError(
            "--feature-columns is required when the score column is absent or --force-propensity is used"
        )
    _require_columns(df, args.feature_cols, "feature")
    X = load_data(data=df, features=args.feature_cols)
    treatment = df[args.treatment_col].values
    model = ElasticNetPropensityModel(random_state=args.random_state)
    df[args.score_col] = model.fit_predict(X, treatment)
    print(f"Computed propensity scores into column: {args.score_col}")


def _score_columns(df: pd.DataFrame, args: argparse.Namespace) -> list[str]:
    score_cols = [args.score_col]
    if args.use_matching_covariates:
        if not args.replace:
            raise ValueError("--use-matching-covariates requires --replace because multi-column matching is replacement-only")
        for col in args.matching_covariates:
            if col not in score_cols:
                score_cols.append(col)
    _require_columns(df, score_cols, "matching score")
    _coerce_numeric(df, score_cols, "matching score")
    return score_cols


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    try:
        if args.ratio < 1:
            raise ValueError("--ratio must be at least 1")
        if args.caliper <= 0:
            raise ValueError("--caliper must be positive")

        df = pd.read_csv(args.input_file)
        _prepare_treatment(df, args.treatment_col)
        _require_columns(df, args.matching_covariates, "matching covariate")
        if args.groupby_col:
            _require_columns(df, [args.groupby_col], "groupby")

        _ensure_score(df, args)
        score_cols = _score_columns(df, args)

        print(f"Loaded input shape: {df.shape}")
        print(f"Treatment counts before matching: {df[args.treatment_col].value_counts().sort_index().to_dict()}")
        _print_balance("Balance before matching:", df, args.treatment_col, args.matching_covariates)

        matcher = NearestNeighborMatch(
            caliper=args.caliper,
            replace=args.replace,
            ratio=args.ratio,
            random_state=args.random_state,
        )
        if args.groupby_col:
            matched = matcher.match_by_group(
                data=df,
                treatment_col=args.treatment_col,
                score_cols=score_cols,
                groupby_col=args.groupby_col,
            )
        else:
            matched = matcher.match(
                data=df,
                treatment_col=args.treatment_col,
                score_cols=score_cols,
            )

        print(f"Matched output shape: {matched.shape}")
        if not matched.empty:
            print(
                "Treatment counts after matching: "
                f"{matched[args.treatment_col].value_counts().sort_index().to_dict()}"
            )
            _print_balance("Balance after matching:", matched, args.treatment_col, args.matching_covariates)
        else:
            print("Matched output is empty; no after-match balance table was computed.", file=sys.stderr)

        matched.to_csv(args.output_file, index=False)
        print(f"Matched CSV written to: {args.output_file}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
