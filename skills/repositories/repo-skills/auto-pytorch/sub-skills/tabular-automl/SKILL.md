---
name: tabular-automl
description: "Guide Auto-PyTorch tabular classification and regression workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Tabular AutoML

Use this sub-skill for Auto-PyTorch tabular classification and regression. It covers the main public search workflow, single-configuration fitting, refitting, feature typing, portfolio selection, and result inspection.

## When to use

Choose this route when the user asks to:

- train or tune tabular classification or regression models
- handle categorical and numerical columns in pandas or NumPy data
- control resampling, budgets, or search-space restrictions
- force or inspect traditional learners
- inspect the final ensemble, run history, or performance over time
- fit one configuration instead of running a full search

## What this route owns

- `TabularClassificationTask`
- `TabularRegressionTask`
- `TabularClassificationPipeline`
- `TabularRegressionPipeline`
- `TraditionalTabularClassificationPipeline`
- `TraditionalTabularRegressionPipeline`
- `TabularInputValidator`
- `TabularFeatureValidator`
- `TabularTargetValidator`
- `get_dataset_requirements(...)`
- `get_configuration_space(...)`
- tabular search, fit, refit, predict, score, and inspection flows

## Main workflow

1. Decide whether the task is classification or regression.
2. Validate the inputs and, when needed, pass `feat_types` for ambiguous dtypes.
3. Build the task or pipeline object.
4. Choose the search style:
   - `search(...)` for end-to-end AutoML
   - `fit_pipeline(...)` for one configuration
   - `refit(...)` after search when you want to retrain on the full dataset
5. Inspect the outcome with `predict(...)`, `score(...)`, `show_models()`, and `sprint_statistics()`.

## Common decisions

### Data shape

- Accepts pandas DataFrames, NumPy arrays, and Python lists in the supported tabular formats.
- Categorical detection is easiest with DataFrames.
- If NumPy data encodes categories as integers, pass `feat_types` explicitly.

### Search control

- Use `include_components` to narrow the search to a known subset.
- Use `exclude_components` to rule out components you do not want.
- Use `search_space_updates` for targeted hyperparameter overrides.
- Use `portfolio_selection='greedy'` when you want the built-in warm-start portfolio.
- Keep `enable_traditional_pipeline=True` when you want the traditional learner baseline alongside neural pipelines.

### Resampling

- Default holdout validation is the common starting point.
- Cross-validation and stratified variants are available when you need more stable evaluation.
- `fit_pipeline(...)` accepts the same family of resampling controls.

### Traditional learners

The traditional path can use:

- LightGBM
- CatBoost
- Random Forest
- Extra Trees
- SVM
- KNN

These remain useful when you want a fast non-neural baseline or a smaller dataset path.

## What to read next

- `references/workflows.md` for end-to-end tabular recipes, including search, fit-pipeline, refit, and result inspection
- `references/api-reference.md` for the main class and method signatures
- `references/troubleshooting.md` for install/import, data-shape, and optional-dependency problems
- `scripts/tabular_smoke.py` for a tiny fixture check of tabular validation and search-space setup

## Do not use this route for

- time series forecasting
- image classification proof-of-concept paths
- repo-maintenance or CI workflows

Route forecasting questions to `sub-skills/forecasting/` instead.
