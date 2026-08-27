# Utilities API Reference

This reference distills the utility helpers that future Orbit sessions most often need.

## Synthetic data helpers

### `make_trend`

```python
make_trend(series_len, method="rw", arma=[0.25, 0.6], rw_loc=0.0, rw_scale=0.1, seed=1)
```

- `method="rw"` builds a seeded random-walk trend and is the safest smoke-check path.
- `method="arma"` uses `statsmodels` ARMA sampling. In this version the seed is not propagated into the ARMA sampler, so repeated calls can differ.
- Returns a 1-D NumPy array.

### `make_seasonality`

```python
make_seasonality(series_len, seasonality, method="discrete", order=3, duration=1, scale=0.05, seed=1)
```

- `method="discrete"` repeats a seasonal pattern; `duration` controls how long each seasonal value is repeated.
- `method="fourier"` returns a Fourier-style seasonal waveform.
- Returns a 1-D NumPy array.

### `make_regression`

```python
make_regression(
    series_len,
    coefs,
    loc=0.0,
    scale=0.5,
    cov=None,
    noise_scale=1.0,
    bias=None,
    relevance=1.0,
    sparsity=0.2,
    seed=1,
)
```

- Returns `(x, y, coefs)` where `x` is 2-D, `y` is 1-D, and `coefs` may be modified by relevance/sparsity.
- Use `cov` when you want correlated regressors.
- `relevance` should stay at `0.0` or `1.0` for reproducible smoke checks; the intermediate branch uses an unseeded coefficient-drop step.

## Feature helpers

### `make_fourier_series`

```python
make_fourier_series(n, period, order=3, shift=0)
```

Returns a 2-D array with alternating cosine and sine columns for the requested order.

### `make_fourier_series_df`

```python
make_fourier_series_df(df, period, order=3, prefix="", suffix="", shift=0)
```

Returns `(out, fs_cols)` where `out` is the input frame with Fourier columns appended and `fs_cols` is the ordered column-name list.

### `make_seasonal_dummies`

```python
make_seasonal_dummies(df, date_col, freq, sparse=True, drop_first=True)
```

- Supported `freq` values in the source are `weekday`, `month`, and `week`.
- `weekday` and `month` are safe on the current pandas runtime.
- The `week` branch is version-sensitive because pandas 3.x removed `Series.dt.week`.
- Returns `(out, cols)`.

### `make_seasonal_regressors`

```python
make_seasonal_regressors(n, periods, orders, labels, shift=0)
```

- Returns a dictionary keyed by the supplied labels.
- `periods`, `orders`, and `labels` must have the same length; the helper indexes them positionally.

### `moving_average`

```python
moving_average(x, window=1, mode="same")
```

- Thin wrapper around `numpy.convolve`.
- `window` should be a positive integer.

## Knot helpers

### `get_knot_idx`

```python
get_knot_idx(
    num_of_obs=None,
    num_of_segments=None,
    knot_distance=None,
    date_array=None,
    knot_dates=None,
)
```

- Use one of three modes: segment count, fixed distance, or explicit dates.
- When `knot_dates` is provided, `date_array` is required.
- When dates are provided, the helper filters out-of-range dates and rounds by the inferred time delta.

### `get_knot_dates`

```python
get_knot_dates(start_date, knot_idx, freq)
```

- Maps indices back to dates using a regular date range starting at `start_date`.
- Works best when `knot_idx` came from a regularly spaced `date_array`.

### `get_knot_idx_by_dist`

```python
get_knot_idx_by_dist(num_of_obs, knot_distance)
```

- Computes knot locations by distance and always includes index `0`.

### `get_dates_delta`

```python
get_dates_delta(start_date, end_date, time_delta)
```

- Converts date differences into index offsets, rounded to integers.

## Generic dataframe helpers

### `expand_grid`

```python
expand_grid(base)
```

- Expands a dictionary of iterables into the full cross-product dataframe.

### `regenerate_base_df`

```python
regenerate_base_df(df, time_col, key_col, val_cols=[], fill_na=None)
```

- Rebuilds a full key/time cross-product from the unique keys and times that are still present in `df`.
- `fill_na` can backfill selected value columns after the merge.

### `is_ordered_datetime`

```python
is_ordered_datetime(array)
```

- Returns `True` when datetime values are strictly increasing.

### `is_even_gap_datetime`

```python
is_even_gap_datetime(array)
```

- Returns `True` when pandas can infer a regular frequency.

### `is_empty_dataframe`

```python
is_empty_dataframe(df)
```

- Returns `True` for `None` or an empty dataframe.

### `update_dict`

```python
update_dict(original_dict, append_dict)
```

- Returns a deep-copied dictionary with `append_dict` merged in.

### `get_parent_path`

```python
get_parent_path(current_file_path)
```

- Convenience wrapper around `os.path.abspath(os.path.join(..., os.pardir))`.

## Grid-search helpers

### `generate_param_args_list`

```python
generate_param_args_list(param_grid)
```

- Accepts a dict or a list of dicts.
- Sorts keys for reproducibility.
- Returns a list of parameter dictionaries.

### `grid_search_orbit`

```python
grid_search_orbit(
    param_grid,
    model,
    df,
    eval_method="backtest",
    min_train_len=None,
    incremental_len=None,
    forecast_len=None,
    n_splits=None,
    metrics=None,
    criteria="min",
    verbose=False,
    **kwargs,
)
```

- `eval_method` must be `backtest` or `bic`.
- `criteria` must be `min` or `max`; `bic` forces `min`.
- `bic` works only with a MAP-backed forecaster.
- Tuned parameter names must exist in the model template, model wrapper, or estimator objects.
- Returns `(best_params, tuned_df)`.

## EDA helpers

The plotting helpers accept `use_orbit_style=False` through Orbit's plot decorator, even though that keyword is not part of the explicit function signature.

### `ts_heatmap`

```python
ts_heatmap(df, date_col, value_col, seasonal_interval, fig_width=8, fig_height=8, normalization=False, path=None, palette=...)
```

Returns `(ax, df, df_pivot)`.

### `correlation_heatmap`

```python
correlation_heatmap(df, var_list, fig_width=8, fig_height=8, path=None, fmt=".1g", palette=...)
```

Returns the heatmap axes. Columns that are all zero are skipped.

### `dual_axis_ts_plot`

```python
dual_axis_ts_plot(df, var1, var2, date_col, fig_width=25, fig_height=6, path=None, color1=..., color2=...)
```

Returns the primary axes for the dual-axis chart.

### `wrap_plot_ts`

```python
wrap_plot_ts(df, date_col, var_list, col_wrap=3, height=4, aspect=2, palettes=...)
```

Returns a seaborn facet grid. Include the date column in `var_list`, and avoid a pre-existing `value` column because the helper uses `melt()` with the default `value_name`.
