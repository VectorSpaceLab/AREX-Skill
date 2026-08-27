---
name: univariate-models
description: "Use PyFlux ARIMA, ARIMAX, and NNAR models for univariate
  time-series forecasting, exogenous regressors, priors, prediction, and
  diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Univariate Models

Use this route when a user wants to:
- fit or compare `ARIMA`, `ARIMAX`, or `NNAR`
- forecast a single series with or without exogenous regressors
- choose AR / MA / integration orders
- run in-sample prediction, out-of-sample forecasting, prediction intervals, posterior samples, or PPCs
- work with continuous or count series through PyFlux families

## Route map

- **ARIMA** for a single observed series with no regressors.
- **ARIMAX** for a single series with known or forecastable exogenous regressors.
- **NNAR** for nonlinear autoregression with BBVI-only fitting.

## Exclusions

- Conditional volatility -> `../volatility-models/`
- GAS and GASRank -> `../gas-models/`
- State-space and dynamic regression -> `../state-space-models/`
- VAR and GPNARX -> `../multivariate-models/`
- `NNARX` is source-only/undocumented, not top-level exported, and not a first-class route here.

## Shared notes

- For the shared fit-method menu, latent-variable priors, result objects, and `Aggregate`, use the root [`families-and-inference`](../../references/families-and-inference.md) reference.
- Use `references/api-reference.md` for constructors and exact method signatures.
- Use `references/workflows.md` for offline synthetic examples and validation checks.
- Use `references/troubleshooting.md` for formula, forecast, Bayesian, and shape issues.

## Smoke helper

Run the bundled smoke helper for this route from this sub-skill or the root skill:

[`scripts/smoke_pyflux_models.py`](../../scripts/smoke_pyflux_models.py) `--section univariate`
