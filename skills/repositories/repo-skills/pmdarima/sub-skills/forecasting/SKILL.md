---
name: forecasting
description: "Fit, search, diagnose, and forecast fixed-order or automatic
  seasonal ARIMA models with pmdarima."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Forecasting

Use this skill when the task is to fit a pmdarima `ARIMA`/`AutoARIMA`, choose orders with `auto_arima`, handle seasonal periods or exogenous regressors, and produce forecasts or intervals. Keep the series and forecast horizon explicit; validate `X` shape before fitting and again before forecasting.

## Operating route

1. Inspect the input as a finite one-dimensional numeric series and decide whether the requested seasonal period `m` is supported by the available history.
2. Start with a constrained fixed-order `ARIMA` when the order is known. Otherwise use stepwise `auto_arima` with a bounded search, `error_action='trace'` while debugging, and a reproducible small `StepwiseContext` when runtime needs a cap.
3. Fit with `y` and, if used, an `X` matrix whose row count equals `len(y)`. For a future forecast, provide exactly one row per period and the same number of columns as training `X`.
4. Call `predict(n_periods=h, return_conf_int=True, alpha=...)` for an out-of-sample forecast and interval matrix, or `predict_in_sample(...)` for fitted values/residual inspection. Examine `model.order`, `model.seasonal_order`, `model.resid()`, and `model.summary()` after fitting.
5. Treat `update(y_new, X=...)` as the observation-refresh handoff to the [persistence-update sub-skill](../persistence-update/SKILL.md); do not use this skill for artifact serialization or update mechanics.

Read the linked references for signatures, bounded workflows, diagnostics, and recovery. Run `scripts/simple_forecast.py --help` before adapting the bundled smoke case; it is deterministic, local, and plotting-free.

## Boundaries

This skill covers `pmdarima.ARIMA`, `pmdarima.auto_arima`, `pmdarima.arima.AutoARIMA`, `StepwiseContext`, seasonal `order`/`seasonal_order`/`m`, exogenous regressors, fitting, prediction, intervals, and residual diagnostics. Preprocessing/transformer internals, cross-validation/model-selection orchestration, and serialization/update artifact mechanics belong to sibling skills.

## Provenance note

The inspected source was tagged `v2.1.1` at commit `4c2dfccb28f64d2c00a5e10b59c1d1a3e16576a9`, while the inspection environment reports package version `0.0.0`. Do not infer a release/version guarantee from this skill; route environment/version discrepancies to root troubleshooting.

## Local references

- [API reference](references/api-reference.md) — signatures, contracts, order semantics, exogenous shapes, and diagnostics.
- [Workflows](references/workflows.md) — fixed, seasonal, automatic, exogenous, interval, and diagnostic procedures.
- [Troubleshooting](references/troubleshooting.md) — symptoms, likely causes, and bounded recovery actions.
- [Deterministic smoke script](scripts/simple_forecast.py) — runnable tiny fixed/seasonal/automatic forecast example.
