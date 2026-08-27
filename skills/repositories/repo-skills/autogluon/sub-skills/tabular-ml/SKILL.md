---
name: tabular-ml
description: "Build, evaluate, customize, troubleshoot, and deploy AutoGluon
  TabularPredictor workflows for supervised tabular machine learning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AutoGluon Tabular ML

Use this sub-skill for supervised tabular classification, regression, and quantile prediction with `autogluon.tabular.TabularPredictor` and `TabularDataset`.

## Route Here When

- The task asks for `TabularPredictor`, `TabularDataset`, leaderboard, feature importance, model management, save/load, or refit workflows.
- The data is a pandas-like table with one target column and rows as samples.
- The user needs presets, hyperparameters, bagging/stacking, HPO, resource limits, sample weights, groups, or feature metadata for tabular data.
- The user wants model families such as LightGBM, CatBoost, XGBoost, RandomForest, ExtraTrees, KNN, linear, neural network, or optional tabular foundation models inside tabular AutoML.

## Route Elsewhere

- Forecasting with item ids, timestamps, horizons, covariates, or `TimeSeriesPredictor`: use `../time-series-forecasting/`.
- Foundation-model workflows for text, image, document, object detection, semantic matching, or `MultiModalPredictor`: use `../multimodal-automl/`.
- Cross-package install/import/backend diagnostics that affect all AutoGluon packages: use the root `references/troubleshooting.md`.

## Start With These References

- `references/api-reference.md`: constructor and method signatures, metrics, model management, save/load, and deployment-facing APIs.
- `references/workflows.md`: novice-to-expert fit/evaluate/predict workflows, quantile prediction, HPO, bagging, stacking, refit, distillation, and deployment cleanup.
- `references/data-and-features.md`: `TabularDataset`, schema expectations, feature metadata, automated feature generators, text columns, sample weights, and groups.
- `references/customization.md`: presets, hyperparameter dictionaries, custom metrics, custom models, resource controls, and optional model families.
- `references/troubleshooting.md`: actionable fixes for optional dependencies, schema drift, problem type errors, resource limits, HPO/Ray, save/load mismatch, and predictor path issues.

## Bundled Scripts

- `scripts/tabular_smoke.py`: trains a tiny in-memory `TabularPredictor`, evaluates it, predicts from a reloaded predictor, and prints a JSON summary.
- `scripts/inspect_tabular_predictor.py`: read-only environment/predictor inspection for versions, importability, optional packages, and saved predictor metadata checks.

Run each script with `--help` first. The smoke script avoids network access and writes only to a temporary directory unless `--output-dir` is supplied.

## Fast Patterns

```python
from autogluon.tabular import TabularPredictor

predictor = TabularPredictor(label="target", eval_metric="accuracy").fit(
    train_data,
    presets="medium_quality",
    time_limit=60,
    hyperparameters={"GBM": {}, "RF": {"n_estimators": 50}},
    num_cpus="auto",
    num_gpus=0,
)
leaderboard = predictor.leaderboard(test_data, extra_info=True)
predictions = predictor.predict(test_data.drop(columns=["target"]))
```

Use an explicit `path` when the predictor must be preserved. Use a new empty path for every independent training run to avoid overwriting prior results.

## Safety And Quality Defaults

- Prefer `presets="medium_quality"` or a small explicit `hyperparameters` dictionary for smoke tests and CPU-constrained repros.
- Prefer `presets="good_quality"` or `"high_quality"` with a real `time_limit` for production candidates; reserve `"best_quality"` and `"extreme_quality"` for larger budgets.
- For deployment, combine quality presets with `"optimize_for_deployment"` or call `delete_models(dry_run=True)` before destructive cleanup.
- For moved saved predictors, load only trusted predictor directories and start with strict version checks before relaxing `require_version_match` or `require_py_version_match`.
