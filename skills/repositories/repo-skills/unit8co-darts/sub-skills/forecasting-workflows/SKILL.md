---
name: forecasting-workflows
description: "Use Darts core forecasting workflows, model selection, covariates,
  probabilistic prediction, and fit/predict validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Forecasting workflows

Use this sub-skill for Darts non-neural/core forecasting: model selection, `fit()`/`predict()`, covariate-capable regression/global models, probabilistic forecasts, historical forecasts/backtesting overview, and forecast troubleshooting.

## Read first

- [`references/model-selection.md`](references/model-selection.md) for model-family choices, optional dependency boundaries, and covariate support.
- [`references/workflows.md`](references/workflows.md) for baseline/core forecast, probabilistic forecast, lagged regression covariates, and validation patterns.
- [`references/api-reference.md`](references/api-reference.md) for fit/predict conventions and common model constructors.
- [`references/troubleshooting.md`](references/troubleshooting.md) for unsupported covariates, wrong horizon, probabilistic output, and optional dependency errors.
- [`scripts/forecasting_smoke.py`](scripts/forecasting_smoke.py) for a tiny baseline + ExponentialSmoothing smoke.

## Route by task

- **First forecast or baseline**: start with `NaiveSeasonal`, `NaiveDrift`, or `ExponentialSmoothing` before complex models.
- **No torch allowed**: stay in this sub-skill and use core/statistical/regression models; do not route to neural models.
- **Covariates with lagged/global models**: use `LinearRegressionModel` or other regression/global models with `lags`, `lags_past_covariates`, and/or `lags_future_covariates`.
- **Model rejects covariate arguments**: do not force them. Switch to a model family that supports the requested covariate type.
- **Probabilistic forecast**: verify the model supports samples/likelihood/quantiles, call `predict(..., num_samples=...)` when supported, then route metric details to `../evaluation-and-explainability/`.
- **Neural model, `darts[torch]`, GPU, checkpoint, or foundation wrapper**: route to `../torch-and-foundation-models/`.

## Safe check

```bash
python scripts/forecasting_smoke.py --compact
```

The smoke uses generated monthly data, validates forecast length and stochastic samples, and does not read repo examples or notebooks.

## Boundaries

This sub-skill does not own Darts data construction, preprocessing/covariate generation, PyTorch trainer configuration, anomaly detection, or final metric interpretation. Cross-link instead of duplicating those workflows.
