#!/usr/bin/env python3
"""Tiny smoke test for StatsForecast MSTL feature engineering.

Builds deterministic daily panel data, runs MSTL(season_length=7)
feature decomposition, and asserts that the returned future X_df has the
expected rows and component columns. In auto mode, pandas is always tested and
polars is tested only when importable.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from typing import Iterable


def _import_or_exit():
    try:
        import pandas as pd
        from statsforecast.feature_engineering import mstl_decomposition
        from statsforecast.models import MSTL
        from statsforecast.utils import generate_series
    except Exception as exc:  # pragma: no cover - depends on caller environment
        print(f"missing runtime dependency: {exc}", file=sys.stderr)
        print(
            "Install statsforecast with pandas support before running this smoke test.",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    return pd, mstl_decomposition, MSTL, generate_series


def _polars_available() -> bool:
    return importlib.util.find_spec("polars") is not None


def _num_rows(df) -> int:
    return int(getattr(df, "height", df.shape[0]))


def _columns(df) -> list[str]:
    return list(df.columns)


def _to_pandas(df):
    if hasattr(df, "to_pandas"):
        return df.to_pandas()
    return df


def _shuffle(df, engine: str):
    if engine == "polars":
        return df.sample(fraction=1.0, shuffle=True, seed=42)
    return df.sample(frac=1.0, random_state=42).reset_index(drop=True)


def _build_panel(engine: str, n_series: int, length: int, seed: int):
    _, _, _, generate_series = _import_or_exit()
    if engine == "polars":
        if not _polars_available():
            raise RuntimeError("polars is not installed")
        import polars as pl

        df = generate_series(
            n_series=n_series,
            freq="D",
            min_length=length,
            max_length=length,
            n_static_features=0,
            equal_ends=True,
            engine="polars",
            seed=seed,
        )
        if str(df.schema.get("unique_id")) == "Categorical":
            return df.with_columns(pl.col("unique_id").cat.physical().cast(pl.Int64))
        return df.with_columns(pl.col("unique_id").cast(pl.Int64))

    df = generate_series(
        n_series=n_series,
        freq="D",
        min_length=length,
        max_length=length,
        n_static_features=0,
        equal_ends=True,
        engine="pandas",
        seed=seed,
    )
    df["unique_id"] = df["unique_id"].astype("int64")
    return df


def _validate_future_rows(train_df, X_df, h: int, pd) -> None:
    train_pd = _to_pandas(train_df)
    x_pd = _to_pandas(X_df)

    n_ids = train_pd["unique_id"].nunique()
    expected_rows = n_ids * h
    assert _num_rows(X_df) == expected_rows, (
        f"expected {expected_rows} future rows, got {_num_rows(X_df)}"
    )

    counts = x_pd.groupby("unique_id").size()
    assert (counts == h).all(), f"expected {h} future rows per id, got {counts.to_dict()}"

    expected_first = train_pd.groupby("unique_id")["ds"].max() + pd.offsets.Day()
    observed_first = x_pd.groupby("unique_id")["ds"].min()
    pd.testing.assert_series_equal(
        observed_first.sort_index(),
        expected_first.sort_index(),
        check_names=False,
    )

    required_cols = {"unique_id", "ds", "trend", "seasonal"}
    missing = sorted(required_cols.difference(_columns(X_df)))
    assert not missing, f"X_df is missing columns {missing}"
    assert "y" not in _columns(X_df), "future X_df must not contain y"

    train_missing = sorted({"trend", "seasonal"}.difference(_columns(train_df)))
    assert not train_missing, f"train_df is missing columns {train_missing}"



def run_engine(engine: str, h: int, n_series: int, length: int, seed: int) -> None:
    pd, mstl_decomposition, MSTL, _ = _import_or_exit()
    df = _shuffle(_build_panel(engine, n_series=n_series, length=length, seed=seed), engine)
    freq = "1d" if engine == "polars" else "D"
    train_df, X_df = mstl_decomposition(df, MSTL(season_length=7), freq=freq, h=h)
    _validate_future_rows(train_df, X_df, h=h, pd=pd)
    print(
        f"{engine}: ok rows={_num_rows(X_df)} columns={','.join(_columns(X_df))}",
        flush=True,
    )


def _engines_to_run(requested: str) -> Iterable[str]:
    if requested == "auto":
        yield "pandas"
        if _polars_available():
            yield "polars"
        else:
            print("polars: skipped (not installed)", flush=True)
        return
    yield requested


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a tiny StatsForecast MSTL feature-engineering smoke test."
    )
    parser.add_argument(
        "--engine",
        choices=("auto", "pandas", "polars"),
        default="auto",
        help="Dataframe engine to test. Auto runs pandas and polars if polars is installed.",
    )
    parser.add_argument("--horizon", type=int, default=7, help="Future rows per series.")
    parser.add_argument("--n-series", type=int, default=3, help="Number of panel series.")
    parser.add_argument(
        "--length",
        type=int,
        default=42,
        help="Training observations per series; keep above several weekly cycles.",
    )
    parser.add_argument("--seed", type=int, default=123, help="Synthetic data seed.")
    args = parser.parse_args(argv)

    if args.horizon <= 0:
        parser.error("--horizon must be positive")
    if args.n_series <= 0:
        parser.error("--n-series must be positive")
    if args.length < 21:
        parser.error("--length must be at least 21 for this weekly MSTL smoke test")
    if args.engine == "polars" and not _polars_available():
        parser.error("--engine polars requested but polars is not installed")

    for engine in _engines_to_run(args.engine):
        run_engine(
            engine=engine,
            h=args.horizon,
            n_series=args.n_series,
            length=args.length,
            seed=args.seed,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
