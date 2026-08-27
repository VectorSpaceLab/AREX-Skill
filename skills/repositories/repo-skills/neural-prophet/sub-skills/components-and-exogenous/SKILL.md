---
name: components-and-exogenous
description: "Configure NeuralProphet trend, seasonality, autoregression,
  regressors, events, holidays, and multi-series models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Components and exogenous features

Use this sub-skill when the task is to change the forecast structure rather than merely run a basic fit: trend and changepoints, seasonalities, autoregression, lagged regressors, future-known regressors, custom events, holidays, conditional seasonality, or global/local multi-series modeling.

## Load this when the user asks to

- Add or tune trend, changepoints, yearly/weekly/daily/custom seasonalities, additive versus multiplicative components.
- Use `n_lags`, `ar_reg`, `ar_layers`, lagged regressors, or sparse autoregression.
- Add future regressors that are known for forecast periods.
- Add custom events or country holidays with lower/upper windows and regularization.
- Fit global, local, or glocal components with an `ID` column for multiple time series.
- Explain why prediction fails after adding a regressor, event, or conditional seasonality column.

## Start here

1. Read [component-recipes.md](references/component-recipes.md) for task-oriented recipes and dataframe requirements.
2. Read [api-reference.md](references/api-reference.md) for verified constructor and `add_*` signatures.
3. Read [troubleshooting.md](references/troubleshooting.md) for missing future regressor columns, invalid component names, holiday/country issues, lag alignment, and global/local mistakes.
4. Run [scripts/smoke_components.py](scripts/smoke_components.py) for a tiny CPU check that exercises future regressors, custom events, and multi-ID data.

## Boundaries

Stay here for component design and exogenous columns. Route elsewhere for:

- Base dataframe validation, `fit`, `predict`, and future dataframe mechanics: `../core-forecasting/SKILL.md`.
- Validation/test/CV, metrics, quantile regression, and conformal prediction: `../evaluation-and-uncertainty/SKILL.md`.
- Plotting backends, save/load, CLI/version, logging/seeding, accelerators, and TorchProphet migration: `../operations-and-migration/SKILL.md`.

## Fast component checklist

- Add all components before calling `fit`; a fitted model is not meant to be reconfigured and fitted again casually.
- Every extra column configured for training must be present when fitting; every future-known regressor needed for future timestamps must be supplied to `make_future_dataframe` through `regressors_df`.
- Event workflows need an event table with `event` and `ds`, then history data expanded with `create_df_with_events` when appropriate.
- Multi-series/global models need an `ID` column and consistent component choices for global, local, or glocal behavior.
- Keep component names distinct from reserved columns and existing component/event/regressor names.
