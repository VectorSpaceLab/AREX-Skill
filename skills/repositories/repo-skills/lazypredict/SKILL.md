---
name: lazypredict
description: "Use Lazy Predict for low-code model benchmarking, supervised
  classification and regression sweeps, time-series forecasting comparisons, CLI
  CSV runs, optional tuning, explainability, MLflow, Spark, and dependency
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Lazy Predict Repo Skill

Use this skill when a task asks how to install, use, debug, or validate the
`lazypredict` Python package. Lazy Predict runs many baseline machine-learning
models with little code and returns ranked pandas DataFrames for comparing
model families before deeper modeling work.

## First checks

1. Confirm the package is installed in the user's Python environment:

   ```python
   import lazypredict
   print(lazypredict.__version__)
   ```

2. For a broader local diagnostic, run the bundled checker:

   ```bash
   python scripts/check_lazypredict_env.py --json
   ```

3. Install only the extras needed for the requested workflow. Start with:

   ```bash
   pip install lazypredict
   ```

   Then add optional extras such as `boost`, `timeseries`, `tune`, `explain`,
   `viz`, `spark`, or `mlflow` only when the task needs them. Read
   [references/install-and-troubleshooting.md](references/install-and-troubleshooting.md)
   before installing broad extras or GPU/Spark/foundation dependencies.

## Route by task

- Read [supervised-benchmarking](sub-skills/supervised-benchmarking/SKILL.md)
  for `LazyClassifier` and `LazyRegressor`: sklearn-style classification or
  regression sweeps, categorical columns, custom metrics, result DataFrames,
  model selection, progress callbacks, persistence, and fitted-pipeline access.
- Read [time-series-forecasting](sub-skills/time-series-forecasting/SKILL.md)
  for `LazyForecaster`: univariate or exogenous series, seasonal period
  detection, lag/rolling features, forecasting metrics, horizon strategies,
  ensembles, diagnostics, plotting, and optional statistical/deep/foundation
  forecasters.
- Read [advanced-workflows](sub-skills/advanced-workflows/SKILL.md) for optional
  tuning, search spaces, permutation/SHAP explainability, FLAML/Optuna choices,
  and advanced smoke checks that should not be mixed into a first quick start.
- Read [cli-and-integrations](sub-skills/cli-and-integrations/SKILL.md) for the
  `lazypredict` CSV CLI, MLflow tracking, Dask/PySpark conversion, Spark MLlib
  classes, GPU/Intel optional acceleration checks, and integration failures.

## Common decision points

- Prefer explicit model subsets, `max_models`, and `timeout` when the user needs
  a fast answer. Running every available estimator can be slow or noisy.
- Treat `ignore_warnings=True` as a benchmarking convenience, not as proof that
  every model succeeded. Inspect `.errors` when important models are missing.
- Use `predictions=True` only when downstream work needs per-model predictions;
  otherwise the second returned DataFrame is normally empty.
- GPU support is optional. `use_gpu=True` requests supported backends but many
  paths fall back to CPU unless CUDA-capable packages and hardware are present.
- The CSV CLI supports supervised classification/regression only. Use the Python
  API for time-series forecasting, tuning, explainability, or custom pipelines.

## Provenance and refresh

Read [references/repo-provenance.md](references/repo-provenance.md) before
checking whether this skill is current for a different Lazy Predict checkout.
If the package version, public entry points, or major workflow files changed,
refresh the skill before relying on detailed API claims.
