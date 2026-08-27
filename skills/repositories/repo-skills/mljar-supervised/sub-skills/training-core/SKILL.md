---
name: training-core
description: "Train, configure, evaluate, and use supervised.AutoML for tabular
  classification and regression."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training Core

Use this sub-skill when a task involves fitting, configuring, evaluating, or making predictions with `supervised.AutoML` for tabular binary classification, multiclass classification, or regression.

## Route here for

- Choosing `mode="Explain"`, `"Perform"`, `"Compete"`, or `"Optuna"` and making the choice safe for the user's time budget.
- Selecting algorithms, validation strategy, time limits, `eval_metric`, custom metrics, random state, CPU parallelism, ensembling, or stacking.
- Calling `fit()`, `predict()`, `predict_proba()`, `predict_all()`, `score()`, or `need_retrain()`.
- Diagnosing training and prediction errors caused by unfitted models, invalid task/mode/algorithm/metric settings, result-directory conflicts, custom CV mistakes, or too-small time limits.
- Creating a bounded synthetic smoke check with `scripts/mljar_automl_smoke.py` before using user data.

## Route elsewhere

- To `../data-preprocessing/` for input dtype cleanup, missing/categorical/text/datetime handling, target-shape decisions, and feature-engineering data choices.
- To `../artifacts-reports/` for saved `results_path` layout, leaderboard/report interpretation, structured reports, explainability artifacts, and save/load workflows.
- To `../fairness-workflows/` for `sensitive_features`, fairness metrics, thresholds, and privileged/underprivileged groups.
- To `../app-deployment/` for `app()`, `local_app()`, and `publish_app()` workflows.

## Operating checklist

1. Confirm the package imports as `supervised` and use `from supervised import AutoML`.
2. Identify the ML task: let `ml_task="auto"` infer from target values only when that inference is safe; otherwise set `binary_classification`, `multiclass_classification`, or `regression` explicitly.
3. Pick a mode and budget. Prefer `Explain` plus a short algorithm list for exploration, `Perform` for production-style tabular models, `Compete` only when extra search is justified, and `Optuna` only with an explicit per-algorithm `optuna_time_budget`.
4. Choose a clean `results_path`. It may be new or empty for training; an existing trained run with `params.json` is loaded instead of treated as scratch output.
5. Fit with `automl.fit(X, y, sample_weight=..., cv=...)` as needed. Use custom `cv` only with `validation_strategy={"validation_type": "custom"}`.
6. Use `predict()` for labels or regression values, `predict_proba()` only for classification probabilities, `predict_all()` for a DataFrame containing labels/probabilities or regression predictions, and `score(X, y)` for accuracy/R².
7. Use `need_retrain(X_new, y_new, decrease=...)` as a quick degradation signal, not as a substitute for full drift monitoring.

## Read next

- [API reference](references/api-reference.md) for signatures, accepted values, return shapes, and task-specific metric rules.
- [Workflows](references/workflows.md) for binary, multiclass, regression, custom validation, scoring, and retraining recipes.
- [Advanced configuration](references/advanced-configuration.md) for modes, time limits, ensembling/stacking, Optuna, custom metrics, and budget controls.
- [Troubleshooting](references/troubleshooting.md) for common training, prediction, configuration, and dependency failures.
- `scripts/mljar_automl_smoke.py` for a no-network synthetic helper that can run from any working directory.
- Root package assumptions: `../../references/package-overview.md`; cross-cutting install/import issues: `../../references/troubleshooting.md`.
