---
name: model-selection
description: "Evaluate ordered pmdarima forecasts with sequential holdouts,
  rolling or sliding cross-validation, aligned exogenous data, and explicit
  error scoring without temporal leakage."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model selection

Route here when the question is **how to evaluate or compare** forecasting
estimators on ordered observations. The route covers positional
`train_test_split`, `RollingForecastCV`, `SlidingWindowForecastCV`,
`check_cv`, `cross_validate`, `cross_val_score`, `cross_val_predict`, and
`pmdarima.metrics.smape`.

## Route

1. State the observation order, target `y`, optional exogenous schema and
   availability-at-origin rule, forecast horizon `h`, untouched final holdout,
   scorer, and a fold/fit budget.
2. Use `train_test_split` for one chronological holdout. Use
   `RollingForecastCV` for expanding history or `SlidingWindowForecastCV` for a
   fixed-size recent history. Materialize folds before fitting and inspect the
   exact boundaries.
3. Pass `y` and the complete positional `X` together. `X` must have one row per
   `y` row, including test rows, and the same columns at fit and prediction.
   Fit feature transformations inside the estimator or pipeline on each fold;
   route feature construction to [preprocessing](../preprocessing/SKILL.md).
4. Use `cross_val_score` for one error per fold, `cross_validate` when fit and
   score timings are needed, and `cross_val_predict` for forecast values.
   pmdarima returns raw errors: lower MAE, MSE, and SMAPE is better.
5. Map averaged predictions back to original positions with the materialized
   test indices. The default output omits training and uncovered positions and
   has no timestamp metadata.
6. Keep `h`, `step`, fold count, estimator order/search, and optimizer
   iterations bounded. Run the bundled local smoke test for a minimal check:
   [cross_validate_forecast.py](scripts/cross_validate_forecast.py).

Read all three route references before making an evaluation decision:
[API reference](references/api-reference.md),
[workflows](references/workflows.md), and
[troubleshooting](references/troubleshooting.md).

## Guardrails and handoffs

- Never shuffle or use random K-fold splitting for a forecast evaluation.
- Never let a training position reach its test fold, or derive test-time `X`
  from realized test targets.
- `cross_val_predict` requires `step <= h`; otherwise it rejects the geometry
  rather than returning silently gapped predictions.
- `scoring=None` is invalid in this API. Supply an exact supported name or a
  callable `metric(y_true, y_pred)`.
- A geometrically valid fold may still be too short for the chosen ARIMA,
  seasonal terms, differencing, or transformer. Route order, seasonality,
  estimator fitting, and forecast intervals to [forecasting](../forecasting/SKILL.md).
- Route target/exogenous feature construction, Fourier/date features,
  transformations, and pipeline fold-fitting to
  [preprocessing](../preprocessing/SKILL.md).

The operating guidance is distilled from pmdarima v2.1.1 at commit
`4c2dfccb28f64d2c00a5e10b59c1d1a3e16576a9`, including model-selection source,
metrics, tests, examples, README usage, and the user-guide index. Runtime
files are self-contained and do not require the source checkout.
