---
name: custom-models
description: "Help future Researcher sessions understand and extend Orbit
  custom-model internals."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# custom-models

Use this sub-skill when a task is about Orbit model internals rather than the public built-in model workflow.

## Trigger words
- build a custom Orbit model
- inspect the forecasting architecture
- choose between Stan MAP/MCMC and Pyro SVI
- troubleshoot a backend or template issue
- understand how a new model template plugs into Orbit

## In scope
- `ModelTemplate`
- forecaster architecture: `Forecaster`, `MAPForecaster`, `FullBayesianForecaster`, `SVIForecaster`
- estimator classes: `BaseEstimator`, `StanEstimator*`, `PyroEstimator*`
- Pyro model classes: `orbit.pyro.lgt.Model`, `orbit.pyro.ktr.Model`
- Stan loading / compilation helpers: `orbit.utils.stan.get_compiled_stan_model`
- cmdstan-path setup: `orbit.utils.set_cmdstan_path`
- built-in template families that reveal the wiring: `ETS`, `LGT`, `DLT`, `KTRLite`, `KTR`

## Out of scope
- backtesting walkthroughs
- general utility helpers unless they explain model wiring
- ordinary built-in-user model usage unless it exposes the architecture

## Core mental model
1. `ModelTemplate` defines the contract.
2. `Forecaster` validates data, builds training / prediction metadata, and calls an estimator.
3. The estimator routes to Stan or Pyro.
4. The backend returns posterior arrays and metrics.
5. The forecaster may expose extra public model helpers after fitting.

## Model contract checklist
A custom Orbit model usually needs:
- `_model_name`
- `_data_input_mapper`
- `_supported_estimator_types`
- optional `_fitter` for custom Pyro-style fitting
- `set_dynamic_attributes()`
- `set_init_values()` when Stan-style initialization is needed
- `get_model_param_names()` / `_set_model_param_names()`
- `predict()`

## Backend selection rules
- Stan path: `StanEstimatorMAP` or `StanEstimatorMCMC` with compiled `orbit/stan/{model_name}.stan`
- Pyro path: `PyroEstimatorSVI` with either a supplied `_fitter` or `orbit.pyro.{model_name}.Model`
- `Forecaster` rejects unsupported estimator/model pairs before fitting starts

## What to inspect first
1. `references/architecture.md`
2. `references/build-your-own-model.md`
3. `references/troubleshooting.md`
4. `scripts/inspect_custom_models.py`

## Handoff rule
If the task needs source-backed detail, keep the evidence in the bundled references and update the snapshot before handing off. Do not depend on reopening the source repo.
