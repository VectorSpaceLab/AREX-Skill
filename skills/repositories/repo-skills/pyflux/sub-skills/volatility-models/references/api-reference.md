# API Reference

## Verified constructors

| Class | Verified signature | Key notes |
| --- | --- | --- |
| `GARCH` | `GARCH(data, p, q, target=None)` | Plain conditional variance with a return mean, ARCH terms, and GARCH terms. |
| `EGARCH` | `EGARCH(data, p, q, target=None)` | Beta-t-EGARCH; supports leverage and the same shared fit/predict methods. |
| `EGARCHM` | `EGARCHM(data, p, q, target=None)` | EGARCH with an in-mean `GARCH-M` term. |
| `LMEGARCH` | `LMEGARCH(data, p, q, target=None)` | Two-component long-memory Beta-t-EGARCH. |
| `SEGARCH` | `SEGARCH(data, p, q, target=None)` | Skew-t EGARCH; adds skewness and `v` latent variables. |
| `SEGARCHM` | `SEGARCHM(data, p, q, target=None)` | Skew-t EGARCH in mean; adds `GARCH-M`. |
| `EGARCHMReg` | `EGARCHMReg(data, p, q, formula)` | Formula-driven regression-in-mean model; use the runtime order `data, p, q, formula`. |

> The docs page for `EGARCHMReg` prints a different argument order; use the runtime signature above.

## Shared fit and forecast methods

| Method | Availability | Notes |
| --- | --- | --- |
| `fit(method=None, **kwargs)` | all classes | Supported methods: `MLE`, `PML`, `Laplace`, `M-H`, `BBVI`. `BBVI` uses `iterations`, `batch_size`, `mini_batch`, `learning_rate`, and `record_elbo`; `M-H` uses `nsims`, `cov_matrix`, `map_start`, and `quiet_progress`. |
| `predict(h=5, intervals=False)` | all classes | Returns a positive volatility forecast DataFrame on the transformed scale. `EGARCHMReg` adds `oos_data=None` in its runtime signature. |
| `predict_is(h=5, fit_once=True, fit_method='MLE', intervals=False)` | all classes | Rolling in-sample validation forecast. For `EGARCHMReg`, this is the safest path when the OOS `predict()` path is fragile. |
| `plot_fit`, `plot_predict`, `plot_predict_is` | all classes | Diagnostic plots that mirror fitted conditional volatility and forecast behavior. |
| `plot_z` | all classes | Inspect latent terms such as variance coefficients, leverage, skewness, degrees of freedom, or regression coefficients. |
| `sample(nsims=1000)`, `plot_sample(nsims=10, plot_data=True)`, `ppc(nsims=1000, T=np.mean)`, `plot_ppc(nsims=1000, T=np.mean)` | BBVI or M-H only | Posterior predictive sampling and checks require a Bayesian fit. |

## Leverage-aware classes

`add_leverage()` is available on `EGARCH`, `EGARCHM`, `LMEGARCH`, `SEGARCH`, `SEGARCHM`, and `EGARCHMReg`. Call it before `fit()` so the latent-variable layout matches the asymmetric specification. `GARCH` does not expose leverage.

## Model-shape hints

| Family | Distinctive latent pieces |
| --- | --- |
| `GARCH` | `Vol Constant`, ARCH/GARCH terms, `Returns Constant` |
| `EGARCH` / `EGARCHM` | `v` degrees of freedom; `EGARCHM` adds `GARCH-M`; leverage is optional |
| `LMEGARCH` | Two volatility components, each with p/q terms |
| `SEGARCH` / `SEGARCHM` | `Skewness`, `v`; `SEGARCHM` adds `GARCH-M`; leverage is optional |
| `EGARCHMReg` | Formula-driven `Vol Beta ...` and `Returns Beta ...` terms for each regressor |

## Data and output notes

- Use returns or log returns, not price levels.
- Constructor-based models accept a DataFrame or ndarray; `target` selects the series when the input has multiple columns.
- `EGARCHMReg` requires a pandas DataFrame plus a patsy formula, and its `oos_data` must include the same formula columns when forecasting.
- Forecast outputs are conditional volatility on the positive scale, not raw returns.
- M-H intervals are the most Bayesian; MLE and BBVI intervals are approximate and do not fully propagate latent-variable uncertainty.
- Legacy docs and tests use live Yahoo/FRED data readers; do not copy those into runtime guidance or smoke checks.
- `SEGARCH` and `SEGARCHM` add a skewness parameter and can be slower or more fragile than the t-based families.
