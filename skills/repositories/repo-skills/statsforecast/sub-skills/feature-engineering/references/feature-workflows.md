# Feature workflows

## Choose the feature workflow

| User need | Recommended workflow | Handoff boundary |
| --- | --- | --- |
| Small reproducible panel for examples or smoke tests | `generate_series` | Route final forecasting details to `core-forecasting`. |
| Built-in monthly demonstration series | `AirPassengersDF.copy()` | Route model choice to `model-selection`. |
| Trend and seasonal regressors for another model | `mstl_decomposition` with `MSTL` | Return `train_df` and `X_df`; route forecast execution to `core-forecasting`. |
| Known future drivers such as calendar, price, weather, or promotion | Build/merge exogenous columns in training `df` and future `X_df` | Confirm the selected model uses exogenous regressors in `model-selection`. |
| Static metadata per series | Repeat static values into future rows only if the downstream model will use them | Drop metadata columns if they are not intended as regressors. |
| pandas/polars parity check | Run the same small decomposition in each available engine | For distributed backends, route to `distributed-execution`. |

## Build deterministic synthetic panels

Use `generate_series` for examples and smoke tests. Keep examples small and deterministic.

```python
from statsforecast.utils import generate_series

# Canonical panel: unique_id, ds, y
df = generate_series(
    n_series=3,
    freq="D",
    min_length=56,
    max_length=56,
    n_static_features=0,
    equal_ends=True,
    engine="pandas",
    seed=7,
)
df["unique_id"] = df["unique_id"].astype("int64")
```

If you need static features for tests, request them explicitly:

```python
df = generate_series(
    n_series=3,
    freq="D",
    min_length=56,
    max_length=56,
    n_static_features=2,
    equal_ends=True,
    seed=7,
)
# Adds static_0 and static_1, constant within each unique_id.
```

Static columns are not automatically present in `mstl_decomposition`'s returned future `X_df`; repeat or drop them before fitting an exogenous-capable downstream model.

## Use AirPassengers fixtures

Use the built-in monthly fixture when a compact real-looking seasonal series is enough.

```python
from statsforecast.utils import AirPassengersDF

ap_df = AirPassengersDF.copy()
# Columns: unique_id, ds, y. ds is month-end dated; y is passenger count.
```

For monthly workflows, choose a frequency string that matches the `ds` index convention in the runtime. If pandas warns about a deprecated alias, switch to the newer month-end alias while keeping the same calendar spacing.

## Generate MSTL trend/seasonal features

Use `mstl_decomposition` to turn an MSTL decomposition into exogenous regressors for another model. The function returns both the transformed training data and the future feature table.

```python
from statsforecast.feature_engineering import mstl_decomposition
from statsforecast.models import MSTL
from statsforecast.utils import generate_series

h = 14
train = generate_series(
    n_series=4,
    freq="D",
    min_length=70,
    max_length=70,
    equal_ends=True,
    seed=0,
)
train["unique_id"] = train["unique_id"].astype("int64")

# Shuffle to prove the function can sort the panel internally.
train = train.sample(frac=1.0, random_state=0).reset_index(drop=True)

mstl = MSTL(season_length=7)
train_features, X_df = mstl_decomposition(train, model=mstl, freq="D", h=h)

assert {"trend", "seasonal"}.issubset(train_features.columns)
assert {"unique_id", "ds", "trend", "seasonal"}.issubset(X_df.columns)
assert X_df.shape[0] == train_features["unique_id"].nunique() * h
```

Handoff to forecasting:

```python
from statsforecast import StatsForecast
from statsforecast.models import ARIMA

sf = StatsForecast(models=[ARIMA(order=(1, 0, 0), season_length=7)], freq="D")
forecasts = sf.forecast(h=h, df=train_features, X_df=X_df)
```

Keep the forecast call minimal here. For fitted values, intervals, cross-validation, custom columns, or persistence, use `core-forecasting`.

## Multiple seasonalities

When `season_length` is a list, future features include one seasonal column per period.

```python
mstl = MSTL(season_length=[7, 28])
train_features, X_df = mstl_decomposition(train, model=mstl, freq="D", h=14)
expected = {"trend", "seasonal7", "seasonal28"}
assert expected.issubset(train_features.columns)
assert expected.issubset(X_df.columns)
```

Use this when the downstream model benefits from known weekly and four-week seasonal components. Model-family selection remains a `model-selection` responsibility.

## Build future `X_df` for time-varying exogenous regressors

For user-supplied exogenous regressors, split the target and future feature table by time. The future `X_df` must include `unique_id`, `ds`, and all future regressor columns, but not `y`.

```python
# y_df: columns unique_id, ds, y
# x_df: columns unique_id, ds, price, promo, weather_index
h = 28
cutoff = y_df["ds"].sort_values().unique()[-h]

train_y = y_df[y_df["ds"] < cutoff]
future_x = x_df[x_df["ds"] >= cutoff].head(h * train_y["unique_id"].nunique())
train = train_y.merge(x_df, on=["unique_id", "ds"], how="left")

feature_cols = [c for c in train.columns if c not in ("unique_id", "ds", "y")]
missing = [c for c in feature_cols if c not in future_x.columns]
assert not missing, f"future X_df is missing {missing}"
assert "y" not in future_x.columns
```

If a future regressor is not known, forecast that regressor separately or remove it from the training data before fitting the downstream model.

## Merge MSTL features with static features

If `train_features` contains both MSTL features and static columns, create future static values per id and merge them into `X_df`.

```python
static_cols = [c for c in train_features.columns if c.startswith("static_")]
if static_cols:
    static_by_id = train_features.groupby("unique_id", as_index=False)[static_cols].last()
    X_df = X_df.merge(static_by_id, on="unique_id", how="left")

required = [c for c in train_features.columns if c not in ("unique_id", "ds", "y")]
missing = [c for c in required if c not in X_df.columns]
assert not missing, missing
```

If the static columns are not intended regressors, drop them from `train_features` before forecasting instead of merging them into `X_df`.

## pandas and polars validation

`mstl_decomposition` accepts pandas or polars DataFrames. For polars examples, use a polars frequency string such as `"1d"` for daily data.

```python
import polars as pl
from statsforecast.feature_engineering import mstl_decomposition
from statsforecast.models import MSTL
from statsforecast.utils import generate_series

h = 7
series_pl = generate_series(
    n_series=2,
    freq="D",
    min_length=42,
    max_length=42,
    equal_ends=True,
    engine="polars",
    seed=1,
).with_columns(pl.col("unique_id").cast(pl.Int64))

train_pl, X_pl = mstl_decomposition(series_pl, MSTL(season_length=7), freq="1d", h=h)
assert X_pl.height == train_pl.select(pl.col("unique_id").n_unique()).item() * h
assert {"trend", "seasonal"}.issubset(set(X_pl.columns))
```

For small checks, converting `train_pl.to_pandas()` and `X_pl.to_pandas()` is acceptable. For large data, keep validation in polars to avoid unnecessary memory use.

## Minimal feature handoff checklist

Before sending a feature-engineered panel to `core-forecasting`, verify:

- `df`/`train_df` has `unique_id`, `ds`, `y` and no unintended metadata columns.
- `X_df` has `unique_id`, `ds`, every required future feature, and no `y`.
- `X_df` row count equals `h * number_of_series`.
- The first future timestamp follows the last training timestamp for each `unique_id`.
- Frequency `freq` and horizon `h` are the same in feature generation and forecasting.
- The selected model actually supports exogenous regressors if you expect it to use feature columns.
