# Forecasting workflows

## Baseline plus core probabilistic forecast

```python
from darts.models import NaiveSeasonal, ExponentialSmoothing
from darts.metrics import mae, rmse

horizon = 12
train, val = series[:-horizon], series[-horizon:]

baseline = NaiveSeasonal(K=12)
baseline.fit(train)
baseline_forecast = baseline.predict(horizon)
assert len(baseline_forecast) == horizon

model = ExponentialSmoothing()
model.fit(train)
forecast = model.predict(horizon, num_samples=100)
assert len(forecast) == horizon
assert forecast.n_samples >= 1

point_forecast = forecast.quantile(0.5) if forecast.is_stochastic else forecast
print(float(mae(val, point_forecast)))
print(float(rmse(val, point_forecast)))
```

Use generated or caller-provided `TimeSeries`; do not depend on original repo CSVs or notebooks.

## Lagged regression with covariates

```python
from darts.models import LinearRegressionModel

model = LinearRegressionModel(
    lags=14,
    lags_past_covariates=7,
    lags_future_covariates=[0, 1, 2, 3, 4, 5, 6],
)
model.fit(train, past_covariates=past_cov, future_covariates=future_cov)
forecast = model.predict(n=horizon, past_covariates=past_cov, future_covariates=future_cov)
```

Before fitting:

- Validate all target/covariate frequencies and spans.
- For multiple series, pass sequences with matching order.
- Use enough target history for `lags` and enough covariate history/future coverage for configured covariate lags.

## Historical forecasts/backtesting overview

Darts models support historical forecast/backtesting workflows, but they can become expensive when retraining many times. Keep agent-generated checks bounded:

- Use small synthetic or user-provided slices first.
- Set short horizons and limited windows.
- Decide whether retraining is required for the user's evaluation question.
- Route metric reductions and reporting to `evaluation-and-explainability`.

## Model persistence handoff

Many Darts models expose save/load behavior, but persistence details differ by model family. For torch models and checkpoints, route to `torch-and-foundation-models`. For core models, prefer ordinary Darts model save/load only after the forecast workflow passes tiny validation.

## Validation checklist

After every forecast:

```python
assert len(forecast) == horizon
assert forecast.start_time() > train.end_time()
assert forecast.n_components == train.n_components or expected_output_components
assert not forecast.pd_dataframe().isna().all().all()
```

For probabilistic forecasts, additionally check `forecast.n_samples` and use median/quantile outputs deliberately.
