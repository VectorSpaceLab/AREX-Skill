---
name: volatility-models
description: "Fit and troubleshoot PyFlux GARCH, EGARCH, EGARCH-in-mean,
  long-memory, and skew-t volatility models for heteroskedastic time series."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Volatility Models

Use this sub-skill for conditional volatility work on return series: data prep, model choice, leverage, in-mean effects, forecasting, intervals, and post-fit checks.

## Route here

- Fit `GARCH`, `EGARCH`, `EGARCHM`, `LMEGARCH`, `SEGARCH`, `SEGARCHM`, or `EGARCHMReg`.
- Model volatility clustering, leverage, fat tails, skewness, or long memory in a univariate series.
- Use `add_leverage()` before fitting when the asymmetric news term is needed.
- Use `fit`, `predict`, `predict_is`, `plot_fit`, `plot_predict`, `plot_predict_is`, `plot_sample`, `plot_ppc`, `plot_z`, `sample`, and `ppc` on these volatility models.
- Validate with the bundled synthetic smoke section instead of the original Yahoo/FRED examples.

## Reroute

- ARIMA, ARIMAX, or NNAR mean-model work: `../univariate-models/SKILL.md`
- GAS / score-driven volatility work: `../gas-models/SKILL.md`
- VAR or GPNARX work: `../multivariate-models/SKILL.md`

## Start fast

1. Convert prices to returns or log returns; if you do not have market data, use a local synthetic return series.
2. Pick the family:
   - `GARCH` for plain conditional variance
   - `EGARCH` for t-based volatility
   - `EGARCHM` for EGARCH-in-mean
   - `LMEGARCH` for long-memory volatility
   - `SEGARCH` / `SEGARCHM` for skew-t volatility
   - `EGARCHMReg` for regression-in-mean with exogenous regressors
3. Call `add_leverage()` before `fit()` when you need leverage terms.
4. After fitting, check `summary()`, `plot_fit()`, `plot_z()`, and then `predict()` / `predict_is()`; use `sample()` and `ppc()` only after BBVI or M-H.
5. Run the bundled smoke helper with `--section volatility`: [smoke helper](../../scripts/smoke_pyflux_models.py).

## References

- [API reference](references/api-reference.md)
- [Workflows](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- Root [families and inference](../../references/families-and-inference.md) for priors, fit methods, result objects, and posterior diagnostics.
- Root [troubleshooting](../../references/troubleshooting.md) for install/build and legacy live-data failures shared across routes.
