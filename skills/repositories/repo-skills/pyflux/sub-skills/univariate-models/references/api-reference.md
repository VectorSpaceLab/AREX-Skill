# API Reference

## Purpose

Verified constructors, post-fit methods, and data/formula rules for the univariate routes.

## Constructors

| Model | Verified signature | Notes |
| --- | --- | --- |
| `ARIMA` | `ARIMA(data, ar, ma, integ=0, target=None, family=Normal())` | Accepts `pd.DataFrame` or `np.ndarray`; `target` selects the series when needed. |
| `ARIMAX` | `ARIMAX(data, formula, ar, ma, integ=0, family=Normal())` | Requires a `pd.DataFrame` and a patsy formula. |
| `NNAR` | `NNAR(data, ar, units, layers, integ=0, target=None, family=Normal(), activation=np.tanh, initialize_random=True)` | BBVI-only model; `units` and `layers` size the network. |

### Families that are safe to mention here

- Continuous defaults and tested alternatives: `Normal()`, `t()`, `Laplace()`, `Cauchy()`, `Skewt()`.
- Count examples: `Poisson()`.
- Detailed prior and inference choices live in the root [`families-and-inference`](../../../references/families-and-inference.md) reference; this page only records which families were exercised with the univariate models.

## Fit and latent-variable lifecycle

| Method | Availability | Important notes |
| --- | --- | --- |
| `fit(method=None, **kwargs)` | `ARIMA`, `ARIMAX`, `NNAR` | `ARIMA` and `ARIMAX` support `MLE`, `PML`, `Laplace`, `M-H`, and `BBVI`; `NNAR` supports `BBVI` only. `method=None` uses the model default (`MLE` for `ARIMA`/`ARIMAX`, `BBVI` for `NNAR`). |
| `adjust_prior(index, prior)` | all three | Changes latent-variable priors. `index` may be an int or list. |
| `plot_z(indices=None, figsize=(15, 5))` | all three | Plots latent variables and uncertainty. |
| `plot_fit(**kwargs)` | all three | Compares fitted mean/filter to the observed series. |

Post-fit result objects are returned by `fit()` and expose `.summary()`. When `record_elbo=True` is passed to BBVI, the returned results object also exposes `elbo_records`.

## Prediction and diagnostics

| Method | Availability | Inputs | Output / notes |
| --- | --- | --- | --- |
| `predict(h=5, intervals=False)` | `ARIMA`, `NNAR` | `h` forecast steps | Returns a `DataFrame` indexed by future dates. `intervals=True` adds 1/5/95/99 percentiles. |
| `predict(h=5, oos_data=None, intervals=False)` | `ARIMAX` | `oos_data` must be a `DataFrame` with the same columns as the training data | The first `h` rows are used for the forecast path; the response column may be NaN and is filled with 0 before the patsy design is rebuilt. |
| `predict_is(h=5, fit_once=True, fit_method='MLE', intervals=False)` | all three | Rolling in-sample forecast | For `NNAR`, pass `fit_method='BBVI'` explicitly; the inherited default `MLE` is not valid. |
| `plot_predict(...)` | all three | Visual forecast wrapper | `ARIMAX.plot_predict` also requires `oos_data`. |
| `plot_predict_is(...)` | all three | Visual in-sample rolling forecast wrapper | Use `fit_method='BBVI'` for `NNAR`. |
| `sample(nsims=1000)` / `plot_sample(nsims=10, plot_data=True)` | all three after Bayesian fit | Posterior predictive draws only | Requires `BBVI` or `M-H` on `ARIMA`/`ARIMAX`; `NNAR` only supports `BBVI`. Returns a 2D `ndarray`. |
| `ppc(nsims=1000, T=np.mean)` / `plot_ppc(...)` | all three after Bayesian fit | Discrepancy function `T` | Same Bayesian restriction as `sample()`. |

## Data and formula notes

- `ARIMA` accepts `pd.DataFrame` or `np.ndarray`; `target` can be a column name or array index.
- `ARIMAX` requires `pd.DataFrame` data and patsy formulas.
- Use a whitespace-free left-hand side in ARIMAX formulas, for example `y~x1+x2`.
- `predict()` and `plot_predict()` read the left-hand side literally with `self.formula.split("~")[0]`, so a space before `~` can produce a key mismatch such as `y `.
- For ARIMAX forecasting, pass `oos_data` with the same columns as the training frame and at least `h` future rows of exogenous values.
- Count examples should use integer or non-negative count data and `Poisson()`.
- Prediction intervals are reported as 1%, 5%, 95%, and 99% quantiles.
- For count models, interval checks should allow ties (`>=`). For continuous models, the native tests usually expect strict ordering (`>`).
- `NNAR` uses autoregressive lags plus hidden layers; use `ar >= 2` for the most reliable examples.

## Exclusions

- `NNARX` is not exported from `pyflux.arma` or `pyflux` and is not a first-class route.
