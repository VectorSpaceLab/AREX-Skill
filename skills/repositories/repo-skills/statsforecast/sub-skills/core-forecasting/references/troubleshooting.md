# Core Forecasting Troubleshooting

Use this when a local pandas/polars `StatsForecast` workflow fails before or during core orchestration.

## Missing future `X_df` for exogenous regressors

Typical symptom:

```text
Models require the following exogenous features [...] for the forecasting step. Please provide them through `X_df`.
```

Cause:

- The historical dataframe contains extra columns beyond id/time/target.
- At least one selected model has `uses_exog=True`.
- `forecast`, `fit_predict`, or `predict` needs future values for those extra columns.

Fix:

1. Build `X_df` with exactly one row per id and future time step for the requested horizon.
2. Include the same exogenous columns as the training data.
3. Do not include the target column.
4. Use the same custom id/time names if `id_col` or `time_col` was customized.
5. If the extra columns were accidental, remove them from the historical dataframe before fitting.
6. If the selected model does not actually need exogenous features, route to `model-selection` to choose a model without `uses_exog=True`.

If the error instead says `Expected X to have shape ...`, the row count or column count is wrong. Recompute `h * number_of_series` rows and verify id/time plus all required feature columns.

## Duplicate model names

Typical symptom:

```text
Model names must be unique. You can use `alias` to set a unique name for each model.
```

Cause:

- The same model class appears more than once with the same default representation.
- A custom model lacks a unique `alias`/`__repr__`.

Fix:

```python
from statsforecast.models import Naive, AutoARIMA

models = [
    Naive(alias="Naive_baseline"),
    AutoARIMA(season_length=7, alias="AutoARIMA_weekly"),
    AutoARIMA(season_length=1, alias="AutoARIMA_nonseasonal"),
]
```

Aliases control output column names. Pick concise, unique, filesystem-safe labels if forecasts will be exported to downstream tools.

## Conformal interval sample-size failures

Typical symptoms:

```text
You need at least two windows to compute conformal intervals
Minimum samples for computing prediction intervals are ..., some series have less.
Prediction intervals settings require at least ... samples, some series have less and will use less windows.
```

Rules:

- `ConformalIntervals(n_windows=...)` requires `n_windows >= 2`.
- Absolute minimum historical samples per series for horizon `h` is `2 * h + 1`.
- To use all requested conformal windows, each series needs `n_windows * h + 1` samples.
- In cross-validation, add the validation `test_size` to those requirements because the held-out portion is not available for interval calibration. If `test_size` is omitted, it is computed as `h + step_size * (n_windows - 1)` for the cross-validation setup.

Fix:

- Reduce forecast horizon `h`.
- Reduce conformal `n_windows`, but not below `2`.
- Drop or separately handle short series.
- For cross-validation, reduce `n_windows`, `step_size`, or `test_size`.
- If the warning says fewer windows will be used, decide whether the reduced calibration is acceptable before treating the output as production-grade uncertainty.

## Invalid `level`

Typical symptom:

```text
Every value in `level` must be a finite real number
Every value in `level` must be between 0 and 100 (exclusive)
You must specify `level` when using `prediction_intervals`
```

Rules:

- Use a list/tuple/sequence, not a scalar: `level=[80, 95]`.
- Every value must be finite and numeric.
- Values must be strictly greater than `0` and strictly less than `100`.
- `forecast`, `fit_predict`, and `cross_validation` require `level` when `prediction_intervals` is provided.
- `predict` warns and returns point forecasts if fitted prediction intervals exist but `level` is omitted.
- `StatsForecast.plot(..., level=...)` also expects list-like levels, not `level=90`.

Fix:

```python
levels = [80, 95]
fcst = sf.forecast(df=df, h=12, level=levels)
```

## Date, frequency, and custom-column issues

Common causes:

- `freq` does not match the observed spacing in the time column.
- Integer time stamps are used with a string datetime frequency.
- Date strings cannot be parsed consistently.
- Custom column names were used for `forecast` or `fit` but omitted for later historical-data methods.
- Future `X_df` uses default `unique_id`/`ds` names even though the fitted data used custom names.

Fix checklist:

1. Confirm the historical dataframe has id/time/target columns and the target is numeric.
2. Convert dates explicitly when possible: `df["ds"] = pd.to_datetime(df["ds"])`.
3. Use `freq=1` for integer `ds` values.
4. Use a frequency alias matching the data cadence (`"D"` for daily, compatible monthly aliases for month-end data, etc.).
5. Sort by id/time before debugging so duplicates and gaps are visible.
6. Reuse `id_col`, `time_col`, and `target_col` consistently whenever a method consumes historical data.
7. Use the same custom id/time names in future `X_df`.

If the data are irregular, resample or aggregate to a regular grid before calling `StatsForecast`.

## Fitted-values misuse

Typical symptoms:

```text
Please run `forecast` method using `fitted=True`
Please run `cross_validation` method using `fitted=True`
```

Rules:

- `forecast_fitted_values()` only reads fitted values from the latest `forecast(..., fitted=True)` call.
- `cross_validation_fitted_values()` only reads fitted values from the latest `cross_validation(..., fitted=True)` call.
- `fit(...)` does not populate `forecast_fitted_values()`.
- A later call to the same workflow can replace or clear the stored fitted-value payload.
- `save(trim=True)` removes stored fitted-value helper payloads to reduce pickle size.

Fix:

```python
sf = StatsForecast(models=[Naive()], freq="D")
_ = sf.forecast(df=df, h=7, fitted=True)
insample = sf.forecast_fitted_values()

_ = sf.cross_validation(df=df, h=7, n_windows=2, fitted=True)
cv_insample = sf.cross_validation_fitted_values()
```

## Cross-validation series too short

Typical symptom:

```text
The following series are too short for the cross validation settings: [...]
```

Fix:

- Reduce `h`, `n_windows`, `step_size`, or explicit `test_size`.
- Use a smaller `input_size` only when the series still has enough observations for the test window.
- Drop short ids or forecast them separately with a simpler rule.

## `refit=False` or integer `refit` fails

Typical symptom:

```text
Can only use integer refit or refit=False with models that implement the forward method
```

Cause:

- At least one selected model, or the configured fallback model, does not implement `forward`.

Fix:

- Use `refit=True`.
- Route to `model-selection` to choose models that implement `forward`.
- Remove or replace the fallback model for that cross-validation run.

## Local parallelism is slower or unstable

Causes:

- Too few series to benefit from process workers.
- Large model objects or data chunks make serialization overhead dominate.
- Interactive or restricted environments can have multiprocessing limitations.

Fix:

- Re-run with `n_jobs=1` to confirm the workflow and expose cleaner stack traces.
- Increase `n_jobs` only for many independent series.
- Remember the effective worker count is capped at the number of series.
- For Dask, Ray, Spark, Fugue, or distributed dataframe behavior, route to `distributed-execution` instead of debugging it here.

## Persistence issues

Symptoms and fixes:

- `Specified path does not exist`: pass a real file path created by `save`.
- `StatsForecast is larger than the specified max_size`: increase `max_size`, use `trim=True`, or avoid persisting large fitted objects.
- Future `predict` after `load` fails for exogenous data: provide the same kind of future `X_df` required before saving.
