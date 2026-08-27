---
name: sklearn-accel
description: "Zero-code-change acceleration for scikit-learn, UMAP, and HDBSCAN."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# sklearn-accel

Use this sub-skill when existing scikit-learn, UMAP, or HDBSCAN code should run through `cuml.accel` without rewriting the workflow to direct cuML APIs.

## Route here when
- you need CLI, notebook, environment-variable, or programmatic activation
- you need to confirm proxying, fallback, logging, or profiling
- you need to explain compatibility-driven CPU fallback or result differences

## Keep out
- direct cuML estimator rewrites and GPU-native tuning -> `../python-estimators/SKILL.md`
- Dask or multi-GPU workflow changes -> `../distributed-dask/SKILL.md`
- generic scikit-learn advice that is not tied to `cuml.accel`

## Core rules
- activate before importing `sklearn`, `umap`, or `hdbscan`
- use `python -m cuml.accel` for scripts, modules, or inline commands
- use `%load_ext cuml.accel` in notebooks before library imports
- use `CUML_ACCEL_ENABLED=1` only when you do not control the app entrypoint
- use `cuml.accel.install(disable_uvm=False, log_level=None)` for programmatic activation
- use `cuml.accel.enabled()`, `cuml.accel.is_proxy()`, and `cuml.accel.profile()` to check behavior
- rely on logs and profiler output to confirm GPU versus CPU execution; `is_proxy()` alone only proves proxy activation

## What belongs here
- CLI forwarding and profiling flags from `python -m cuml.accel`
- notebook and IPython activation, log-level, and profiler magics
- fallback compatibility by estimator family, input type, parameter, and dependency version
- expected numerical differences and when to compare metrics instead of fitted attributes

## References
- `references/compatibility-and-profiling.md`
- `references/troubleshooting.md`
- `scripts/cuml_accel_smoke.py`
