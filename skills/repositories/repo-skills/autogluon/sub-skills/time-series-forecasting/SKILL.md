---
name: time-series-forecasting
description: "Use AutoGluon TimeSeriesPredictor and TimeSeriesDataFrame for
  forecasting workflows, covariates, probabilistic forecasts, metrics, model
  presets, evaluation, and time-series troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Time-Series Forecasting

Use this sub-skill when the task is about AutoGluon time-series forecasting with `autogluon.timeseries`, especially `TimeSeriesDataFrame` and `TimeSeriesPredictor`.

## Route Here When

- The user needs multi-step forecasts, prediction intervals, quantiles, backtesting, `leaderboard`, or `evaluate` for time series.
- Data has `item_id`, `timestamp`, and a numeric target column, or must be converted into `TimeSeriesDataFrame`.
- The workflow needs known future covariates, past covariates, static features, frequency inference/resampling, or train/test horizon splits.
- The user asks about time-series model presets, `Chronos`, `Chronos2`, `Toto`, `DeepAR`, `TemporalFusionTransformer`, `DirectTabular`, `RecursiveTabular`, or statistical baselines.

## Route Elsewhere

- General supervised classification/regression on rows: use `../tabular-ml/`.
- Text, image, document, object detection, or semantic matching AutoMM workflows: use `../multimodal-automl/`.
- Package installation, import/version checks, backend compatibility, or cross-subpackage save/load issues: use root `../../references/troubleshooting.md`.

## Read First

- `references/data-formats.md` for constructing `TimeSeriesDataFrame`, required columns, frequency, covariates, static features, and validation patterns.
- `references/api-reference.md` for `TimeSeriesPredictor` and `TimeSeriesDataFrame` method signatures and behavior.
- `references/workflows.md` for quick-start, covariate, backtesting, probabilistic forecast, save/load, and feature-importance workflows.
- `references/model-and-metric-guide.md` for model families, presets, metrics, quantiles, Chronos/Toto constraints, and offline-safe choices.
- `references/troubleshooting.md` for common forecasting failures and fixes.

## Bundled Scripts

- `scripts/validate_timeseries_frame.py`: validates a tiny or user-provided CSV/Parquet file as a `TimeSeriesDataFrame`, checks schema, static features, frequency, series length, and known-covariate horizon coverage.
- `scripts/timeseries_smoke.py`: builds a tiny in-memory dataset and verifies `TimeSeriesDataFrame`; pass `--fit` to run a deliberately small local-model predictor fit.

## Default Agent Strategy

1. Normalize the data into `TimeSeriesDataFrame` with `item_id`, `timestamp`, and target columns before discussing models.
2. Confirm `prediction_length`, frequency, target name, known future covariates, and whether static features must be carried into prediction.
3. For offline or quick validation, choose `hyperparameters={"Naive": {}, "SeasonalNaive": {}, "Theta": {}}` or `presets="fast_training"`; avoid Chronos/Toto unless model artifacts and required backends are available.
4. Use `train_data, test_data = data.train_test_split(prediction_length)` for evaluation and ensure every series is long enough for the requested horizon and validation windows.
5. Expect predictions as a `TimeSeriesDataFrame` with `mean` plus quantile columns such as `0.1`, `0.5`, and `0.9`.
