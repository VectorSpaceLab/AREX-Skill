---
name: pmdarima
description: "Guide Python time-series forecasting with pmdarima, including
  ARIMA and AutoARIMA modeling, preprocessing, temporal validation, diagnostics,
  datasets, and trusted model refresh workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# pmdarima operating skill

Use this skill when a task names `pmdarima`, `auto_arima`, `ARIMA`, seasonal
forecasting, differencing, Fourier features, rolling forecast validation, or a
pmdarima model artifact. It is a CPU-oriented scientific-Python package skill;
there is no CUDA, ROCm, MPS, or vendor backend route to enable.

## Start here

1. Confirm the target series, observation frequency, forecast horizon, missing-
   value policy, and whether future exogenous regressors are available.
2. Read [API overview](references/api-overview.md) for the public surface and
   route the request to the smallest focused sub-skill below.
3. Use the focused route's API reference and workflow recipe before writing
   code. Keep order bounds, seasonal period, data shapes, and scoring choices
   explicit so results are reproducible.
4. Run [the environment checker](scripts/check_environment.py) when import,
   compiled-extension, dependency, or version questions are part of the task.
5. Read [troubleshooting](references/troubleshooting.md) when installation,
   dynamic version metadata, optional plotting, convergence, data validation,
   or artifact compatibility is unclear.

## Focused routes

- **[forecasting](sub-skills/forecasting/SKILL.md)** — fixed `ARIMA`, bounded
  `auto_arima`/`AutoARIMA`, seasonal `(P,D,Q,m)` models, exogenous `X`, fitted
  values, residuals, intervals, and primary forecasts.
- **[preprocessing](sub-skills/preprocessing/SKILL.md)** — Box-Cox/log target
  transforms, Fourier and date features, future feature contracts, and ordered
  `Pipeline` stages.
- **[model-selection](sub-skills/model-selection/SKILL.md)** — temporal
  train/test splits, rolling/sliding forecast CV, scoring, `smape`, and leakage-
  safe comparison with aligned `X`.
- **[datasets-diagnostics](sub-skills/datasets-diagnostics/SKILL.md)** — built-
  in datasets, `ndiffs`/`nsdiffs`/`diff`, decomposition, ACF/PACF, and
  headless numeric diagnostics.
- **[persistence-update](sub-skills/persistence-update/SKILL.md)** — trusted
  pickle round trips, pipeline artifacts, `ARIMA.update`, version warnings,
  provenance, and refit-versus-refresh decisions.

## Cross-route decisions

- Establish frequency and a defensible seasonal cycle before calling
  `auto_arima`; `m` is observations per cycle, not the forecast horizon.
- Fit transforms and feature generators only on training data. Use a complete
  `Pipeline` for transform, estimator, prediction, and inverse-transform order.
- Use chronological splits rather than shuffled validation. Keep future `X`
  rows aligned with every forecast horizon and every fold.
- Treat `auto_arima` as a bounded search. Record `seasonal`, `m`, order limits,
  `stepwise`, `maxiter`, `error_action`, and warnings in experiment notes.
- Never deserialize an untrusted pickle. A pmdarima version warning is a
  compatibility signal, not a migration or security guarantee.

## Installation and smoke check

Install the public distribution with `python -m pip install pmdarima`. For a
checkout or source build, Python 3.10+ and a working C/Cython build path may be
needed; prefer a compatible wheel. Verify with:

```bash
python -c "import pmdarima as pm; print(pm.__version__)"
python /path/to/this/skill/scripts/check_environment.py
```

The bundled checker performs no network access, model download, plotting, or
artifact loading. It confirms imports, dependency versions, a tiny ARIMA fit,
a dataset loader, a temporal split, and a metric. Read
[repository provenance](references/repo-provenance.md) before refreshing this
skill against a different checkout or release.

## Scope boundary

This skill teaches use of the public package, not repository maintenance,
benchmark reproduction, release automation, CI configuration, or source-code
editing. Native examples and tests were distilled into the bundled references
and safe helpers; runtime instructions do not require the original checkout.
