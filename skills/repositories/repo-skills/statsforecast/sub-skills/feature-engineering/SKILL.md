---
name: feature-engineering
description: "Generate StatsForecast synthetic fixtures, MSTL trend/seasonal
  features, future X_df regressors, and static/exogenous feature panels."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# StatsForecast feature engineering

Use this sub-skill when a task is about constructing or validating StatsForecast input features, especially synthetic panels, AirPassengers fixtures, MSTL trend/seasonal component features, future `X_df` rows, and static/exogenous column conventions for pandas or polars data.

## Load these files

- [Feature workflows](references/feature-workflows.md): end-to-end recipes for `generate_series`, AirPassengers fixtures, `mstl_decomposition`, future `X_df`, static features, and pandas/polars validation.
- [API reference](references/api-reference.md): signatures, imports, dataframe schemas, output columns, and `X_df` shape contracts.
- [Troubleshooting](references/troubleshooting.md): fixes for invalid MSTL models, unsorted panels, horizon/frequency mismatches, optional polars availability, and future-exogenous column alignment.
- [MSTL feature smoke script](scripts/mstl_feature_smoke.py): a tiny runtime check that builds data, runs `MSTL(season_length=7)` decomposition, and asserts future `X_df` rows.

## Fast routing

1. If the user needs to create a small example panel, use `generate_series` or `AirPassengersDF` from [Feature workflows](references/feature-workflows.md).
2. If the user wants trend/seasonal regressors for a downstream model, use `mstl_decomposition` and hand the returned `train_df` plus `X_df` to the forecasting workflow.
3. If the user has extra training columns, decide whether each one is a static feature or a time-varying exogenous regressor, then ensure future rows carry the same needed feature columns.
4. If the issue is final forecast execution, prediction intervals, fitted values, or persistence, route to `core-forecasting` after preparing features.
5. If the issue is choosing the downstream model family or checking whether a model uses exogenous variables, route to `model-selection`.
6. If the issue is Dask, Ray, Spark, Fugue, or local multiprocessing behavior, route to `distributed-execution`.

## Operating cautions

- `mstl_decomposition` expects canonical columns `unique_id`, `ds`, and `y`; rename custom columns before decomposition.
- The function requires an instantiated `statsforecast.models.MSTL`, not a different StatsForecast model.
- Treat the returned `X_df` as the future exogenous table for MSTL-derived features. It must have exactly `h * number_of_series` rows before it is passed to a model that uses exogenous regressors.
- Runtime files here are self-contained; do not depend on source repository notebooks, tests, docs, or local checkout paths.
