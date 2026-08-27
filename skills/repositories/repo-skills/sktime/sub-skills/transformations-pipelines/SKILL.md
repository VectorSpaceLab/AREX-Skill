---
name: transformations-pipelines
description: "Transform time series, extract features, and compose sktime
  transformer and forecasting pipelines."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Transformations and Pipelines

Use this sub-skill when the task is to transform `sktime` time-series data,
extract features, repair missing values, create lag/window/difference/detrended
series, or compose transformers with other estimators.

## Route here

- Transform a univariate, multivariate, panel, or hierarchical time series.
- Extract features with `SummaryTransformer`, `WindowSummarizer`, `Tabularizer`,
  `Rocket`/`MiniRocket`, `tsfresh`, `catch22`, or related transformers.
- Difference, lag, impute, interpolate, detrend, deseasonalize, or create date,
  Fourier, and holiday features.
- Build transformer-only pipelines with `*`, `+`, `TransformerPipeline`,
  `FeatureUnion`, `OptionalPassthrough`, or `make_pipeline`.
- Decide whether a transformer belongs on target `y` via
  `TransformedTargetForecaster` or on exogenous `X` via `ForecastingPipeline`.

## Route away

Forecasting objective design routes to `forecasting`; raw mtype/file conversion
to `data-interfaces`; classifier/regressor/clusterer behavior to `panel-learning`.

## References and helper

- [API reference](references/api-reference.md) for signatures, categories,
  composition, pipeline semantics, and optional surfaces.
- [Workflows](references/workflows.md) for concrete fit/transform and pipeline recipes.
- [Troubleshooting](references/troubleshooting.md) for mtype errors, index
  changes, inverse-transform failures, optional dependencies, and parameter names.
- Run [scripts/transform_pipeline_smoke.py](scripts/transform_pipeline_smoke.py)
  for an offline transformer and transformed-target pipeline check.
