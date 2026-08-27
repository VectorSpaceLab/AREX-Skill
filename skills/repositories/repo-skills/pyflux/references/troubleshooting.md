# PyFlux Troubleshooting

## Purpose

Use this reference for cross-cutting PyFlux install, import, data, inference, and runtime problems. For model-specific details, use the nearest sub-skill troubleshooting page.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError`, `_check_build` failure, or missing compiled recursion module | PyFlux includes Cython extensions and is easiest on an older Python/Numpy stack | Use a Python 3.7-era environment with compatible `numpy`, `pandas`, `scipy`, `patsy`, and `numdifftools`; reinstall PyFlux; for source builds, ensure `Cython` and a compiler are available. |
| Installation fails on modern Python such as 3.11+ | Legacy package metadata and generated C extensions were written for older Python releases | Prefer a compatible older environment instead of patching generated C files during ordinary package use. |
| Examples or tests fail on `pandas.io.data.DataReader`, Yahoo, FRED, or HTTP CSVs | Old docs/tests used live data readers and remote files | Replace with local synthetic data or a local CSV fixture; use bundled smoke helpers for offline validation. |
| Forecast method raises `No latent variables estimated!` | `predict`, plotting, sampling, or PPC was called before `fit()` | Fit first, then re-run the forecast or diagnostic. |
| `ValueError: Method not supported!` | The selected model does not expose that inference method | Check `model.supported_methods`; use `OLS` for VAR default, `BBVI` for NNAR, and non-Gaussian state-space class-specific BBVI `fit(...)`. |
| `sample()` or `ppc()` fails after MLE/PML/OLS/Laplace | Posterior predictive draws require a Bayesian fit | Refit with `BBVI` or `M-H` before calling posterior predictive helpers. |
| `KeyError` on ARIMAX response during forecast, often with a trailing-space column such as `y ` | ARIMAX forecast code reads the formula left side literally with `split("~")[0]` | Prefer formulas like `y~x1+x2` without a space before `~`, or make the forecast frame column match the exact left-hand side. |
| Patsy formula errors in ARIMAX/GASX/GASReg/DynReg/NDynReg | Training and forecast DataFrame columns differ, or the response placeholder is missing | Keep identical column names and include the response column in `oos_data`; future response values may be `NaN` or placeholder zeros depending on the class. |
| Forecast output has the wrong horizon or NaNs | Too-short series, too many lags, missing values, unsupported family/data support, or convergence trouble | Reduce lags/horizon, clean finite numeric data, choose a family matching data support, fit with the default method first, and run the section smoke helper. |
| Skew-t or long-memory models fit slowly or warn under MLE/MAP | More parameters and fragile likelihood geometry | Start with simpler Normal/t/GARCH models; use `BBVI` or `M-H` if skewness/heavy-tail posterior uncertainty is essential. |
| `EGARCHMReg.predict()` raises unpacking/shape errors | This release has a fragile out-of-sample regression-in-mean path | Validate with `predict_is()` first; if OOS forecasts are required, keep a tiny controlled fixture and treat failure as a package limitation. |
| `Aggregate.predict()` raises negative-dimension or data-mismatch errors | Too little warm-up history or incompatible model data tails | Increase `h_train`, reduce model lags/horizon, and ensure all aggregated models share the same last observations. |
| `AttributeError: module 'pyflux.families' has no attribute 'FLat'` while building `GPNARX(..., kernel=pf.ARD())` | PyFlux 0.4.17's ARD kernel references `families.FLat` instead of the public `Flat` class | Prefer `SquaredExponential`, `OrnsteinUhlenbeck`, `RationalQuadratic`, or `Periodic`; patch source only in an explicit repo-maintenance task. |
| User asks for `NNARX` | Source module exists but it is undocumented, not first-class exported, and failed smoke fitting in the inspected runtime | Route to `NNAR` for nonlinear autoregression or to `ARIMAX` for exogenous regressors; do not present `NNARX` as stable. |

## Environment check

Run the import checker from the skill root:

```bash
python scripts/check_pyflux_env.py --with-optional
```

Run a focused smoke check before deep debugging:

```bash
python scripts/smoke_pyflux_models.py --section univariate
python scripts/smoke_pyflux_models.py --section volatility
python scripts/smoke_pyflux_models.py --section gas
python scripts/smoke_pyflux_models.py --section state-space
python scripts/smoke_pyflux_models.py --section multivariate
```

## Data checklist

- Numeric arrays/DataFrames only; clean missing or infinite values before fitting.
- Use returns/log returns for volatility models, not raw price levels.
- Use nonnegative integer-like data for `Poisson()` and positive/nonnegative data for `Exponential()`.
- Keep forecast frames at least `h` rows long and include all formula columns.
- Keep synthetic smoke samples short; use longer real data only after the route is known to work.

## When to stop and report a package limitation

Stop instead of inventing a workaround when:

- the environment cannot import compiled PyFlux extensions even after a compatible install;
- a model path is undocumented/internal and has no verified synthetic smoke (`NNARX`);
- a forecast path is known fragile in this release (`EGARCHMReg.predict`) and the user specifically needs production-grade OOS forecasts;
- the task requires live external datasets or credentials that are unavailable.
