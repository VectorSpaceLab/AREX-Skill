---
name: state-space-models
description: "Build PyFlux Gaussian, non-Gaussian, local-level, local-trend,
  dynamic regression, and dynamic autoregression state-space models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# PyFlux state-space models

Use this sub-skill for PyFlux structural time-series work: local level/trend, dynamic regression, dynamic autoregression, and the family-dispatch wrappers that select the Gaussian or non-Gaussian implementation.

## Route here

- `LLEV(data, integ=0, target=None)` and `LLT(data, integ=0, target=None)` for Gaussian local-level and local-linear-trend models.
- `NLLEV(data, family, integ=0, target=None)` and `NLLT(data, family, integ=0, target=None)` for non-Gaussian local-level and local-linear-trend models.
- `DAR(data, ar, integ=0, target=None)` for dynamic autoregression.
- `DynReg(formula, data)` for Gaussian dynamic regression with Patsy formulas.
- `NDynReg(formula, data, family)` for non-Gaussian dynamic regression.
- `DynamicGLM(formula, data, family)` when you want a selector that returns `DynReg` for `Normal()` and `NDynReg` otherwise.
- `LocalLevel(data, family, integ=0, target=None)` and `LocalTrend(data, family, integ=0, target=None)` when you want the family object to route to the concrete class.

Route elsewhere:

- `GASLLEV` and `GASLLT` go to `../gas-models/`.
- `VAR` and `GPNARX` go to `../multivariate-models/`.
- GARCH/EGARCH-style volatility models go to `../volatility-models/`.
- Do not expose internal Kalman recursion helpers or Cython implementation details as user entry points.

## Default operating procedure

1. Pick the model family first: Gaussian/Kalman-style for continuous responses, non-Gaussian BBVI for counts or other non-Gaussian observations.
2. Use the convenience wrapper when the family should decide the concrete class: `LocalLevel`, `LocalTrend`, or `DynamicGLM`.
3. For formula models, make the training DataFrame columns match the Patsy formula exactly, and supply the same column names in `oos_data` for forecasting.
4. Fit the model, then check `summary()`, `plot_fit()`, `predict()`, and `predict_is()`. For Gaussian models, `predict()` can return intervals; for non-Gaussian point forecasts, `predict()` is simpler and `plot_predict()` carries the visual intervals.
5. Validate with the bundled smoke helper section: [`../../scripts/smoke_pyflux_models.py --section state-space`](../../scripts/smoke_pyflux_models.py).

## References

- [API reference](references/api-reference.md)
- [Workflows](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- Root [families and inference](../../references/families-and-inference.md) for priors, fit methods, result objects, and posterior diagnostics.
- Root [troubleshooting](../../references/troubleshooting.md) for install/build and legacy live-data failures shared across routes.
