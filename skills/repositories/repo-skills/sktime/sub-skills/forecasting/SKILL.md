---
name: forecasting
description: "Forecast univariate, exogenous, probabilistic, panel, and
  hierarchical time series with sktime forecasters, pipelines, reduction,
  backtesting, updating, and model selection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Forecasting

Use this sub-skill when the task is to produce, update, evaluate, tune, or
compose an `sktime` forecast. It covers `ForecastingHorizon`, CPU-safe baseline
forecasters, future exogenous variables, prediction intervals and quantiles,
pipelines and reduction, local/global or hierarchical forecasting, temporal
backtesting, and forecasting model selection.

## Route here

- Forecast future values from a `Series`, panel, or hierarchical target.
- Choose or configure `NaiveForecaster`, `ThetaForecaster`, a reduction
  forecaster, or another public forecaster.
- Convert between relative step-ahead horizons and absolute time-index horizons.
- Supply known future `X`, update a fitted forecaster, or make rolling forecasts.
- Request point forecasts, quantiles, intervals, or variance when the estimator
  advertises probabilistic capability.
- Build `TransformedTargetForecaster`, `ForecastingPipeline`, `ForecastX`, or
  `make_reduction` compositions.
- Backtest with temporal splitters and `evaluate`, or tune forecaster parameters
  with forecasting search estimators.
- Diagnose an unavailable AutoARIMA, Prophet, StatsForecast, or other
  soft-dependency-backed forecaster.

## Route away

- Raw `Series`/`Panel`/`Hierarchical` conversion and datatype validation:
  `data-interfaces`.
- Transformer-only behavior or composition not specific to forecasting:
  `transformations-pipelines`.
- Metric design, splitter-only design, or broad comparative benchmarking:
  `evaluation-benchmarking`.

## Fast decision path

1. Establish target scitype, time index, cutoff, forecast steps, whether future
   `X` is known, and whether output is point or probabilistic.
2. Start with a CPU-safe baseline such as `NaiveForecaster(strategy="last", sp=period)`.
3. Make horizon representation explicit: integer steps are relative; time-like
   indexes should be wrapped as `ForecastingHorizon(index, is_relative=False)`.
4. Fit only on observations available at the cutoff. Pass future `X` to `predict`
   only when the fitted forecaster uses exogenous variables and `X` covers every
   requested forecast index.
5. Validate output index, length, finiteness, and requested probabilistic output.
6. If a model is unavailable, retain the baseline path and report the missing
   optional dependency rather than silently substituting a different model.

## References and helper

- [API reference](references/api-reference.md) for public imports, signatures,
  horizon semantics, output shapes, and capability gates.
- [Workflows](references/workflows.md) for fit/predict, exogenous data,
  probabilistic forecasts, update, pipelines, reduction, evaluation, and tuning.
- [Troubleshooting](references/troubleshooting.md) for horizon/index/X errors,
  insufficient data, missing optional packages, and leakage-safe evaluation.
- Run [scripts/forecasting_smoke.py](scripts/forecasting_smoke.py) for an
  offline no-download forecast and backtest smoke.
