# Component and Exogenous Feature Recipes

Read this when a NeuralProphet task needs model structure beyond a default trend/seasonality baseline. The recipes are self-contained and do not require reopening upstream notebooks or tests.

## Quick component decision table

| User intent | Configure | Data obligation |
| --- | --- | --- |
| Smooth or flexible trend | `growth`, `changepoints`, `n_changepoints`, `trend_reg` | Standard `ds`, `y`, optional `ID`; manual changepoints within history. |
| Per-series trend | `trend_global_local="local"`, optional `trend_local_reg` | Multi-series dataframe with stable `ID`. |
| Built-in seasonality | `yearly_seasonality`, `weekly_seasonality`, `daily_seasonality` | Enough history to observe the period. |
| Custom/conditional seasonality | `add_seasonality(..., condition_name=...)` | Condition column in train and prediction frames. |
| Autoregression | `n_lags>0`, `n_forecasts`, optional `ar_reg`/`ar_layers` | Enough contiguous target history per ID. |
| Lagged covariate | `add_lagged_regressor(...)` | Historical covariate column aligned with `ds`, `y`, and `ID`. |
| Future-known covariate | `add_future_regressor(...)` | Historical column plus future values in `regressors_df`. |
| Custom event | `add_events(...)`, `create_df_with_events(...)` | `events_df` with `event`, `ds`, optional `ID`. |
| Country holiday | `add_country_holidays(...)` | Supported country/list/dict; add all countries in one call. |
| Global/local/glocal panel | `ID`, `trend_global_local`, `season_global_local`, local regularization | Consistent IDs in history, prediction frames, and ID-specific exogenous frames. |

## Standard registration order

```python
from neuralprophet import NeuralProphet

m = NeuralProphet(
    n_lags=7,
    n_forecasts=3,
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=False,
    seasonality_mode="additive",
    trend_global_local="global",
    season_global_local="global",
    epochs=20,
    learning_rate=0.05,
)

m.add_lagged_regressor("observed_temperature", n_lags="auto")
m.add_future_regressor("planned_price", mode="additive")
m.add_events(["promo", "outage"], lower_window=-1, upper_window=1)
m.add_country_holidays(["US", "Germany"])
m.add_seasonality("business_month", period=30.5, fourier_order=5)

history = m.create_df_with_events(df, events_df)
m.fit(history, freq="D", progress=None, checkpointing=False)
future = m.make_future_dataframe(
    history,
    periods=14,
    events_df=events_df,
    regressors_df=future_regressors,
    n_historic_predictions=True,
)
forecast = m.predict(future)
```

Only register components that are needed. A fitted model should not be reconfigured; create a new model and refit when component scope changes.

## Trend and changepoints

```python
m = NeuralProphet(
    growth="linear",
    n_changepoints=20,
    changepoints_range=0.8,
    trend_reg=1.0,
    trend_reg_threshold=False,
)
```

Use fewer changepoints or larger `trend_reg` for smoother trend; use explicit `changepoints=[...]` when domain change dates are known. `growth="off"` disables trend. `growth="discontinuous"` allows discontinuities but can force trend sharing back to global when local trend would be invalid.

For multi-ID data:

```python
m = NeuralProphet(trend_global_local="local", trend_local_reg=1.0)
```

Use `trend_global_local="global"` when all IDs share one long-run shape, `"local"` when each ID needs independent parameters, and positive `trend_local_reg` for regularized-local/glocal behavior.

## Seasonality

Built-in seasonalities can be `True`, `False`, `"auto"`, or an integer Fourier order:

```python
m = NeuralProphet(
    yearly_seasonality="auto",
    weekly_seasonality=True,
    daily_seasonality=False,
    seasonality_mode="multiplicative",
    seasonality_reg=0.1,
)
```

Custom seasonality:

```python
m = NeuralProphet(weekly_seasonality=False)
m.add_seasonality(name="business_month", period=30.5, fourier_order=5, global_local="global")
```

Conditional seasonality:

```python
def add_weekend_flag(frame):
    frame = frame.copy()
    frame["is_weekend"] = frame["ds"].dt.dayofweek.isin([5, 6]).astype(float)
    return frame

df = add_weekend_flag(df)
m = NeuralProphet(weekly_seasonality=False)
m.add_seasonality("weekend_daily", period=1, fourier_order=3, condition_name="is_weekend")
m.fit(df, freq="D")
future = m.make_future_dataframe(df, periods=14)
future = add_weekend_flag(future)
forecast = m.predict(future)
```

Condition columns should be numeric 0/1 or fractional weights. Recompute them after `make_future_dataframe` because generated future rows can contain missing values for non-core columns.

## Autoregression and lagged regressors

Autoregression uses target history:

```python
m = NeuralProphet(n_lags=14, n_forecasts=3, ar_reg=0.5)
```

Lagged regressors use past values of external columns:

```python
df["temperature_ma"] = df.groupby("ID", dropna=False)["temperature"].transform(
    lambda s: s.rolling(7, min_periods=1).mean()
)
m = NeuralProphet(n_lags=7, n_forecasts=2, lagged_reg_layers=[16, 16])
m.add_lagged_regressor("temperature_ma", n_lags="auto", normalize="auto")
m.fit(df, freq="D")
```

Guidance:

- `n_lags="auto"` follows AR lag count when AR is enabled; otherwise it becomes 1.
- `n_lags="scalar"` uses only the most recent known value.
- Compute lagged or rolling features within each `ID`, never across concatenated IDs.
- Lagged regressors are for historical covariates. If values are known for future timestamps, use future regressors.

## Future-known regressors

```python
m = NeuralProphet(future_regressors_model="linear")
m.add_future_regressor("planned_price", mode="additive")
m.fit(df, freq="D")

future_regressors = pd.DataFrame({
    "ds": future_dates,
    "planned_price": planned_prices,
})
future = m.make_future_dataframe(
    df,
    periods=len(future_regressors),
    regressors_df=future_regressors,
)
forecast = m.predict(future)
```

Multi-ID future regressors include `ID` when values differ by series:

```python
# columns: ds, ID, planned_price
future = m.make_future_dataframe(panel_for_ids, periods=horizon, regressors_df=future_regressors)
```

Checklist:

- The fit dataframe has every registered future regressor column.
- `regressors_df` has every registered future regressor for every requested future period.
- If `regressors_df` includes `ID`, its IDs are present in the base dataframe passed to `make_future_dataframe`.
- Sort future regressor rows by `ds` within each ID; include `ds` for clarity.
- Use neural future-regressor variants only after the linear path is correct.

## Custom events and country holidays

Custom event workflow:

```python
events_df = pd.DataFrame({
    "event": ["promo", "outage"],
    "ds": pd.to_datetime(["2024-03-01", "2024-03-05"]),
})

m = NeuralProphet()
m.add_events(["promo", "outage"], lower_window=-1, upper_window=2, mode="additive")
history = m.create_df_with_events(df, events_df)
m.fit(history, freq="D")
future = m.make_future_dataframe(history, periods=30, events_df=events_df)
```

For multi-ID events, add `ID` to `events_df`. If an event schedule is shared by all IDs, omit `ID` so NeuralProphet broadcasts it.

Holiday workflow:

```python
m = NeuralProphet()
m.add_country_holidays(["US", "Germany"], lower_window=-1, upper_window=1)
# or one subdivision mapping
m.add_country_holidays({"US": "CA"}, lower_window=0, upper_window=1)
```

Call `add_country_holidays` only once. If a country/subdivision is unsupported, model those dates as custom events instead.

## Global, local, and regularized-local multi-series modeling

```python
panel = pd.concat([df_a.assign(ID="series_a"), df_b.assign(ID="series_b")], ignore_index=True)

m = NeuralProphet(
    n_lags=7,
    n_forecasts=2,
    trend_global_local="local",
    trend_local_reg=1.0,
    season_global_local="global",
    global_normalization=False,
)
m.add_future_regressor("planned_price")
m.fit(panel, freq="D")
```

Use global components for shared behavior, local components for independent per-ID shapes, and local components plus positive local regularization for glocal/regularized-local behavior. For split/CV decisions such as `local_split=True`, route to `../evaluation-and-uncertainty/SKILL.md`. For ID-specific plots or parameters, route to `../operations-and-migration/SKILL.md`.

## Pre-flight validation before prediction

- Component names are unique and not reserved.
- Every component is registered before `fit`.
- Training data contains all lagged/future regressor and condition columns.
- Custom event table uses only registered event names.
- Future regressor frames cover the forecast horizon and relevant IDs.
- Each ID has enough history for the maximum lag.
- Multiplicative components make sense for the target scale.
