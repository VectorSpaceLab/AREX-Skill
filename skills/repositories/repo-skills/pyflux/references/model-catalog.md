# PyFlux Model Catalog

## Purpose

Use this reference to identify the PyFlux class family and the generated sub-skill that owns the workflow. For fit-method and prior details, read `families-and-inference.md`; for symptom-driven fixes, read `troubleshooting.md`.

## Model routes

| Task shape | Primary classes | Owning route |
| --- | --- | --- |
| Single-series AR/MA forecasting | `ARIMA` | `sub-skills/univariate-models/` |
| Single-series forecasting with known exogenous regressors | `ARIMAX` | `sub-skills/univariate-models/` |
| Neural nonlinear autoregression | `NNAR` | `sub-skills/univariate-models/` |
| Conditional volatility and returns | `GARCH`, `EGARCH`, `EGARCHM`, `LMEGARCH`, `SEGARCH`, `SEGARCHM` | `sub-skills/volatility-models/` |
| Volatility regression-in-mean | `EGARCHMReg` | `sub-skills/volatility-models/` |
| Score-driven univariate forecasting | `GAS` | `sub-skills/gas-models/` |
| Score-driven exogenous/regression workflows | `GASX`, `GASReg` | `sub-skills/gas-models/` |
| Score-driven local level/trend | `GASLLEV`, `GASLLT` | `sub-skills/gas-models/` |
| Dynamic paired comparison/ranking | `GASRank` | `sub-skills/gas-models/` |
| Gaussian local level/trend | `LLEV`, `LLT`, `LocalLevel`, `LocalTrend` with `Normal()` | `sub-skills/state-space-models/` |
| Non-Gaussian local level/trend | `NLLEV`, `NLLT`, `LocalLevel`, `LocalTrend` with non-`Normal()` family | `sub-skills/state-space-models/` |
| Dynamic regression and dynamic GLM | `DynReg`, `NDynReg`, `DynamicGLM` | `sub-skills/state-space-models/` |
| Dynamic autoregression | `DAR` | `sub-skills/state-space-models/` |
| Vector autoregression | `VAR` | `sub-skills/multivariate-models/` |
| Gaussian-process nonlinear autoregression | `GPNARX` plus kernels | `sub-skills/multivariate-models/` |

## Distribution families

Public distribution/prior classes used across model families:

- Continuous: `Normal`, `t`, `Skewt`, `Laplace`, `Cauchy`.
- Count or positive-support: `Poisson`, `Exponential`.
- Priors/support helpers: `Flat`, `TruncatedNormal`, `InverseGamma`, `InverseWishart`.

Use the family object in the model constructor when the model supports non-Normal observations, for example `family=pf.Poisson()` for count data. Do not force signed data into positive-support families.

## Kernel classes

`GPNARX` expects a kernel instance, not a string:

- `SquaredExponential()` for smooth nonlinear dynamics.
- `OrnsteinUhlenbeck()` for rougher exponential-decay correlation.
- `ARD()` when lag dimensions may have separate relevance; in PyFlux 0.4.17 this path is known fragile because `ARD.build_latent_variables()` refers to a non-existent `families.FLat`, so prefer another kernel unless the source has been patched.
- `RationalQuadratic()` for mixed length-scale behavior.
- `Periodic()` for repeating/seasonal structure.

## Cross-cutting utilities

- `Aggregate` combines forecasts from compatible fitted PyFlux models through online exponential weighting. It is a support workflow, not a replacement for model selection; see `families-and-inference.md`.
- `acf` and `acf_plot` are lightweight autocorrelation utilities useful before choosing AR/MA or volatility lags.
- `TablePrinter` is output formatting infrastructure, usually not a direct user workflow.
- Low-level recursion, Kalman, covariance, and Cython extension functions are implementation details unless the user is explicitly debugging PyFlux internals.

## Surfaces intentionally not routed

- `NNARX` exists as a source module but is not a first-class route here. It is undocumented, not top-level exported, lacks native test coverage, and the inspected runtime hit `ValueError: ndarray is not C-contiguous` during a synthetic fit.
- Live financial/NFL examples from old documentation are evidence only. Use local fixtures and bundled smoke helpers for repeatable operation.
