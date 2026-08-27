# Core API Reference

This reference covers the native `StatsForecast` orchestration API for pandas and polars panels. It assumes model objects have already been selected. If model choice is unclear, route to `model-selection` first.

## Imports

```python
from statsforecast import StatsForecast
from statsforecast.models import Naive, SeasonalNaive  # examples only
from statsforecast.utils import ConformalIntervals
```

Use installed package imports. Runtime scripts and workflows must not depend on a source checkout.

## Constructor

```python
StatsForecast(
    models: list,
    freq: str | int,
    n_jobs: int = 1,
    fallback_model = None,
    verbose: bool = False,
)
```

- `models`: instantiated model objects. Every output name must be unique. Most StatsForecast models expose an `alias=` constructor argument; use it when including multiple variants of the same model.
- `freq`: time frequency. Use a pandas/polars offset alias for datetime data (`"D"`, `"H"`, monthly aliases, or polars-style aliases accepted by the installed dependencies). Use an integer such as `1` for integer datestamps.
- `n_jobs`: local process parallelism for native pandas/polars execution. `-1` or `None` requests all CPU cores, but the effective worker count is capped at the number of series. Prefer `1` for tiny panels and debugging; use more workers only when there are enough independent series to amortize process overhead.
- `fallback_model`: model used when a primary model fails during fitting or forecasting paths. Forecast and cross-validation output columns keep the primary model names; the fallback is a recovery behavior, not a new output label. Cross-validation with `refit=False` or integer `refit` also requires the fallback to implement `forward`.
- `verbose`: enables progress bars in single-job paths.

## Forecasting methods

### `forecast`

```python
fcst_df = sf.forecast(
    h=12,
    df=panel,
    X_df=None,
    level=None,
    fitted=False,
    prediction_intervals=None,
    id_col="unique_id",
    time_col="ds",
    target_col="y",
)
```

Use this as the default production path when fitted model objects are not needed. It trains each model inside each series, emits forecasts, and discards fitted model objects to reduce memory pressure. If `fitted=True`, call `sf.forecast_fitted_values()` immediately after to retrieve in-sample predictions from that forecast run.

### `fit` + `predict`

```python
sf.fit(
    df=panel,
    prediction_intervals=None,
    id_col="unique_id",
    time_col="ds",
    target_col="y",
)
pred_df = sf.predict(h=12, X_df=None, level=None)
```

Use this when the fitted model objects need to be retained for repeated future predictions, inspection, save/load, or parity with familiar estimator-style workflows. `predict` requires `fit` to have run first and uses the column names/frequency stored during `fit`.

### `fit_predict`

```python
pred_df = sf.fit_predict(
    h=12,
    df=panel,
    X_df=None,
    level=None,
    prediction_intervals=None,
    id_col="unique_id",
    time_col="ds",
    target_col="y",
)
```

Use this when a single call should both store fitted objects and return forecasts. It is less memory-frugal than `forecast` because fitted models are kept on `sf`.

## Fitted-value helpers

```python
fitted_df = sf.forecast_fitted_values()
cv_fitted_df = sf.cross_validation_fitted_values()
```

- `forecast_fitted_values()` requires the latest relevant forecast call to have used `forecast(..., fitted=True)`. It returns id/time, target, and in-sample fitted columns.
- `cross_validation_fitted_values()` requires `cross_validation(..., fitted=True)`. It returns id/time, `cutoff`, target, and fitted columns for each validation window.
- A later `forecast` call clears prior forecast fitted values; a later `cross_validation` call clears prior cross-validation fitted values.

## Cross-validation

```python
cv_df = sf.cross_validation(
    h=12,
    df=panel,
    n_windows=2,
    step_size=1,
    test_size=None,
    input_size=None,
    level=None,
    fitted=False,
    refit=True,
    prediction_intervals=None,
    id_col="unique_id",
    time_col="ds",
    target_col="y",
)
```

- Output columns include id, time, `cutoff`, target, one column per model, and optional interval columns.
- Provide either `n_windows` or `test_size`. If `test_size` is omitted, it is computed as `h + step_size * (n_windows - 1)`.
- `step_size` controls the distance between validation windows; overlapping windows are possible.
- `input_size=None` uses expanding windows. An integer `input_size` creates fixed-length rolling training windows.
- `refit=True` refits for every window. `refit=False` or an integer refit cadence requires every model, and the fallback model if present, to implement `forward`.
- Series shorter than the validation setup are rejected before model execution.
- The public cross-validation method does not accept a separate `X_df`; design exogenous evaluation carefully.

## Intervals

### Analytic/native interval columns

```python
fcst = sf.forecast(df=df, h=12, level=[80, 95])
```

For models that implement probabilistic output, `level` adds columns such as `AutoARIMA-lo-80`, `AutoARIMA-hi-80`, `AutoARIMA-lo-95`, and `AutoARIMA-hi-95`. `level` must be list-like, finite, and strictly between 0 and 100.

### Conformal intervals

```python
intervals = ConformalIntervals(n_windows=2, h=12, method="conformal_distribution")
fcst = sf.forecast(df=df, h=12, level=[80, 95], prediction_intervals=intervals)
```

`ConformalIntervals` can also be attached to compatible model constructors. Passing `prediction_intervals` without a `level` raises on `forecast`, `fit_predict`, and `cross_validation`; `predict` emits a warning and returns point forecasts if fitted intervals exist but `level` is omitted.

Available conformal methods are `"conformal_distribution"` and `"conformal_error"`. `n_windows` must be at least `2`.

## Exogenous regressors

`StatsForecast` treats every dataframe column other than `id_col`, `time_col`, and `target_col` as exogenous input. If any selected model has `uses_exog=True` and training data contains extra columns, future forecasts must receive `X_df`.

```python
import pandas as pd

future_x = pd.DataFrame(...)  # one row per id/future timestamp, no target column
fcst = sf.forecast(df=train_df, h=7, X_df=future_x)
```

`X_df` must contain exactly one row per `(id, future time)` pair for the requested horizon and include the same exogenous feature columns used during fit. It should not include the target column.

## Plot, save, and load

```python
fig = StatsForecast.plot(df=df, forecasts_df=fcst_df, level=[80])
sf.fit(df=df)
sf.save("statsforecast.pkl", max_size="100MB", trim=True)
loaded = StatsForecast.load("statsforecast.pkl")
future_x = ...  # only needed when the fitted model used exogenous features
new_pred = loaded.predict(h=12, X_df=future_x)
```

- `plot` is a static method; pass historical `df` and optional forecasts. Use `level` as a list when plotting interval bands.
- `save` pickles the object. `max_size` accepts units `B`, `KB`, `MB`, or `GB`. `trim=True` removes stored fitted-value helper payloads before saving.
- `load` returns a `StatsForecast` instance; the file must have been created by `save`.
