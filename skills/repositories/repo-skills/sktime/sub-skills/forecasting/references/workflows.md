# Forecasting Workflows

## Minimal holdout forecast

```python
from sktime.datasets import load_airline
from sktime.forecasting.base import ForecastingHorizon
from sktime.forecasting.naive import NaiveForecaster
from sktime.split import temporal_train_test_split

y = load_airline()
y_train, y_test = temporal_train_test_split(y, test_size=12)
fh = ForecastingHorizon(y_test.index, is_relative=False)
model = NaiveForecaster(strategy="last", sp=12)
y_pred = model.fit(y_train).predict(fh=fh)
assert y_pred.index.equals(y_test.index)
```

Use `ThetaForecaster(sp=12)` when the active environment supports it. Keep a
naive seasonal benchmark even when evaluating a more complex model.

## Future exogenous data

1. Verify the chosen forecaster uses exogenous variables with
   `get_tag("capability:exogenous")`.
2. Split `y` and `X` along the same cutoff.
3. Fit with historical `X_train` and predict with `X_future` covering all horizon
   points.
4. If the model ignores `X`, do not pass future covariates as if they affected
   predictions.

## Backtesting

Use `evaluate` with temporal splitters:

```python
from sktime.forecasting.model_evaluation import evaluate
from sktime.forecasting.naive import NaiveForecaster
from sktime.performance_metrics.forecasting import MeanAbsolutePercentageError
from sktime.split import SlidingWindowSplitter

cv = SlidingWindowSplitter(window_length=36, fh=[1, 2, 3], step_length=3)
metric = MeanAbsolutePercentageError(symmetric=True)
result = evaluate(NaiveForecaster(strategy="last", sp=12), cv=cv, y=y,
                  scoring=metric, strategy="refit", error_score="raise")
```

Do not use random train/test split for forecasting targets unless the task is not
time ordered.

## Pipelines and reduction

- Use `TransformedTargetForecaster` for transformations on `y`.
- Use `ForecastingPipeline` for transformations of exogenous `X`.
- Use reduction forecasters when a scikit-learn regressor should forecast a time
  series from lagged features.
- Route transformer parameter details to `transformations-pipelines`, then return
  to this workflow for horizons and forecast evaluation.

## Probabilistic forecasts

Check `capability:pred_int` before calling `predict_interval` or
`predict_quantiles`. Validate coverage/alpha arguments, returned multi-index
columns, and finite interval bounds. If a forecaster lacks the tag, use a wrapper
or select a forecaster that advertises probabilistic output.
