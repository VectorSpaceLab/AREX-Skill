---
name: forecasting
description: "Guide Auto-PyTorch time series forecasting workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Forecasting

Use this sub-skill for Auto-PyTorch time series forecasting. It covers sequence validation, horizon setup, known future features, forecasting-specific search and prediction, and the public forecasting task API.

## When to use

Choose this route when the user asks to:

- forecast future values from one or more time series
- format sequences with `start_times`, `freq`, or `series_idx`
- provide known future features
- control the forecast horizon with `n_prediction_steps`
- inspect or customize forecasting-specific initialization and metrics
- validate uni-variant versus multi-variant forecasting data

## What this route owns

- `TimeSeriesForecastingTask`
- `TimeSeriesForecastingPipeline`
- `TimeSeriesForecastingInputValidator`
- `TimeSeriesFeatureValidator`
- `TimeSeriesTargetValidator`
- `TimeSeriesSequence`
- `TimeSeriesForecastingDataset`
- forecasting search, fit, predict, and score flows
- forecasting metrics and sliding-window setup

## Main workflow

1. Decide whether the input is uni-variant or multi-variant.
2. Build the sequence layout:
   - lists of series, or
   - DataFrames with series identifiers
3. Set `start_times` and `freq` when the series need explicit temporal context.
4. Provide `known_future_features` if the forecast uses exogenous features that are already known for the future.
5. Use `search(...)` for end-to-end forecasting AutoML or `get_search_space(...)` / `fit_pipeline(...)` for a single configuration.
6. Call `predict(...)` with either prepared `TimeSeriesSequence` objects or the raw future-features path plus `past_targets`.

## Common decisions

### Data layout

- Uni-variant tasks may omit `X_train` and validate only targets.
- Multi-variant tasks require feature data.
- When `series_idx` is used, the feature DataFrame must contain those identifier columns.
- The validator preserves per-series order and emits sequence-aware outputs.

### Search control

- `enable_traditional_pipeline` is disabled by default for forecasting.
- `suggested_init_models` and `custom_init_setting_path` let you bias the starting models.
- `search_space_updates` is often used to adjust `window_size`, `batch_size`, or batches-per-epoch when the default window is not appropriate.

### Metrics

Typical forecasting metrics include:

- `mean_MASE_forecasting`
- `median_MASE_forecasting`
- `mean_MAE_forecasting`
- `mean_MAPE_forecasting`
- `mean_MSE_forecasting`

## What to read next

- `references/workflows.md` for end-to-end forecasting recipes and input-shape examples
- `references/api-reference.md` for the main class and method signatures
- `references/troubleshooting.md` for missing-dependency, shape, and sequence-identity failures
- `scripts/forecasting_smoke.py` for a tiny synthetic sequence validation check

## Do not use this route for

- tabular classification or regression
- image classification proof-of-concept paths
- repo-maintenance or CI workflows

Route tabular questions to `sub-skills/tabular-automl/` instead.
