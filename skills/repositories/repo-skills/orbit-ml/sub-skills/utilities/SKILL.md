---
name: utilities
description: "Use Orbit utility helpers for sample datasets, synthetic
  time-series, Fourier and seasonal features, knot placement, full-span
  dataframe expansion, quick parameter-grid setup, and EDA plots."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Utilities

Use this sub-skill when a task is about Orbit data preparation, synthetic series, feature engineering, knot selection, dataframe expansion, quick tuning-grid construction, or diagnostic EDA plots.

## Read this when

- The user needs a sample dataset, an example data shape, or a loader-backed tutorial frame.
- The user needs synthetic time-series for a smoke check, demo, or reproducible toy example.
- The user needs Fourier regressors, seasonal dummies, or seasonal regressor blocks.
- The user needs knot indices or knot dates for KTR/KTRLite-style workflows.
- The user needs a full-span multi-series dataframe or a way to restore missing key/date rows.
- The user needs a quick parameter-grid helper or the grid-search call shape.
- The user needs EDA plots for a time series, correlation matrix, or panel view.

## What this sub-skill owns

- Network-loaded sample dataset helpers in `orbit.utils.dataset`.
- Synthetic series helpers in `orbit.utils.simulation`.
- Fourier / seasonal feature builders in `orbit.utils.features`.
- Knot/date alignment helpers in `orbit.utils.knots`.
- Generic dataframe helpers in `orbit.utils.general`.
- Parameter-grid helpers in `orbit.utils.params_tuning`.
- EDA plots in `orbit.eda.eda_plot`.

## What this sub-skill does not own

- Primary model fit/predict workflows for ETS, LGT, DLT, KTR, or KTRLite.
- Backtesting, forecast scoring, residual diagnostics, or evaluation workflows except for helper-level tuning inputs.
- Backend compilation or model-estimator internals.

## Start here

1. If you need a loader, read `references/data-loaders.md` and remember the loaders are network-dependent.
2. If you need synthetic data, feature engineering, or knot placement, read `references/workflow-recipes.md`.
3. If you need exact signatures, edge conditions, or output columns, read `references/api-reference.md`.
4. If you hit a failure, open `references/troubleshooting.md`.
5. Run `python scripts/smoke_utilities.py` for a network-free synthetic smoke check.

## Fast routing cheatsheet

- Need a sample dataset: use a loader only when network access is acceptable; otherwise build a synthetic frame with `make_trend`, `make_seasonality`, or `make_regression`.
- Need synthetic trend: use `make_trend(..., method="rw")` for reproducible smoke checks; the `arma` branch is not seed-stable in this version.
- Need seasonality features: use `make_fourier_series_df` for Fourier regressors and `make_seasonal_dummies` for weekday/month dummies. Treat `freq="week"` as version-sensitive on pandas 3.x.
- Need knot placement: use `get_knot_idx` first, then map back with `get_knot_dates`.
- Need a full-span panel: use `expand_grid`; use `regenerate_base_df` to fill missing key/date combinations that still exist in the observed unique keys and dates.
- Need a tuning grid: use `generate_param_args_list` to expand the search space; `grid_search_orbit` validates arguments but real tuning belongs with the model workflow that owns the fitted model.
- Need plots: use `ts_heatmap`, `correlation_heatmap`, `dual_axis_ts_plot`, or `wrap_plot_ts`; pass `use_orbit_style=False` if the default Orbit style causes font warnings.

## Good entry points

- `from orbit.utils.dataset import load_iclaims, load_m4weekly, load_m5daily, load_m3monthly, load_electricity_demand, load_air_passengers, load_energy_hourly`
- `from orbit.utils.simulation import make_trend, make_seasonality, make_regression`
- `from orbit.utils.features import make_fourier_series, make_fourier_series_df, make_seasonal_dummies, make_seasonal_regressors, moving_average`
- `from orbit.utils.knots import get_knot_idx, get_knot_dates, get_knot_idx_by_dist, get_dates_delta`
- `from orbit.utils.general import expand_grid, regenerate_base_df, is_ordered_datetime, is_even_gap_datetime, is_empty_dataframe, update_dict, get_parent_path`
- `from orbit.utils.params_tuning import generate_param_args_list, grid_search_orbit`
- `from orbit.eda import eda_plot`
- `python scripts/smoke_utilities.py` for the bundled offline check
