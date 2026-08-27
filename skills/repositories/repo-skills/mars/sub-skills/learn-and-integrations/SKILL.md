---
name: learn-and-integrations
description: "Routes Mars Learn estimator, Dask-on-Mars, and optional ML
  framework integration requests to the bundled API and dependency guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Learn and Integrations

Use this sub-skill for Mars Learn estimators and optional integration packages.
The core route is scikit-learn-style API usage on Mars tensors/DataFrames; the
optional route is Dask, PyTorch, TensorFlow, XGBoost, LightGBM, Statsmodels,
Joblib, or Proxima integration.

## Trigger phrases

- "Use Mars Learn like scikit-learn."
- "Run `KMeans`, `PCA`, or `NearestNeighbors` on Mars data."
- "Use Dask on top of Mars."
- "Run a PyTorch or TensorFlow script through Mars."
- "Use XGBoost, LightGBM, Statsmodels, Joblib, or Proxima with Mars."

## What belongs here

- Core Mars Learn estimators and utilities.
- Dataset generation and preprocessing helpers.
- Optional integration import and dependency guidance.
- Tiny CPU estimator smoke checks.

## What stays elsewhere

- Tensor/DataFrame fundamentals -> `tensor-dataframe-core`.
- Remote callable DAGs not tied to Learn -> `remote-and-scripts`.
- Ray, GPU, Kubernetes, YARN, or service CLI startup -> `deployment-and-backends`.

## Read these bundled files

- `references/api-reference.md` for bundled estimator and integration entry
  points.
- `references/workflows.md` for the core CPU estimator path and optional
  integration routing.
- `references/troubleshooting.md` for missing optional dependencies, shape
  errors, and script-runner failures.
- `scripts/check_mars_learn.py` for a tiny Mars Learn CPU smoke.

## Minimal route

1. Start from local tensor data with `mars.tensor as mt`.
2. Import the estimator, for example `from mars.learn.decomposition import PCA`.
3. Fit or transform tiny data; many `fit` / `predict` style methods trigger
   execution internally.
4. If the user asks for an optional integration, identify the exact dependency
   first and do not install broad extras by default.

## Common decisions

- Use Mars Learn core estimators for base package guidance.
- Treat TensorFlow, PyTorch, XGBoost, LightGBM, and Statsmodels as optional
  integrations, not required baseline dependencies.
- For Dask-on-Mars, ensure real `dask` is installed; a placeholder object means
  the optional integration is unavailable.
- For distributed deep-learning scripts, route runtime/back-end prerequisites to
  `deployment-and-backends` when GPUs, Ray, or clusters are involved.

## Quality bar

A future agent should be able to distinguish a core Mars Learn estimator task
from an optional integration task, run a tiny CPU estimator smoke, and explain
what external package or backend is missing when an integration cannot import.
