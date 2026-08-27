# Feature engineering API reference

## Imports

```python
from statsforecast.feature_engineering import mstl_decomposition
from statsforecast.models import MSTL
from statsforecast.utils import AirPassengers, AirPassengersDF, generate_series
```

`statsforecast.feature_engineering` also exposes `MSTL` through its module import, but importing `MSTL` from `statsforecast.models` makes the model dependency explicit.

## `generate_series`

Signature:

```python
generate_series(
    n_series: int,
    freq: str = "D",
    min_length: int = 50,
    max_length: int = 500,
    n_static_features: int = 0,
    equal_ends: bool = False,
    engine: str = "pandas",
    seed: int = 0,
)
```

Purpose: create deterministic synthetic panel data for examples, smoke tests, and validation.

Returned columns:

- Always: `unique_id`, `ds`, `y`.
- When `n_static_features > 0`: additional static columns such as `static_0`, `static_1`, repeated for every row of each `unique_id`.

Important options:

- `engine="pandas"` returns a pandas DataFrame; `engine="polars"` returns a polars DataFrame when polars is installed.
- `equal_ends=True` forces every series to share the same last timestamp, which simplifies forecast-output comparisons.
- `min_length=max_length=<n>` makes every generated series the same length.
- `seed` controls reproducibility.

## AirPassengers fixtures

- `AirPassengers` is a NumPy array of 144 monthly passenger counts.
- `AirPassengersDF` is a pandas DataFrame with canonical columns:
  - `unique_id`: one series identifier, stored as ones.
  - `ds`: monthly end dates beginning in 1949.
  - `y`: passenger counts.

Use `AirPassengersDF.copy()` before mutation. For monthly forecasts, choose a `freq` that matches the month-end `ds` values in the installed pandas version, commonly `"M"` or `"ME"`.

## `mstl_decomposition`

Signature:

```python
mstl_decomposition(
    df,                  # pandas or polars DataFrame
    model: MSTL,         # statsforecast.models.MSTL instance
    freq: str,           # frequency compatible with df["ds"]
    h: int,              # forecast horizon
) -> tuple[df_type, df_type]
```

Input requirements:

- `df` must use canonical StatsForecast columns: `unique_id`, `ds`, `y`.
- `model` must be an instantiated `MSTL`, for example `MSTL(season_length=7)`.
- `freq` must describe one step in `ds`; use the same meaning later in `StatsForecast`.
- `h` is the number of future rows per `unique_id`.

Behavior:

1. Sorts the panel by `unique_id` and `ds` when needed.
2. Fits an internal `StatsForecast(models=[model], freq=freq)`.
3. Adds in-sample decomposition columns to the training data.
4. Creates future rows and future decomposition columns for `X_df`.

Return values:

- `train_df`: original training rows plus MSTL-derived columns.
- `X_df`: future rows with `unique_id`, `ds`, and the same MSTL-derived feature columns needed by exogenous-capable downstream models.

Output columns:

| MSTL constructor | Added columns in `train_df` and `X_df` |
| --- | --- |
| `MSTL(season_length=7)` | `trend`, `seasonal` |
| `MSTL(season_length=[7, 28])` | `trend`, `seasonal7`, `seasonal28` |

The exact seasonal column names come from the fitted MSTL component table and start with `seasonal`.

## Future `X_df` contract

For feature-engineering handoff to core forecasting:

- `X_df` must have one row for every `(unique_id, future ds)` pair.
- Expected row count: `h * train_df["unique_id"].nunique()` for pandas, or the equivalent unique count for polars.
- The first future `ds` for each id should be one frequency step after that id's last training `ds`.
- The future feature columns must match every extra training column required by the selected downstream model.
- Do not include `y` in `X_df`.

Minimal validation for pandas-style data:

```python
import pandas as pd

assert X_df.shape[0] == train_df["unique_id"].nunique() * h
pd.testing.assert_series_equal(
    train_df.groupby("unique_id")["ds"].max() + pd.offsets.Day(),
    X_df.groupby("unique_id")["ds"].min(),
    check_names=False,
)
required = [c for c in train_df.columns if c not in ("unique_id", "ds", "y")]
missing = [c for c in required if c not in X_df.columns]
assert not missing, missing
```

For polars, either use native polars grouping or convert the small validation slices with `.to_pandas()`.

## Static and exogenous columns

StatsForecast records every training column other than `unique_id`, `ds`, and `y` as a candidate exogenous feature. If the chosen model uses exogenous regressors, those columns must be present in `X_df` for the future horizon.

Conventions:

- Time-varying exogenous columns, such as `month`, promotion flags, weather, or prices, must be known or separately forecasted for the future horizon.
- Static features must be repeated for each future row of the corresponding `unique_id` if the downstream model uses them.
- If static columns are only metadata and should not be model regressors, drop them before fitting the exogenous-capable downstream model.
- If a downstream model does not use exogenous regressors, extra feature columns may be ignored by that model, but keeping unnecessary columns can confuse later handoffs; prefer explicit feature selection.

Pandas pattern for repeating static features into `X_df`:

```python
static_cols = [c for c in train_df.columns if c.startswith("static_")]
if static_cols:
    static_by_id = train_df.groupby("unique_id", as_index=False)[static_cols].last()
    X_df = X_df.merge(static_by_id, on="unique_id", how="left")
```

## Custom column names

`mstl_decomposition` has no `id_col`, `time_col`, or `target_col` parameters. For custom schemas, rename before decomposition:

```python
canonical = raw.rename(columns={"series": "unique_id", "timestamp": "ds", "value": "y"})
train_df, X_df = mstl_decomposition(canonical, MSTL(season_length=7), freq="D", h=14)
```

After feature creation, keep canonical names for normal `StatsForecast` workflows unless the downstream core-forecasting workflow explicitly renames both `df` and `X_df` with matching custom-column parameters.
