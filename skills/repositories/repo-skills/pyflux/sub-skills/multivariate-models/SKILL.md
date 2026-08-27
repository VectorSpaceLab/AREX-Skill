---
name: multivariate-models
description: "Use PyFlux VAR and GPNARX workflows, including multivariate
  DataFrame inputs, autoregressive lags, Gaussian-process kernels, and
  forecasts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# PyFlux multivariate models

Use this sub-skill when the task is a PyFlux vector-autoregression or Gaussian-process nonlinear autoregression workflow.

## Route map

Use this sub-skill for:

- `pf.VAR(data, lags, target=None, integ=0, use_ols_covariance=False)` when the input is a multivariate time series and each variable is a DataFrame column.
- `pf.GPNARX(data, ar, kernel, integ=0, target=None)` when the input is one target series and nonlinear autoregression should be modeled with a Gaussian-process kernel.
- GPNARX kernels: `pf.SquaredExponential()`, `pf.OrnsteinUhlenbeck()`, `pf.RationalQuadratic()`, and `pf.Periodic()`; `pf.ARD()` is exported but known fragile in PyFlux 0.4.17, so check troubleshooting before using it.

Route elsewhere:

- ARIMA, ARIMAX, and NNAR -> `../univariate-models/`.
- State-space models and dynamic regression -> `../state-space-models/`.
- Conditional volatility -> `../volatility-models/`.
- GAS and score-driven models -> `../gas-models/`.
- Raw covariance helpers are implementation details unless the user explicitly asks about PyFlux internals.

## Default operating procedure

1. Decide whether the series is truly multivariate (`VAR`) or one target series with nonlinear lag structure (`GPNARX`).
2. For `VAR`, build a numeric `pandas.DataFrame` with variables as columns, choose `lags`, optionally choose `integ`, and start with the default OLS fit.
3. For `GPNARX`, build one numeric series, choose `ar >= 1`, instantiate a kernel object, and start with the default MLE fit.
4. Forecast with `predict(h=...)` and backtest with `predict_is(...)`; validate horizon length, column count, and finite/non-NaN predictions.
5. Escalate from OLS/MLE to `PML`, `Laplace`, `M-H`, or `BBVI` only when the task needs priors, posterior uncertainty, or regularization.

## References and smoke check

- [API reference](references/api-reference.md)
- [Offline workflows](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- Root [families and inference](../../references/families-and-inference.md) for fit methods, priors, result objects, and posterior diagnostics.
- Root [troubleshooting](../../references/troubleshooting.md) for install/build and legacy live-data failures shared across routes.
- Smoke helper: [`../../scripts/smoke_pyflux_models.py --section multivariate`](../../scripts/smoke_pyflux_models.py)
