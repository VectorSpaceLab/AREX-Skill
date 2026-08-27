# Plotting and diagnostics

## Purpose

Use this file when you need to inspect forecast plots, decomposition outputs, residual diagnostics, or the exploratory plots that often accompany an evaluation pass. The `orbit.diagnostics.plot` module imports `statsmodels` at import time, so install that dependency before using any of the plot helpers.

## Forecast plots

### `plot_predicted_data()`

Use this for one fitted model and one prediction dataframe.

- Requires a non-empty training dataframe and a non-empty prediction dataframe.
- Expects `predicted_df` dates to be strictly ordered.
- If you pass test actuals, they are overlaid as a second observation series.
- Confidence bands appear only when the lower/upper percentile columns are present.

Good trigger phrases:

- "plot train vs forecast"
- "show holdout predictions"
- "add prediction intervals"

### `plot_predicted_components()`

Use this after `predict(..., decompose=True)` when you want to inspect component-level forecasts.

- Default components are `trend`, `seasonality`, and `regression`.
- `plot_components` can narrow or extend the display set.
- Only components present in the dataframe are plotted.
- Prediction interval bands are drawn when matching percentile columns exist.

Good trigger phrases:

- "decompose the forecast"
- "inspect trend and seasonality separately"
- "plot forecast components"

## Backtest plots

### `plot_bt_predictions()`

Use this when you want a small grid of backtest folds with actuals and predictions overlaid.

- Expects the dataframe returned by `BackTester.get_predicted_df()` with `date`, `actual`, `prediction`, `training_data`, and `split_key` columns.
- Computes the per-split metric value from the provided callable.
- Draws a vertical cutoff line by default.
- Use `split_key_list` to focus on a subset of folds.
- Best when you want a compact comparison across multiple splits.

### `plot_bt_predictions2()`

Use this when you want one figure per split or a directory of saved split images.

- Expects the same backtest dataframe columns as `plot_bt_predictions()`.
- `fig_dir` must exist before use.
- `fix_xylim=True` keeps the axis ranges comparable across folds.
- `export_gif=True` additionally requires `imageio`.

Good trigger phrases:

- "save one plot per fold"
- "animate the backtest"
- "compare split plots consistently"

## Residual diagnostics

### `residual_diagnostic_plot()`

Use this after you have residuals and fitted values available in a dataframe. The helper is mainly for side effects and visual inspection; it does not return a structured diagnostic table.

It renders:

1. residual by time
2. residual vs fitted
3. residual distribution
4. QQ plot
5. residual ACF
6. residual PACF

Requirements and cautions:

- `statsmodels` must be installed.
- Use `dist="norm"` for the standard QQ plot or `dist="t-dist"` with `sparams`.
- The input dataframe should contain the residual and fitted columns you name.
- ACF/PACF plots work best when there are enough residual observations.

Good trigger phrases:

- "check residual autocorrelation"
- "inspect fitted vs residual"
- "look at diagnostics after forecasting"

## Exploratory plotting overlap

The EDA surface is useful when the evaluation task also needs a quick look at the series structure or driver relationships.

### `ts_heatmap()`

Use for seasonal pattern inspection, especially when the series has a repeat interval such as 7 or 52.

### `correlation_heatmap()`

Use for quick pairwise correlation screening among candidate regressors or diagnostic variables.

### `dual_axis_ts_plot()`

Use for two-series comparison when the scales differ but the timing matters.

### `wrap_plot_ts()`

Use for a small panel of line charts across many variables.

## Posterior-sample diagnostics

The model diagnostics notebook demonstrates ArviZ-based posterior checks such as trace, pair, density, and forest plots.
Use those when you already have posterior samples and need chain-level inspection; they are adjacent to evaluation, but not part of the core backtest workflow.
