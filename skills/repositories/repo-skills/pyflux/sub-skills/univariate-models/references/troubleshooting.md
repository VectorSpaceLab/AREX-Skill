# Troubleshooting

## Purpose

Symptom-driven fixes for the univariate routes.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `KeyError` on the response column during ARIMAX forecasting, often with a name like `y ` | The formula left-hand side is read literally with `self.formula.split("~")[0]`, so a space before `~` becomes part of the key, or the `oos_data` columns do not match the training frame | Prefer `y~x1+x2`; if you must keep the formula text, rename the response column in `oos_data` to match the exact left-hand-side string. |
| `ValueError: Method not supported!` when fitting or rolling-forecasting NNAR | `NNAR` supports `BBVI` only, and `predict_is()` / `plot_predict_is()` inherit a misleading default of `fit_method='MLE'` | Fit with `model.fit('BBVI', ...)` and pass `fit_method='BBVI'` explicitly to rolling-forecast helpers. |
| `No latent variables estimated!` from `predict()`, `sample()`, or `ppc()` | The model was not fitted first, or it was fitted with a method that does not produce the required Bayesian state | Fit first; use `BBVI` or `M-H` on ARIMA/ARIMAX, and `BBVI` on NNAR. |
| Posterior samples or PPCs fail after a classical fit | `sample()` and `ppc()` only work after `BBVI` or `M-H` on ARIMA/ARIMAX and after `BBVI` on NNAR | Refit with a supported Bayesian method before sampling or PPC. |
| Prediction intervals contain NaNs or fail the ordering check | Convergence trouble, too-short series, invalid family for the data, or a discrete family where equal bounds are expected | Refit on finite data, reduce the forecast horizon, and for Poisson models check `>=` rather than strict `>`. |
| NNAR raises a shape alignment error with a very small lag order | `ar=1` can be fragile for the hidden-layer layout used by the current implementation | Use `ar >= 2` in examples unless the simple case has already been verified. |
| Forecasts look too optimistic | Only `M-H` gives fully Bayesian predictive intervals for ARIMA/ARIMAX; BBVI intervals are approximate, and NNAR has no M-H path | Use `M-H` when fully Bayesian intervals matter, or document that NNAR intervals are BBVI-based approximations. |
| ARIMAX forecast fails even though the model fit succeeded | The forecast frame does not include future exogenous values or the same columns as the training DataFrame | Build an `oos_data` DataFrame with the same columns and at least `h` future rows; `y` may be NaN. |
| You found `NNARX` in source and want to use it as a route | It is source-only, undocumented, and not exported as a first-class public model | Route users to `NNAR` for nonlinear autoregression or `ARIMAX` for exogenous regression. |

## Quick recovery order

1. Check the fit method first.
2. Check formula spacing and `oos_data` columns for ARIMAX.
3. Check lag order and series length for NNAR.
4. Check whether the requested diagnostic requires a Bayesian fit.
5. From `sub-skills/univariate-models/`, re-run with the root smoke helper once the root script exists:

   `../../../scripts/smoke_pyflux_models.py --section univariate`
