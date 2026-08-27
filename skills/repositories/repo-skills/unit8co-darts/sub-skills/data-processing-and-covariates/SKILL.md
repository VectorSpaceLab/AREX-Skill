---
name: data-processing-and-covariates
description: "Use Darts preprocessing transformers, Pipeline, missing-value
  filling, scaling, inverse transforms, and covariate span checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data processing and covariates

Use this sub-skill when the user needs to clean/transform Darts `TimeSeries`, fit preprocessing only on training data, inverse-transform forecasts, or build/validate past and future covariates.

## Read first

- [`references/workflows.md`](references/workflows.md) for train-only preprocessing, generated covariates, stacking, and span validation patterns.
- [`references/api-reference.md`](references/api-reference.md) for verified constructor signatures and common transformer/covariate APIs.
- [`references/troubleshooting.md`](references/troubleshooting.md) for leakage, inverse-transform, missing-value, covariate frequency, and horizon coverage errors.
- [`scripts/transform_pipeline_smoke.py`](scripts/transform_pipeline_smoke.py) for a tiny generated pipeline/covariate smoke.

## Route by task

- **Fill missing target values**: use `MissingValuesFiller`, usually inside a `Pipeline`.
- **Scale data**: fit `Scaler` or a `Pipeline` on train only, then transform validation/test; never fit on held-out data.
- **Invert forecast scale**: keep the fitted transformer and call `inverse_transform()` on the forecast with matching components.
- **Generate calendar covariates**: use Darts time-series generation helpers such as datetime/day-of-week attributes or caller-provided covariate tables, then stack components.
- **Fix covariate span errors**: validate target end time, forecast horizon, covariate start/end, frequency, and one covariate series per target series.
- **Choose a model that consumes covariates**: route to `../forecasting-workflows/` for core/regression models or `../torch-and-foundation-models/` for neural models.

## Safe check

```bash
python scripts/transform_pipeline_smoke.py --quiet
```

The script generates a small daily series, fills/scales train data, transforms validation data, inverse-transforms a toy forecast, stacks two future covariates, and asserts horizon coverage.

## Boundaries

This sub-skill prepares data and covariates. It does not decide all model-family details or interpret final metrics. Do not solve future covariate span errors by extending the target series with fake values; extend/regenerate the covariate series instead.
