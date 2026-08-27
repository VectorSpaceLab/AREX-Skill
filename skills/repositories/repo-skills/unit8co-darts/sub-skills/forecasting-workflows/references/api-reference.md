# Forecasting API reference

## Fit/predict convention

Darts forecasting models generally follow:

```python
model.fit(series, past_covariates=None, future_covariates=None, ...)
forecast = model.predict(n, series=None, past_covariates=None, future_covariates=None, num_samples=1, ...)
```

Exact accepted arguments vary by model. Do not assume covariate or `num_samples` support across all families.

## Common imports

```python
from darts.models import (
    NaiveMean,
    NaiveSeasonal,
    NaiveDrift,
    ExponentialSmoothing,
    LinearRegressionModel,
)
```

Optional model imports may fail until extras are installed:

```python
from darts.models import LightGBMModel, XGBModel, CatBoostModel, Prophet
```

Torch model imports require `darts[torch]` and are owned by `torch-and-foundation-models`.

## Core examples

### Naive seasonal

```python
model = NaiveSeasonal(K=12)
model.fit(train)
forecast = model.predict(12)
```

### Exponential smoothing

```python
model = ExponentialSmoothing()
model.fit(train)
forecast = model.predict(len(val), num_samples=100)
```

### Linear regression with lags

```python
model = LinearRegressionModel(lags=12)
model.fit(train)
forecast = model.predict(6)
```

With covariates:

```python
model = LinearRegressionModel(lags=12, lags_future_covariates=[0, 1, 2])
model.fit(train, future_covariates=future_covariates)
forecast = model.predict(3, future_covariates=future_covariates)
```

## Output checks

- `len(forecast)` should equal `n`.
- `forecast.start_time()` should follow the training target end time for ordinary future forecasts.
- `forecast.n_components` should match expected target/output width.
- `forecast.n_samples > 1` indicates a stochastic forecast; deterministic forecasts usually have one sample.
- Use `forecast.quantile(q)` or `forecast.mean()`/median-like operations deliberately when metrics expect deterministic series.
