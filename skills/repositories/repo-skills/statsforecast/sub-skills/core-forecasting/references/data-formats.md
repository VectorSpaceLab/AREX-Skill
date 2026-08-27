# Data Formats

`StatsForecast` is a panel forecaster: one dataframe contains many univariate series. Native local workflows accept pandas and polars dataframes. Other distributed dataframe engines should be routed to `distributed-execution`.

## Required panel schema

Default column names:

| Column | Meaning | Required | Notes |
| --- | --- | --- | --- |
| `unique_id` | Series identifier | yes | String, integer, or categorical-like ids are acceptable. Each id identifies one independent series. |
| `ds` | Timestamp or time index | yes | Datetime-like values, parseable date strings, or integer stamps. Must match `freq`. |
| `y` | Target value | yes | Numeric value to forecast. |
| Extra columns | Static or time-varying regressors | optional | Treated as exogenous input when selected models use exogenous features. |

Minimum example:

```python
import pandas as pd

panel = pd.DataFrame(
    {
        "unique_id": ["a", "a", "a", "b", "b", "b"],
        "ds": pd.to_datetime([
            "2024-01-01", "2024-01-02", "2024-01-03",
            "2024-01-01", "2024-01-02", "2024-01-03",
        ]),
        "y": [10.0, 11.0, 13.0, 20.0, 21.0, 19.0],
    }
)
```

## Time and frequency rules

- `freq` must describe the spacing of `ds` values inside each series.
- For daily datetime data, use `freq="D"`. For integer stamps, use `freq=1` so future times advance by one integer step.
- String dates are coerced to datetime when possible, but explicit datetime columns are safer.
- Monthly and other calendar frequencies should use a valid offset alias accepted by the installed pandas/polars and `utilsforecast` stack.
- Keep each series on a regular cadence. If the cadence is irregular, resample, fill, or remove problematic rows before calling `StatsForecast`.
- Series do not need equal starts or equal lengths. Future output starts one frequency step after each series' last timestamp.

## Custom column names

Every core method that consumes historical data accepts the same naming arguments:

```python
custom = panel.rename(
    columns={"unique_id": "item_id", "ds": "timestamp", "y": "target"}
)

sf.forecast(
    df=custom,
    h=7,
    id_col="item_id",
    time_col="timestamp",
    target_col="target",
)
```

Rules:

- Pass the same `id_col`, `time_col`, and `target_col` whenever a method consumes the historical dataframe.
- After `fit(df=custom, ...)`, `predict(...)` reuses the stored custom names and does not receive naming arguments.
- Fitted-value helpers return the custom id/time/target names from the most recent fitted call.
- Future `X_df` must use the same id/time column names as the fitted data.

## Exogenous columns and `X_df`

Any historical column that is not the id, time, or target column is stored as an exogenous feature. If all selected models ignore exogenous features, extra columns can be present and no future `X_df` is needed. If any selected model uses exogenous features, future forecasts require `X_df`.

Historical training data with one time-varying regressor:

```python
train = panel.assign(price=[1.0, 1.1, 1.2, 0.9, 1.0, 1.1])
```

Future exogenous data for `h=2`:

```python
future_x = pd.DataFrame(
    {
        "unique_id": ["a", "a", "b", "b"],
        "ds": pd.to_datetime(["2024-01-04", "2024-01-05", "2024-01-04", "2024-01-05"]),
        "price": [1.25, 1.30, 1.05, 1.10],
    }
)
```

`X_df` contract:

- Rows: exactly `h * number_of_series` rows.
- Id/time: every id from the fitted data and exactly the next `h` timestamps for that id.
- Columns: id column, time column, and all required exogenous feature columns; omit the target column.
- Types: keep feature dtypes numeric or model-compatible. Preserve the same column names used in the historical data.
- Order: sorted id/time order is easiest, but the processing layer groups by id/time. Do not rely on accidental row order when constructing expected outputs.

If the shape is wrong, core validation raises an error like `Expected X to have shape ...`. If required exogenous columns are absent or `X_df` is omitted, the error names the missing features and asks for `X_df`.

## Output dataframes

### Forecast output

Default forecast columns:

```text
unique_id, ds, <model>, <model>-lo-80, <model>-hi-80, ...
```

- Future rows are repeated for every id and horizon step.
- Custom id/time names are preserved.
- The target column is not present in future forecasts.
- Interval columns appear only when `level` is provided and the model supports intervals or conformal intervals are configured.

### Forecast fitted values

`forecast(..., fitted=True)` followed by `forecast_fitted_values()` returns:

```text
unique_id, ds, y, <model>, ...
```

The rows align to the training data. Initial fitted values can be missing for models that need lagged history.

### Cross-validation output

`cross_validation(...)` returns:

```text
unique_id, ds, cutoff, y, <model>, <model>-lo-80, <model>-hi-80, ...
```

- `cutoff` is the last training timestamp for that validation window.
- `ds` is the forecasted timestamp inside the held-out window.
- `y` is the observed value for that held-out timestamp.

### Cross-validation fitted values

`cross_validation(..., fitted=True)` followed by `cross_validation_fitted_values()` returns training-window fitted values with a `cutoff` column, so the same historical row can appear once per validation window.

## Polars notes

- Native polars dataframes are accepted by the same methods.
- Prefer frequency strings compatible with polars duration aliases when the input is polars.
- Output remains polars for native polars input when the installed dependencies support the operation.
- If the user's object is a lazy frame, Dask/Ray/Spark object, or Fugue execution target rather than an eager pandas/polars dataframe, route to `distributed-execution`.
