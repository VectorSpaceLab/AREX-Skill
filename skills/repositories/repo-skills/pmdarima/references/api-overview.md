# pmdarima API overview

Read this when routing a request or checking the package surface. The public
surface below is distilled from `pmdarima/__init__.py`, package modules, docs,
examples, tests, and installed signature inspection.

## Core estimators

- `pmdarima.ARIMA(order, seasonal_order=(0, 0, 0, 0), ...)` is a fixed-order
  estimator with scikit-learn-like `fit`, `predict`, `predict_in_sample`,
  `update`, `summary`, `resid`, and `fittedvalues` methods.
- `pmdarima.auto_arima(y, X=None, ...)` searches bounded non-seasonal and
  seasonal orders and returns a fitted estimator. `pmdarima.arima.AutoARIMA`
  exposes the estimator form for pipelines and repeated fitting.
- `order=(p,d,q)` controls non-seasonal AR, differencing, and MA terms;
  `seasonal_order=(P,D,Q,m)` controls seasonal terms and observations per
  cycle. `m` must come from the data frequency, not the requested horizon.
- `StepwiseContext(max_steps=None, max_dur=None)` bounds stepwise search. Record
  its limits and search warnings with the chosen order.

## Data and feature components

- `pmdarima.model_selection.train_test_split` creates ordered holdouts.
  `RollingForecastCV` and `SlidingWindowForecastCV` generate chronological
  train/test index pairs with horizon `h`, `step`, `initial`, or `window_size`.
- `pmdarima.preprocessing` provides `BoxCoxEndogTransformer`,
  `LogEndogTransformer`, `FourierFeaturizer`, `DateFeaturizer`, and pipeline
  transformer bases. Transformers generally return `(y, X)` pairs from
  `fit_transform`; read the focused reference before unpacking.
- `pmdarima.pipeline.Pipeline` chains named transformers and an ARIMA-family
  estimator. Keep the estimator last and preserve training/future feature
  schema.
- `pmdarima.datasets` contains offline built-in time-series loaders such as
  `load_wineind`, `load_sunspots`, and `load_airpassengers`.

## Diagnostics and scoring

- `pmdarima.arima.ndiffs`, `nsdiffs`, `diff`, and `decompose` help inspect
  differencing and seasonal structure; they do not replace domain validation.
- `pmdarima.acf`, `pacf`, `plot_acf`, `plot_pacf`, and `tsdisplay` support
  residual/series diagnostics. Plotting is optional and should be headless in
  automation.
- `pmdarima.metrics.smape` and model-selection scorers support forecast
  comparison. Report the exact scoring direction and whether values are raw
  fold predictions, scores, or aggregate statistics.

## Return-shape contracts

- `predict(n_periods=h)` returns a one-dimensional forecast of length `h`.
- `predict(..., return_conf_int=True)` returns `(forecast, conf_int)` where the
  interval has shape `(h, 2)`.
- A model fit with exogenous `X` needs compatible future `X` for each forecast
  row and compatible rows in every update or validation fold.
- A fitted model is not evidence that the forecast is good: inspect held-out
  errors, residuals, interval behavior, data coverage, and baseline models.

Use [forecasting](../sub-skills/forecasting/SKILL.md) for estimator details,
[preprocessing](../sub-skills/preprocessing/SKILL.md) for feature contracts,
[model-selection](../sub-skills/model-selection/SKILL.md) for temporal
validation, [datasets-diagnostics](../sub-skills/datasets-diagnostics/SKILL.md)
for data inspection, and [persistence-update](../sub-skills/persistence-update/SKILL.md)
for artifacts and refreshes.
