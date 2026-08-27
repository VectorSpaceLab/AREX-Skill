#!/usr/bin/env python3
"""Network-free smoke check for Orbit utility helpers.

This script exercises only synthetic or pure helper paths. It does not load
remote sample datasets or fit Orbit models.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from dataclasses import dataclass

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pandas as pd

try:
    from orbit.eda.eda_plot import correlation_heatmap, dual_axis_ts_plot, ts_heatmap, wrap_plot_ts
    from orbit.exceptions import IllegalArgument
    from orbit.utils.features import (
        make_fourier_series,
        make_fourier_series_df,
        make_seasonal_dummies,
        make_seasonal_regressors,
        moving_average,
    )
    from orbit.utils.general import (
        expand_grid,
        is_empty_dataframe,
        is_even_gap_datetime,
        is_ordered_datetime,
        regenerate_base_df,
        update_dict,
    )
    from orbit.utils.knots import get_dates_delta, get_knot_dates, get_knot_idx, get_knot_idx_by_dist
    from orbit.utils.params_tuning import generate_param_args_list, grid_search_orbit
    from orbit.utils.simulation import make_regression, make_seasonality, make_trend
except ModuleNotFoundError as exc:
    print(f"utilities smoke missing dependency: {exc}", file=sys.stderr)
    raise SystemExit(2)


@dataclass
class SmokeResult:
    trend_len: int
    season_len: int
    regression_shape: tuple[int, int]
    fourier_shape: tuple[int, int]
    seasonal_dummy_cols: list[str]
    knot_idx: list[int]
    grid_count: int
    panel_rows: int
    eda_checked: bool


def _assert_raises(expected_exc, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except expected_exc:
        return
    raise AssertionError(f"Expected {expected_exc.__name__} from {fn.__name__}")


def build_synthetic_frame(seed: int = 2024):
    n = 36
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    trend = make_trend(n, method="rw", rw_loc=0.01, rw_scale=0.05, seed=seed)
    season = make_seasonality(n, seasonality=7, method="fourier", order=2, seed=seed)
    x, reg, _coefs = make_regression(
        n,
        coefs=[0.3, -0.2],
        scale=0.2,
        noise_scale=0.01,
        sparsity=0.0,
        relevance=1.0,
        seed=seed,
    )

    df = pd.DataFrame(
        {
            "date": dates,
            "y": trend + season + reg,
            "x1": x[:, 0],
            "x2": x[:, 1],
        }
    )
    return df, trend, season, x, reg, _coefs


def run_smoke(include_eda: bool = True) -> SmokeResult:
    df, trend, season, x, reg, coefs = build_synthetic_frame()

    fs = make_fourier_series(n=len(df), period=7, order=2)
    fs_df, fs_cols = make_fourier_series_df(df[["date"]].copy(), period=7, order=2, prefix="weekly_")
    assert fs.shape == (len(df), 4)
    assert fs_df.shape[0] == len(df)
    assert len(fs_cols) == 4

    df, wd_cols = make_seasonal_dummies(df.copy(), "date", freq="weekday", sparse=False)
    assert len(wd_cols) == 6

    reg_blocks = make_seasonal_regressors(
        n=len(df), periods=[7, 365.25], orders=[2, 1], labels=["weekly", "yearly"]
    )
    assert reg_blocks["weekly"].shape == (len(df), 4)
    assert reg_blocks["yearly"].shape == (len(df), 2)

    moving = moving_average(np.array([1.0, 2.0, 3.0, 4.0]), window=2)
    assert np.allclose(moving, np.array([0.5, 1.5, 2.5, 3.5]))

    weekly = pd.date_range("2024-01-07", periods=12, freq="W-SUN")
    knot_idx = get_knot_idx(num_of_obs=len(weekly), num_of_segments=3)
    knot_dates = get_knot_dates(weekly[0], knot_idx, pd.infer_freq(weekly))
    round_trip = np.asarray(get_knot_idx(date_array=weekly, knot_dates=knot_dates))
    assert np.array_equal(round_trip, knot_idx)
    assert np.array_equal(get_knot_idx_by_dist(len(weekly), 3), np.array([0, 2, 5, 8, 11]))
    assert np.array_equal(get_dates_delta(weekly[0], knot_dates, np.timedelta64(7, "D")), knot_idx)

    assert is_ordered_datetime(weekly)
    assert is_even_gap_datetime(weekly)
    assert is_empty_dataframe(pd.DataFrame())
    assert update_dict({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}

    panel = expand_grid({
        "series_id": ["north", "south"],
        "date": pd.date_range("2024-01-31", periods=4, freq="ME"),
    })
    panel = panel.assign(y=np.arange(len(panel), dtype=float))
    panel_missing = panel.drop(index=[2]).reset_index(drop=True)
    panel_full = regenerate_base_df(panel_missing, "date", "series_id", val_cols=["y"], fill_na=0.0)
    assert panel_full.shape[0] == panel.shape[0]
    assert panel_full["y"].isna().sum() == 0

    grid = generate_param_args_list({"b": [1, 2], "a": ["x"]})
    assert grid == [{"a": "x", "b": 1}, {"a": "x", "b": 2}]
    _assert_raises(TypeError, generate_param_args_list, 123)
    _assert_raises(IllegalArgument, grid_search_orbit, {}, None, pd.DataFrame(), eval_method="invalid")
    _assert_raises(IllegalArgument, grid_search_orbit, {}, None, pd.DataFrame(), criteria="median")

    if include_eda:
        heatmap_ax, heatmap_df, heatmap_pivot = ts_heatmap(
            df=df.rename(columns={"y": "value"}),
            date_col="date",
            value_col="value",
            seasonal_interval=7,
            use_orbit_style=False,
        )
        corr_ax = correlation_heatmap(df, ["x1", "x2"], use_orbit_style=False)
        dual_ax = dual_axis_ts_plot(df, "x1", "x2", "date", use_orbit_style=False)
        facet = wrap_plot_ts(df, "date", ["date", "x1", "x2"], use_orbit_style=False)
        _ = (heatmap_ax, heatmap_df, heatmap_pivot, corr_ax, dual_ax, facet)

    result = SmokeResult(
        trend_len=len(trend),
        season_len=len(season),
        regression_shape=x.shape,
        fourier_shape=fs.shape,
        seasonal_dummy_cols=wd_cols,
        knot_idx=knot_idx.tolist(),
        grid_count=len(grid),
        panel_rows=panel_full.shape[0],
        eda_checked=include_eda,
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-eda", action="store_true", help="Skip the plotting helpers.")
    parser.add_argument("--json", action="store_true", help="Print the smoke result as JSON.")
    args = parser.parse_args(argv)

    warnings.filterwarnings("ignore", category=FutureWarning)
    result = run_smoke(include_eda=not args.skip_eda)

    payload = {
        "trend_len": result.trend_len,
        "season_len": result.season_len,
        "regression_shape": list(result.regression_shape),
        "fourier_shape": list(result.fourier_shape),
        "seasonal_dummy_cols": result.seasonal_dummy_cols,
        "knot_idx": result.knot_idx,
        "grid_count": result.grid_count,
        "panel_rows": result.panel_rows,
        "eda_checked": result.eda_checked,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("Orbit utilities smoke check passed")
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
