---
name: core-forecasting
description: "Operate normal StatsForecast pandas/polars panel forecasting
  workflows, including schema, forecasts, fitted values, cross-validation,
  intervals, exogenous future data, custom columns, persistence, plotting,
  fallback models, and local n_jobs choices."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# core-forecasting

Use this sub-skill when the user needs the `StatsForecast` orchestrator for local pandas or polars panel forecasting: build the input schema, construct `StatsForecast`, run forecasts, get fitted values, perform temporal cross-validation, add intervals, pass future exogenous data, use custom column names, save/load fitted objects, create basic plots, and choose local `n_jobs`/`fallback_model` behavior.

## Route boundaries

Stay in this sub-skill for:

- Native pandas or polars panels with id, time, target, and optional exogenous columns.
- `forecast`, `fit`/`predict`, `fit_predict`, `forecast_fitted_values`, `cross_validation`, and `cross_validation_fitted_values` workflows.
- Prediction interval plumbing, including `level` and `ConformalIntervals` usage at the orchestrator level.
- Custom `id_col`, `time_col`, and `target_col` names.
- Basic `plot`, `save`, and `load` calls.
- Local process parallelism through `n_jobs` and primary-model recovery through `fallback_model`.

Route out when the user is really asking for:

- Which forecasting model family or model constructor to use: load `model-selection`.
- MSTL decomposition or future seasonal/trend feature generation: load `feature-engineering`.
- Dask, Ray, Spark, Fugue engines, distributed dataframes, or cluster behavior: load `distributed-execution`.

## Operating sequence

1. Validate the panel layout and time frequency using [references/data-formats.md](references/data-formats.md).
2. Pick or confirm model objects elsewhere if model choice is non-trivial, then construct `StatsForecast` using [references/api-reference.md](references/api-reference.md).
3. Select the workflow (`forecast` vs `fit`/`predict` vs `fit_predict` vs cross-validation) from [references/workflows.md](references/workflows.md).
4. If the panel contains extra columns and any model uses exogenous regressors, build a future `X_df` with all ids, all future timestamps, and the same exogenous columns.
5. If adding intervals, pass a list-like `level` and check conformal sample-size requirements before running expensive jobs.
6. If a call fails, diagnose with [references/troubleshooting.md](references/troubleshooting.md) before changing model families.
7. To sanity-check an installed runtime without a repository checkout, run [scripts/core_forecast_smoke.py](scripts/core_forecast_smoke.py); use `--help` to see optional custom-column, exogenous, and interval checks.

## Output expectations

Core `StatsForecast` calls return the same dataframe family as the native input when possible. Forecast outputs contain id/time columns plus one column per model and, when requested, interval columns named like `<model>-lo-80` and `<model>-hi-80`. Cross-validation outputs add `cutoff` and observed target values. Fitted-value helpers only work after the corresponding call used `fitted=True`.
