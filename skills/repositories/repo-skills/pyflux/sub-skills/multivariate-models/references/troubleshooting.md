# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| VAR input errors or wrong series count | The input is not a numeric multivariate frame, or the variables are not stored as columns. | Use a numeric `pandas.DataFrame` with one column per variable. Keep the column order deliberate. |
| `target` does not seem to narrow a VAR fit | This runtime path is still multivariate-first. | Feed the exact multivariate frame you want modeled. If you truly need a one-series workflow, route to `univariate-models` instead. |
| Need a one-series nonlinear autoregression | GPNARX is the correct model; VAR is not a substitute. | Use `pf.GPNARX(...)` with one target series and a kernel object. |
| `kernel_type='OU'` or a kernel string fails | GPNARX expects a kernel instance, not a name string. | Instantiate `pf.SquaredExponential()`, `pf.OrnsteinUhlenbeck()`, `pf.ARD()`, `pf.RationalQuadratic()`, or `pf.Periodic()` and pass the object to `GPNARX`. |
| `ValueError: Cannot have less than 1 AR term!` | `ar` was set below 1. | Use `ar >= 1`. |
| `AttributeError: module 'pyflux.families' has no attribute 'FLat'` with `pf.ARD()` | This PyFlux release has a typo in the ARD kernel latent-variable builder | Use `SquaredExponential`, `OrnsteinUhlenbeck`, `RationalQuadratic`, or `Periodic` for ordinary work; patch `FLat` to `Flat` only when explicitly maintaining the source. |
| `No latent variables estimated!` | `predict`, `plot_fit`, or `plot_predict` was called before fitting. | Call `fit()` first, then forecast or plot. |
| Forecasts are NaN or unstable | Too many lags, too little data, missing values, or an aggressive kernel choice. | Reduce `lags` / `ar`, shorten the horizon, clean the input, and retry with the default fit method before moving to Bayesian methods. |
| GPNARX is slow on a modest dataset | GP covariance work scales quickly with sample length. | Keep smoke checks short, compare one kernel at a time, and avoid long horizons during validation. |
| Rolling backtests are expensive | `predict_is` refits repeatedly unless you ask it not to. | Use `fit_once=True` for a quick replay. For VAR, keep `fit_method='OLS'` unless you specifically need another estimator. |
| You need covariance internals or impulse-response details | Those are implementation details, not first-line workflow steps. | Prefer the public `use_ols_covariance` flag, the fit methods, and the prediction helpers. |
| Output shape does not match expectations | VAR and GPNARX return different shapes by design. | VAR should return one column per series; GPNARX should return one column for the target series. |

## Quick reminders

- VAR is the multivariate linear route.
- GPNARX is the univariate nonlinear-kernel route.
- Use synthetic, offline checks first.
- Keep sample sizes modest for kernel-based validation.
