---
name: core-forecasting
description: "Fit NeuralProphet models, validate time-series dataframes, build
  future dataframes, and run basic forecasts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Core forecasting

Use this sub-skill when the task is to get a NeuralProphet forecast running: prepare a dataframe, choose core model settings, call `fit`, build a future dataframe, call `predict`, or understand the `yhat*` forecast columns.

## Load this when the user asks to

- Create a first NeuralProphet model from a pandas dataframe with `ds` and `y` columns.
- Validate or repair timestamp, target, frequency, missing-value, duplicate-date, or optional `ID` column issues before fitting.
- Choose basic constructor settings such as `n_lags`, `n_forecasts`, `epochs`, `batch_size`, `learning_rate`, `collect_metrics`, and `accelerator='cpu'`.
- Forecast future periods with `make_future_dataframe` and explain historic versus future rows.
- Interpret the shape of `forecast` dataframes, especially `yhat1`, `yhat2`, ... columns.

## Start here

1. Read [workflows.md](references/workflows.md) for the minimal fit/predict recipe, dataframe contract, future dataframe patterns, and validation checklist.
2. Read [api-reference.md](references/api-reference.md) when you need verified signatures and parameter defaults for `NeuralProphet`, `fit`, `predict`, `make_future_dataframe`, and dataframe utility helpers.
3. Read [troubleshooting.md](references/troubleshooting.md) when a fit/predict run fails, frequency inference is wrong, `metrics` is `None`, or dependency versions break current NeuralProphet code.
4. Run [scripts/smoke_forecast.py](scripts/smoke_forecast.py) to prove a tiny CPU fit and prediction can run without network access.
5. Run [scripts/validate_neuralprophet_dataframe.py](scripts/validate_neuralprophet_dataframe.py) before fitting user data when timestamps, `y`, `ID`, or frequency quality is uncertain.

## Boundaries

Stay here for core model execution and dataframe readiness. Route elsewhere for:

- Trend, seasonality, autoregression, regressors, events, holidays, or global/local component design: `../components-and-exogenous/SKILL.md`.
- Validation splits, cross-validation, metrics, quantiles, conformal prediction, and uncertainty evaluation: `../evaluation-and-uncertainty/SKILL.md`.
- CLI/version checks, plotting backends, save/load, logging, seeding, accelerators, and TorchProphet migration: `../operations-and-migration/SKILL.md`.

## Fast decision checklist

- Dataframe has parseable `ds`; training data has `y`; multi-series data uses `ID`.
- Use an explicit pandas frequency string such as `"D"`, `"H"`, `"MS"`, or `"5min"` when `freq='auto'` would be ambiguous.
- Start with CPU, small `epochs`, and disabled seasonalities for smoke tests; add components only after core fit/predict works.
- If `n_lags > 0`, preserve enough history and use `n_historic_predictions` deliberately when constructing future data.
- Do not rely on original repository notebooks or tests at runtime; use the bundled references and scripts here.
