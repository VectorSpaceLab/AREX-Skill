---
name: advanced-workflows
description: "Use Lazy Predict optional advanced workflows for tuning, search
  spaces, explainability, feature importance, SHAP, Optuna, FLAML, visualization
  pointers, and safe advanced dependency checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Advanced Workflows

Use this sub-skill when the task goes beyond a first Lazy Predict leaderboard:
hyperparameter tuning, search-space inspection, permutation or SHAP
explainability, FLAML/Optuna decisions, optional visualization dependencies, or
advanced smoke checks.

## Start here

1. Run a small core benchmark first with the supervised or time-series
   sub-skill. Advanced APIs usually need fitted models or score tables.
2. Check optional dependencies before promising SHAP, Optuna, FLAML,
   InterpretML, or plotting.
3. Keep trials, top-k counts, and timeouts bounded. Advanced workflows can be
   much more expensive than the initial Lazy Predict sweep.
4. Run the bundled advanced smoke helper for a quick environment check:

   ```bash
   python scripts/smoke_advanced.py --json
   ```

## What to read

- [references/advanced-workflows.md](references/advanced-workflows.md) covers
  supervised and time-series tuning, search-space registries, permutation/SHAP
  explainability, and dependency choices.
- [references/troubleshooting.md](references/troubleshooting.md) covers missing
  optional packages, invalid tuning parameters, slow or empty tuning runs, SHAP
  compatibility, and unfitted model errors.

## Common routes

- For `LazyClassifier(..., tune=True)` or `LazyRegressor(..., tune=True)`, read
  the supervised tuning section and then return to
  [supervised-benchmarking](../supervised-benchmarking/SKILL.md) for the base
  fit contract.
- For `LazyForecaster(..., tune=True)`, read the time-series tuning section and
  then return to [time-series-forecasting](../time-series-forecasting/SKILL.md)
  for forecasting data and metrics.
- For feature importance after supervised fitting, prefer permutation
  importance as the base dependency path; use SHAP only when the `shap` extra is
  installed and the fitted model family is compatible.
- For MLflow, Dask/PySpark, Spark, CLI, or GPU environment checks, use
  [cli-and-integrations](../cli-and-integrations/SKILL.md).

## Do not use this sub-skill for

- A first quick model comparison without tuning or explanation.
- Repository maintenance, release automation, or documentation publishing.
- Full production AutoML orchestration outside Lazy Predict's exposed APIs.
