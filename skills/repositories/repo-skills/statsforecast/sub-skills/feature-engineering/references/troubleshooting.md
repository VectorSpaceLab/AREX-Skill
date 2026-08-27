# Feature engineering troubleshooting

## `model` must be an MSTL instance

Symptom:

```text
`model` must be an MSTL instance
```

Cause: `mstl_decomposition` only accepts `statsforecast.models.MSTL`. Passing `Naive`, `AutoARIMA`, `ARIMA`, or another model raises an error.

Fix:

```python
from statsforecast.feature_engineering import mstl_decomposition
from statsforecast.models import MSTL

train_df, X_df = mstl_decomposition(df, MSTL(season_length=7), freq="D", h=14)
```

Choose the final forecasting model separately in `model-selection`; the MSTL instance here is only for component feature generation.

## Unsorted panel or surprising row order

Symptoms:

- Training data was shuffled before decomposition.
- Returned rows appear sorted differently than the input.
- Later merges compare the wrong rows after decomposition.

Cause: `mstl_decomposition` computes sort indices by `unique_id` and `ds` and sorts internally when needed. This is correct for model fitting, but downstream row-wise comparisons against the unsorted input can fail.

Fixes:

- Compare by keys (`unique_id`, `ds`), not by original row position.
- Reset pandas indices after shuffling or sorting.
- For merge-based checks, sort both frames by `unique_id`, `ds`.

```python
train_df = train_df.sort_values(["unique_id", "ds"]).reset_index(drop=True)
X_df = X_df.sort_values(["unique_id", "ds"]).reset_index(drop=True)
```

For polars:

```python
train_df = train_df.sort(["unique_id", "ds"])
X_df = X_df.sort(["unique_id", "ds"])
```

## Horizon or frequency mismatch

Symptoms:

- Future timestamps do not start immediately after each series' final training timestamp.
- Forecasting later raises an `X_df` shape error.
- Monthly or daily future dates are offset incorrectly.

Causes:

- `h` used in decomposition differs from `h` used in forecasting.
- `freq` does not match the actual spacing of `ds`.
- pandas and polars frequency strings were mixed incorrectly.

Fixes:

- Use one shared `h` variable for decomposition and forecasting.
- Use the same calendar meaning for `freq` in both steps.
- For daily pandas data, `"D"` is typical; for daily polars decomposition, `"1d"` is a safe choice.
- For month-end data such as AirPassengers, use the month-end alias accepted by the installed pandas version.

Validation:

```python
import pandas as pd

pd.testing.assert_series_equal(
    train_df.groupby("unique_id")["ds"].max() + pd.offsets.Day(),
    X_df.groupby("unique_id")["ds"].min(),
    check_names=False,
)
assert X_df.shape[0] == train_df["unique_id"].nunique() * h
```

Replace `pd.offsets.Day()` with the matching offset for non-daily data.

## Future `X_df` column alignment

Symptoms:

```text
Models require the following exogenous features [...] for the forecasting step. Please provide them through `X_df`.
```

or

```text
Expected X to have shape (...), but got (...)
```

Causes:

- Training `df` contains extra columns not present in future `X_df`.
- `X_df` contains too few or too many future rows.
- `X_df` includes `y` or misses required `(unique_id, ds)` rows.
- A static column was present in training data but was not repeated into future rows.

Fix:

```python
id_time_target = ("unique_id", "ds", "y")
required = [c for c in train_df.columns if c not in id_time_target]
missing = [c for c in required if c not in X_df.columns]
extra_y = "y" in X_df.columns
expected_rows = train_df["unique_id"].nunique() * h
assert not missing, f"missing future exogenous columns: {missing}"
assert not extra_y, "future X_df must not include y"
assert X_df.shape[0] == expected_rows
```

If missing columns are static metadata, either repeat them into `X_df` per `unique_id` or drop them from `train_df` before fitting the downstream model.

## Static feature confusion

Symptoms:

- `generate_series(n_static_features=...)` works for decomposition but a later exogenous-capable model asks for `static_0`, `static_1`, etc. in `X_df`.
- A feature intended only for grouping metadata is treated as a regressor.

Cause: StatsForecast treats all training columns outside `unique_id`, `ds`, and `y` as candidate exogenous columns. `mstl_decomposition` adds future MSTL columns, but it does not invent future rows for unrelated static columns.

Fixes:

- If the static variables should be regressors, repeat them into `X_df`:

```python
static_cols = [c for c in train_df.columns if c.startswith("static_")]
static_by_id = train_df.groupby("unique_id", as_index=False)[static_cols].last()
X_df = X_df.merge(static_by_id, on="unique_id", how="left")
```

- If the static variables are metadata only, remove them before forecasting:

```python
train_df = train_df.drop(columns=static_cols)
```

## polars is optional or unavailable

Symptoms:

- `ModuleNotFoundError: No module named 'polars'`.
- A polars example fails while pandas works.
- Frequency parsing differs between pandas and polars runs.

Fixes:

- Use pandas (`engine="pandas"`) when polars is not installed.
- Install polars only if the runtime needs polars parity or polars input/output.
- For daily polars data, call `mstl_decomposition(..., freq="1d", h=h)`.
- For small parity checks, convert polars results with `.to_pandas()` and compare column values; for large data, keep validation native to polars.

The bundled smoke script automatically skips the polars branch in `--engine auto` mode when polars is not importable.

## Custom column names with `mstl_decomposition`

Symptom: decomposition fails or silently uses the wrong columns when the user's data uses names like `series_id`, `timestamp`, or `value`.

Cause: `mstl_decomposition` does not expose custom column parameters. It expects `unique_id`, `ds`, and `y`.

Fix:

```python
canonical = raw.rename(columns={
    "series_id": "unique_id",
    "timestamp": "ds",
    "value": "y",
})
train_df, X_df = mstl_decomposition(canonical, MSTL(season_length=7), freq="D", h=14)
```

When calling core forecasting later with custom column names, rename both the training dataframe and `X_df` consistently or stay canonical.

## Too little history for the requested seasonal decomposition

Symptoms:

- Decomposition components contain many missing or unstable values.
- The downstream forecast is poor or emits numeric warnings.

Cause: MSTL needs enough history to estimate the requested seasonal period(s). Very short series relative to `season_length` or `max(season_length)` are weak feature sources.

Fixes:

- Increase the training window.
- Use a smaller or single seasonal period.
- Fall back to simpler calendar features such as day-of-week/month indicators.
- If the task is model-family selection rather than feature creation, route to `model-selection`.

## Future regressors are unknown

Symptom: user wants to use weather, price, promotion, or calendar-like regressors but future values are not available.

Fixes:

- Calendar features can usually be generated directly from future `ds`.
- Known schedules such as holidays and promotions should be joined onto future rows.
- Unknown signals such as weather or price must be forecasted separately, supplied from an external plan, or removed from both training `df` and future `X_df`.

Do not pass partial future exogenous data to a model that requires complete future rows.
