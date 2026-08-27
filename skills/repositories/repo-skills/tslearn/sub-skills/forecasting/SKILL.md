---
name: forecasting
description: "Fit, predict, and diagnose tslearn VARIMA and AutoVARIMA
  workflows, including variable-length series and seasonal-length caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Forecasting

Use this sub-skill when the task involves `tslearn.forecasting` or `tslearn.forecasting._arima`: fitting `VARIMA`, fitting `AutoVARIMA`, forecasting from fitted data, forecasting a fresh variable-length dataset, or diagnosing ARIMA-order, seasonality, and minimum-length failures.

## Route the task

- Start from the root tslearn router at `../../SKILL.md` for package-wide task routing.
- For constructors, method signatures, shapes, fitted attributes, and minimum-length rules, read `references/api-reference.md`.
- For tiny reproducible `fit`, `predict`, `fit_predict`, AutoVARIMA, and seasonal workflows, read `references/workflows.md`.
- For too-short series, stationarity or seasonal-period setup, and convergence or optimizer issues, read `references/troubleshooting.md`.
- To sanity-check the smallest bundled forecasting workflow, run `python scripts/forecasting_smoke.py`.
- If the blocker is dataset shaping, NaN padding, resampling, or conversion to a time-series dataset, route to `../data-preparation/`.
- If the blocker is forecast scoring such as MAE/MSE/MASE or backend/performance details, route to `../metrics-backends/`.

## Core boundaries

- Cover `VARIMA`, `AutoVARIMA`, `fit`, `predict`, `fit_predict`, `best_estimator_`, variable-length forecasting input, and seasonal/differencing caveats.
- Keep matrix profile, serialization, clustering, and supervised classification outside this sub-skill.
- Keep general preprocessing and metric-selection depth in the sibling sub-skills named above.

## Fast starting point

1. Use `VARIMA(p, d, q, ...)` when the ARIMA orders are already chosen; use `AutoVARIMA(...)` when the task is order selection plus forecasting.
2. For `VARIMA`, every series must have at least `p + q + d + 1 + seasonal_period` real timestamps at both fit and predict time.
3. For `AutoVARIMA`, validate the same shape/feature rules and expect the selected `best_estimator_` to impose its own `VARIMA` minimum-length rule.
4. Run `python scripts/forecasting_smoke.py` before adapting examples to larger user data.
