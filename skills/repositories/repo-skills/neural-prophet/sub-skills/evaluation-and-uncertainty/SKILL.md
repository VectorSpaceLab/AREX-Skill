---
name: evaluation-and-uncertainty
description: "Validation, cross-validation, metrics, quantile regression,
  conformal prediction, and uncertainty evaluation workflows for NeuralProphet."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Evaluation and uncertainty

Use this sub-skill when the task mentions train/validation/test splits, holdout metrics, rolling cross-validation, metric collection, quantile forecasts, prediction intervals, split conformal prediction, or uncertainty evaluation.

## Route map

Stay here for:

- `split_df`, sequential train/calibration/test splits, and validation passed through `fit(validation_df=...)`.
- Holdout `test(...)` metrics after fitting a model.
- Rolling folds from `crossvalidation_split_df(...)` and advanced validation/test fold sets from `double_crossvalidation_split_df(...)`.
- Constructor `quantiles`, quantile-forecast columns, `conformal_predict(...)`, and `uncertainty_evaluate(...)`.

Route elsewhere inside this skill graph when the task is mainly about:

- Core `ds`/`y` dataframe preparation, basic `fit`, `predict`, or future dataframe construction: `../core-forecasting/SKILL.md`.
- Trend, seasonality, autoregression, lagged regressors, future regressors, events, holidays, or global/local model configuration: `../components-and-exogenous/SKILL.md`.
- Plotting backends, interval plots, save/load, CLI/version checks, logging, accelerator/trainer operations, or TorchProphet migration: `../operations-and-migration/SKILL.md`.

## Start here

1. For holdout validation/test and rolling backtests, follow `references/evaluation-workflows.md`.
2. For exact method signatures, output columns, and parameter meanings, use `references/api-reference.md`.
3. For quantile, conformal, split leakage, missing metric, and expensive-CV recovery, use `references/troubleshooting.md`.
4. To prove the installed package can run a tiny CPU uncertainty path without network access, run `python scripts/smoke_uncertainty.py` from this sub-skill directory or pass the script path to Python from any working directory.

Assume evaluation dataframes already contain the required `ds`, `y`, optional `ID`, and any configured exogenous columns. This sub-skill explains how to split and evaluate them; it does not redefine the core dataframe schema or component construction contracts.
