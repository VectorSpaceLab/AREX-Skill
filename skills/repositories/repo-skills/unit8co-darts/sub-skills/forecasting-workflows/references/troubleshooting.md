# Forecasting troubleshooting

## Model rejects covariate arguments

**Symptom:** `fit()` or `predict()` complains about `past_covariates` or `future_covariates`.

**Cause:** the selected model family does not support that covariate type.

**Fix:**

- Do not force covariates into `NaiveSeasonal` or other unsupported local models.
- Switch to a covariate-capable family such as `LinearRegressionModel` or a torch model.
- Route covariate span construction to `data-processing-and-covariates`.

## Optional model import fails

**Symptom:** import of `Prophet`, `LightGBMModel`, `XGBModel`, `CatBoostModel`, or StatsForecast-related model fails.

**Fix:** install the smallest needed extra (`darts[notorch]` or the specific package) and rerun an import check. If the user does not need that model family, choose a base model instead.

## Forecast horizon or start time is wrong

Check:

```python
assert len(forecast) == n
print(train.end_time(), forecast.start_time(), forecast.end_time())
```

Common causes include splitting at the wrong point, passing an unexpected `series=` argument to `predict()`, or insufficient covariate coverage.

## Probabilistic forecast is deterministic

`num_samples` does not make every model stochastic. Verify model support and configuration. If the result has `forecast.n_samples == 1`, use deterministic metrics or choose a probabilistic-capable model/likelihood.

## Historical forecasts are slow

Backtesting and historical forecasts may refit models many times. Use tiny windows and bounded horizons before scaling. Do not run large benchmark-like historical forecasts in an agent verification check unless the user explicitly authorizes the runtime.

## Incompatible frequency or missing target values

Route back to:

- `time-series-and-data` for missing dates/frequency construction.
- `data-processing-and-covariates` for missing values and preprocessing.

Do not hide data issues by dropping arbitrary rows after the train/validation split unless the user approves that data policy.
