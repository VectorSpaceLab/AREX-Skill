# Multivariate models API reference

Use `import pyflux as pf` and keep these models data-driven rather than formula-driven.

## Quick routing

| Goal | Use |
| --- | --- |
| Multivariate linear autoregression | `pf.VAR` |
| One target series with nonlinear lag structure and a kernel | `pf.GPNARX` |
| Single-series ARIMA / ARIMAX / NNAR | route to `../univariate-models/` |
| Dynamic regression / state-space | route to `../state-space-models/` |

## VAR

### Constructor

`pf.VAR(data, lags, target=None, integ=0, use_ols_covariance=False)`

| Argument | Notes |
| --- | --- |
| `data` | Prefer a numeric `pandas.DataFrame` with variables as columns. The model is multivariate-first. |
| `lags` | Positive integer number of autoregressive lags. |
| `target` | Present in the public signature, but this runtime path is still multivariate-first. Do not rely on it to slice a single-column model; if you only need one series, use a univariate route. |
| `integ` | Number of differences applied to every variable before fitting. |
| `use_ols_covariance` | Use the fixed OLS covariance path instead of the estimated covariance path. |

### Fit methods

`fit(method=None, **kwargs)` uses the model default, which is `OLS`.

Supported methods:

- `OLS`
- `MLE`
- `PML`
- `Laplace`
- `M-H`
- `BBVI`

Notes:

- `OLS` is the default and the fastest first check.
- `M-H` accepts `nsims`.
- `BBVI` accepts `iterations`, `optimizer`, `batch_size`, `mini_batch`, `learning_rate`, and related inference kwargs.
- `PML` and `MLE` are optimization-based routes; use them when you want point estimates or regularization-style inference.

### Important methods

| Method | What it returns |
| --- | --- |
| `predict(h=5)` | A `DataFrame` of `h` future rows, one column per series. |
| `predict_is(h=5, fit_once=False, fit_method='OLS', **kwargs)` | Rolling in-sample predictions. Use `fit_once=True` for a faster replay. |
| `plot_predict(h=..., past_values=..., intervals=...)` | Forecast plot for each series. |
| `plot_predict_is(h=..., ...)` | Rolling in-sample plot for each series. |
| `plot_fit(**kwargs)` | Fit-vs-data plots for each series. |
| `adjust_prior(index, prior)` | Advanced prior adjustment for latent variables. |

### Data and forecast notes

- `integ` differences the full multivariate series before fitting.
- Forecasts are produced per variable, so the output shape should match `h x n_series`.
- Keep the input numeric and aligned; the model expects each column to be a separate variable.
- If you difference the data, rebuild level forecasts yourself; the model does not automatically invert differencing.

## GPNARX

### Constructor

`pf.GPNARX(data, ar, kernel, integ=0, target=None)`

| Argument | Notes |
| --- | --- |
| `data` | A single numeric series as a `DataFrame` column or 1D array-like input. |
| `ar` | Positive integer number of autoregressive terms. The constructor raises if `ar < 1`. |
| `kernel` | A kernel object instance, not a string. Example: `pf.SquaredExponential()`. |
| `integ` | Number of differences applied before the lag matrix is built. |
| `target` | Column or index selector for the single target series. |

### Fit methods

`fit(method=None, **kwargs)` uses the model default, which is `MLE`.

Supported methods:

- `MLE`
- `PML`
- `Laplace`
- `M-H`
- `BBVI`

Notes:

- GPNARX does not use `OLS`.
- `M-H` accepts `nsims`.
- `BBVI` accepts `iterations`, `optimizer`, `batch_size`, `mini_batch`, `learning_rate`, and related inference kwargs.
- `predict_is` reuses the model default fit path internally unless you explicitly refit the replay model yourself.

### Important methods

| Method | What it returns |
| --- | --- |
| `predict(h=5)` | A `DataFrame` with `h` forecast rows for the target series. |
| `predict_is(h=5, fit_once=True)` | Rolling one-step in-sample predictions. |
| `plot_predict(h=..., past_values=..., intervals=...)` | Forecast plot with intervals. |
| `plot_predict_is(h=..., fit_once=...)` | Rolling in-sample plot. |
| `plot_fit(intervals=True, **kwargs)` | Fit-vs-data plot. |

### Data and kernel notes

- GPNARX is a univariate autoregression plus kernel model, not a multivariate VAR substitute.
- The model normalizes the target series internally after lag trimming.
- The constructor assigns `kernel.X` from the lag design matrix, so you should pass a kernel instance and let the model wire it up.
- Keep sample sizes modest in validation runs because kernel matrices grow quickly with data length.

## Kernels

All kernel classes accept `X=np.array([1])` by default, but the model overwrites `kernel.X` during initialization.

| Kernel | Typical use |
| --- | --- |
| `pf.SquaredExponential()` | Smooth nonlinear dynamics. |
| `pf.OrnsteinUhlenbeck()` | Rougher exponential-decay correlation. |
| `pf.ARD()` | Separate relevance/length-scale behavior per lag dimension, but PyFlux 0.4.17's ARD path is known fragile because it refers to `families.FLat`; prefer another kernel unless maintaining a patched source tree. |
| `pf.RationalQuadratic()` | Multiple length-scale behavior in one kernel. |
| `pf.Periodic()` | Repeating or seasonal patterns. |

## Practical validation checklist

- Confirm the constructor signature matches the route you want.
- Fit with the default method first.
- Verify finite latent variables and non-NaN predictions.
- Verify the forecast horizon length matches `h`.
- Prefer synthetic offline checks before any real dataset run.

See also: [Offline workflows](workflows.md) and [Troubleshooting](troubleshooting.md).
