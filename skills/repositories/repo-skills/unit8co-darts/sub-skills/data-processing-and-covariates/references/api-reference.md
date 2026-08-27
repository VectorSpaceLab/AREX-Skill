# Data processing and covariate API reference

## Verified signatures for Darts 0.46.1

```text
Pipeline(transformers, copy=False, verbose=None, n_jobs=None)
MissingValuesFiller(fill='auto', name='MissingValuesFiller', n_jobs=1, verbose=False, columns=None)
Scaler(scaler=None, name='Scaler', global_fit=False, n_jobs=1, verbose=False, columns=None)
```

`Pipeline` sequences Darts data transformers. Fittable transformers must be fit before transforming. Invertible transformers can support `inverse_transform()` when every stage in the path supports inversion.

## Common transformer roles

| Transformer/API | Use | Notes |
| --- | --- | --- |
| `MissingValuesFiller` | fill NaNs in target/covariate series | `fill='auto'` interpolates; use constants when required by the data policy. |
| `Scaler` | scale target/covariate values | Wraps a sklearn-like scaler; fit only on train for leakage-safe validation. |
| `Pipeline` | sequence transformers | Keep the fitted pipeline object for validation/test transforms and inverse transforms. |
| `Mapper`/`InvertibleMapper` | elementwise value maps | Use when simple deterministic value transforms are enough. |
| time-series generation helpers | generated calendar/cyclic covariates | Use for day/month/year/position-like covariates; validate span and frequency. |

## Leakage-safe split pattern

```python
from darts.dataprocessing import Pipeline
from darts.dataprocessing.transformers import MissingValuesFiller, Scaler

train, val = series[:-12], series[-12:]
pipe = Pipeline([MissingValuesFiller(), Scaler()])
train_t = pipe.fit_transform(train)
val_t = pipe.transform(val)
# fit model on train_t, predict on transformed scale
forecast_original_scale = pipe.inverse_transform(forecast_transformed, partial=True)
```

Fit the pipeline once on train. Do not call `fit_transform()` on validation or test data. `MissingValuesFiller` is not invertible, so a pipeline that includes it needs `partial=True` to inverse-transform only invertible stages such as `Scaler`.

## Covariate span checklist

For `predict(n=horizon)` with future covariates:

- Future covariates must include the time range required by the model through the forecast horizon.
- The covariate frequency must match or be compatible with the target frequency.
- For multiple target series, use a parallel sequence of future-covariate series.
- If using lagged models, include enough history for the configured lags and enough future points for positive/required future lags.

For past covariates:

- Past covariates usually need historical coverage across training and prediction contexts.
- Torch and regression models have model-specific lag/chunk requirements; route to their owning sub-skills after constructing valid covariates.

## Stacking generated covariates

```python
from darts.utils.timeseries_generation import datetime_attribute_timeseries

cov1 = datetime_attribute_timeseries(series, attribute="dayofweek", one_hot=False)
cov2 = datetime_attribute_timeseries(series, attribute="month", one_hot=False)
future_covariates = cov1.stack(cov2)
assert future_covariates.n_components == 2
```

When the forecast horizon extends beyond the target index, generate covariates on an extended index or an extended dummy time span rather than appending target values.
