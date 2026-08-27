---
name: pyflux
description: "Use PyFlux 0.4.17 for time-series modeling, forecasting,
  probabilistic inference, ARIMA/GARCH/GAS/state-space/VAR/GPNARX workflows, and
  package-specific troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# PyFlux Repo Skill

Use this skill when a coding or research agent needs package-specific guidance for PyFlux time-series modeling, forecasting, probabilistic inference, diagnostics, or troubleshooting.

PyFlux 0.4.17 is a legacy probabilistic time-series library with a unified model lifecycle: build a model, inspect/adjust latent-variable priors, fit with a supported inference method, then forecast, backtest, sample, or run posterior predictive checks. Prefer a Python 3.7-era scientific stack for reliable use; newer Python/Numpy/Pandas combinations may fail during install or Cython extension import.

## Quick start

Install the package in a compatible environment, then run a safe import check:

```bash
pip install pyflux
python scripts/check_pyflux_env.py
```

Minimal model lifecycle:

```python
import numpy as np
import pyflux as pf

y = np.cumsum(np.random.normal(size=100))
model = pf.ARIMA(data=y, ar=2, ma=1, family=pf.Normal())
print(model.latent_variables)
result = model.fit("MLE")
result.summary()
forecast = model.predict(h=5, intervals=True)
```

## Route by task

- Use [`sub-skills/univariate-models/`](sub-skills/univariate-models/) for `ARIMA`, `ARIMAX`, and `NNAR` single-series forecasts, exogenous regressors, AR/MA/integration choices, ARIMAX formula handling, prediction intervals, posterior samples, and PPCs.
- Use [`sub-skills/volatility-models/`](sub-skills/volatility-models/) for `GARCH`, `EGARCH`, `EGARCHM`, `LMEGARCH`, `SEGARCH`, `SEGARCHM`, `EGARCHMReg`, leverage terms, in-mean volatility, and return-series volatility forecasting.
- Use [`sub-skills/gas-models/`](sub-skills/gas-models/) for `GAS`, `GASX`, `GASReg`, `GASLLEV`, `GASLLT`, and `GASRank` score-driven forecasting, local-level/trend models, and paired comparisons.
- Use [`sub-skills/state-space-models/`](sub-skills/state-space-models/) for `LLEV`, `LLT`, `NLLEV`, `NLLT`, `DAR`, `DynReg`, `NDynReg`, `DynamicGLM`, `LocalLevel`, and `LocalTrend` state-space or dynamic-regression workflows.
- Use [`sub-skills/multivariate-models/`](sub-skills/multivariate-models/) for `VAR`, `GPNARX`, Gaussian-process kernels, multivariate DataFrame layout, and VAR-vs-kernel routing.

## Shared references

- [`references/model-catalog.md`](references/model-catalog.md): package taxonomy, public classes, and which sub-skill owns each route.
- [`references/families-and-inference.md`](references/families-and-inference.md): cross-cutting families, priors, fit methods, result objects, prediction diagnostics, and `Aggregate` model-combination guidance.
- [`references/troubleshooting.md`](references/troubleshooting.md): install/build, legacy pandas/network examples, ARIMAX formula whitespace, inference, convergence, data-shape, and unsupported/internal-surface fixes.
- [`references/repo-provenance.md`](references/repo-provenance.md): source snapshot, evidence paths, and refresh baseline.

## Shared helpers

- [`scripts/check_pyflux_env.py`](scripts/check_pyflux_env.py): import/package/API check with no network access.
- [`scripts/smoke_pyflux_models.py`](scripts/smoke_pyflux_models.py): synthetic CPU smoke checks. Run `--section all` or one of `univariate`, `volatility`, `gas`, `state-space`, or `multivariate`.

Example:

```bash
python scripts/smoke_pyflux_models.py --section gas
```

## Common operating procedure

1. Confirm the environment with the import helper before debugging model code.
2. Pick the route from the task: mean model, volatility model, score-driven model, state-space model, or multivariate/kernel model.
3. Build a small local synthetic fixture first; do not depend on live Yahoo/FRED/NFL examples for validation.
4. Inspect `model.latent_variables`, then adjust priors only when the task needs Bayesian or regularized inference.
5. Start with the fastest default fit (`MLE` for most models, `OLS` for `VAR`, `BBVI` for `NNAR` and non-Gaussian state-space classes).
6. Validate with `summary()`, `predict_is()`, finite latent variables, and forecast horizon shape before using long horizons or Bayesian sampling.
7. Use `sample()`, `ppc()`, `plot_sample()`, and `plot_ppc()` only after `BBVI` or `M-H` fits.

## Safety and self-containment

This generated skill is self-contained. Runtime references and helper scripts live inside this skill directory and do not require opening the original repository checkout. Original tests and docs were used as evidence only; use the bundled routes, references, and synthetic helpers for future work.
