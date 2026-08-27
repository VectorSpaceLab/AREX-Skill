# Forecasting API Reference

## Core imports and signatures

```python
from sktime.forecasting.base import ForecastingHorizon
from sktime.forecasting.naive import NaiveForecaster
from sktime.forecasting.theta import ThetaForecaster
from sktime.forecasting.model_evaluation import evaluate
from sktime.split import temporal_train_test_split, SlidingWindowSplitter
```

Verified public signatures include:

- `ForecastingHorizon(values=None, is_relative=None, freq=None)`.
- `NaiveForecaster(strategy='last', window_length=None, sp=1)`.
- `ThetaForecaster(initial_level=None, deseasonalize=True, sp=1, deseasonalize_model='multiplicative')`.
- `evaluate(forecaster, cv, y, X=None, strategy='refit', scoring=None, return_data=False, error_score=nan, backend=None, ...)`.

## Forecasting horizon rules

- Relative horizons are integer steps ahead from the fitted cutoff, e.g. `[1, 2, 3]`.
- Absolute horizons are concrete time indexes, e.g. the index of a held-out
  monthly series; construct them with `is_relative=False`.
- Do not mix relative integers and absolute time stamps in one horizon.
- When scoring against a holdout, ensure `y_pred.index.equals(y_test.index)` for
  absolute horizons or compare after intentional reindexing.

## Estimator capability tags

Use tags to confirm behavior instead of guessing:

```python
forecaster.get_tag("capability:exogenous", False)
forecaster.get_tag("capability:pred_int", False)
forecaster.get_tag("requires-fh-in-fit", False)
forecaster.get_tag("python_dependencies", None)
```

Important gates include exogenous `X`, prediction intervals/quantiles, missing
values, multivariate/global support, random state, and optional dependencies.

## Optional dependency discipline

Base workflows should run with only core sktime dependencies. `forecasting` extras
cover selected integration packages such as `pmdarima`, `prophet`, `statsmodels`,
`statsforecast`, `skpro`, and `arch`. Deep-learning and foundation-model
forecasters may require torch/TensorFlow/Hugging Face packages, model caches, and
sometimes accelerator resources; verify those separately before use.
