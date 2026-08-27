---
name: gas-models
description: "Use PyFlux GAS, GASX, GASReg, GASRank, and GAS local-level/trend
  models for score-driven forecasting and paired comparisons."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# PyFlux GAS models

Use this sub-skill when the task is a PyFlux score-driven model: univariate `GAS`, exogenous `GASX`, dynamic `GASReg`, score-driven local level/trend (`GASLLEV`, `GASLLT`), or dynamic paired-comparison `GASRank`.

## Route map

Use this sub-skill for:

- `pf.GAS(data, ar, sc, family, integ=0, target=None)` for univariate score-driven forecasting.
- `pf.GASX(data, formula, ar, sc, family, integ=0)` for GAS with exogenous regressors.
- `pf.GASReg(formula, data, family)` for score-driven dynamic regression coefficients.
- `pf.GASLLEV(data, family, integ=0, target=None)` and `pf.GASLLT(data, family, integ=0, target=None)` for score-driven local-level and local-linear-trend models.
- `pf.GASRank(data, team_1, team_2, family, score_diff, gradient_only=False)` for local paired-comparison/ranking data.

Route elsewhere:

- Kalman-style state-space wrappers that are not prefixed `GAS` go to `../state-space-models/`.
- GARCH/EGARCH conditional volatility goes to `../volatility-models/`.
- ARIMA/ARIMAX-style mean models go to `../univariate-models/`.
- Do not make live HTTP NFL CSV reads a runtime dependency; use the offline GASRank fixture pattern in the workflows reference.

## Default operating procedure

1. Classify the data: univariate time series, formula model with exogenous columns, local level/trend, or paired comparison.
2. Validate family/data compatibility: signed continuous series can use continuous families; count/intensity series must be nonnegative before using Poisson or Exponential-style families.
3. Fit first with a small deterministic/offline workflow and `MLE` unless a Bayesian posterior check is specifically needed.
4. Validate the fit by checking latent-variable values and forecast/prediction outputs for finite values, expected horizon length, and ordered interval columns when intervals are requested.
5. For GASRank, ensure every team and second-component name that will be predicted appears in the local training DataFrame.

## References and smoke check

- [API reference](references/api-reference.md)
- [Offline workflows](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- Root [families and inference](../../references/families-and-inference.md) for priors, fit methods, result objects, and posterior diagnostics.
- Root [troubleshooting](../../references/troubleshooting.md) for install/build and legacy live-data failures shared across routes.
- Smoke helper: [`../../scripts/smoke_pyflux_models.py --section gas`](../../scripts/smoke_pyflux_models.py)
