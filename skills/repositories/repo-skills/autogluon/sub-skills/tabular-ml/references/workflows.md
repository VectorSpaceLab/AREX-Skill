# Tabular Workflows

Use these workflows to answer practical `TabularPredictor` requests without reopening the source repository.

## Minimal Classification Or Regression

```python
from autogluon.tabular import TabularPredictor

label = "target"
predictor = TabularPredictor(label=label, path="ag-tabular-model").fit(
    train_data,
    presets="medium_quality",
    time_limit=120,
    num_gpus=0,
)
metrics = predictor.evaluate(test_data)
leaderboard = predictor.leaderboard(test_data, extra_info=True)
predictions = predictor.predict(test_data.drop(columns=[label]))
```

Checklist:

1. Confirm `label` exists in training and evaluation data.
2. Hold out a real test set; do not treat `tuning_data` as unbiased final evaluation.
3. Use `leaderboard(test_data)` to compare validation and test behavior.
4. If the user asks for probabilities, call `predict_proba` only when `predictor.can_predict_proba` is true.
5. Persist the predictor path if the model must be reused.

## CPU-Safe Tiny Reproduction

Use this for debugging a user issue, CI smoke checks, or constrained environments:

```python
hyperparameters = {
    "RF": {"n_estimators": 20, "ag_args": {"name_suffix": "Tiny"}},
    "XT": {"n_estimators": 20, "ag_args": {"name_suffix": "Tiny"}},
}
predictor = TabularPredictor(label="label", problem_type="binary", verbosity=0).fit(
    train_data,
    hyperparameters=hyperparameters,
    time_limit=30,
    num_cpus=1,
    num_gpus=0,
    fit_weighted_ensemble=False,
)
```

This avoids optional LightGBM/CatBoost/XGBoost/PyTorch model dependencies while still exercising AutoGluon tabular training, prediction, evaluation, save, and load.

## Mixed Numeric, Categorical, And Text Columns

AutoGluon’s default tabular feature generator handles numeric, categorical, datetime, and text-derived features. For mixed data:

```python
predictor = TabularPredictor(label="churn", eval_metric="f1", positive_class="yes").fit(
    train_data,
    presets=["medium_quality", "ignore_text"],  # remove ignore_text if text should be used
    time_limit=300,
    num_gpus=0,
)
```

Decision points:

- Keep text features when short free-text columns are predictive and text processing is affordable.
- Add `presets="ignore_text"` or disable text ngrams via feature generator kwargs when text columns are identifiers, noisy notes, or too expensive.
- For image/document-specific workflows, route to `../multimodal-automl/` instead of forcing tabular text/image handling.
- Use `FeatureMetadata` when automatic type inference treats an ID-like string as text or a categorical code as numeric.

## Custom Metric And Threshold-Sensitive Binary Tasks

```python
predictor = TabularPredictor(
    label="converted",
    problem_type="binary",
    eval_metric="balanced_accuracy",
    positive_class=1,
).fit(train_data, time_limit=300, calibrate_decision_threshold="auto")

threshold = predictor.calibrate_decision_threshold(metric="balanced_accuracy")
predictions = predictor.predict(test_data, decision_threshold=threshold)
metrics = predictor.evaluate(test_data, decision_threshold=threshold)
```

Use threshold calibration for metrics such as F1 and balanced accuracy. Warn users that optimizing one threshold-sensitive metric can hurt another metric such as accuracy or log loss.

## Quantile Prediction

Quantile prediction estimates conditional quantiles of a numeric label.

```python
quantile_levels = [0.1, 0.5, 0.9]
predictor = TabularPredictor(
    label="demand",
    problem_type="quantile",
    eval_metric="pinball_loss",
    quantile_levels=quantile_levels,
).fit(
    train_data,
    hyperparameters={"GBM": {}, "RF": {"n_estimators": 100}},
    time_limit=600,
)
quantile_predictions = predictor.predict(test_data)
```

Notes:

- Quantile output is a table-like prediction with one column per quantile level.
- Use numeric labels only.
- `predict_proba` is not valid for quantile problems.
- Bagging and calibration-style workflows can improve interval quality but increase runtime.
- Validate interval coverage on a held-out set by comparing observed labels against lower and upper quantile columns.

## Preset Selection

- `medium_quality`: default-style quick prototype; fast, no automatic stacking.
- `good_quality`: better accuracy and fast inference; uses lighter model portfolio, refit-full, and deployment-friendly choices.
- `high_quality`: higher accuracy with refit-full and reduced bag-fold storage; larger runtime than `good_quality`.
- `best_quality`: strongest standard tabular ensemble path; expect larger model counts, runtime, disk, and memory.
- `extreme_quality`: high-resource tabular foundation-model path; requires optional tabular foundation model extras and is GPU-oriented.
- `optimize_for_deployment`: keep only the best needed artifacts and save space; pair after a quality preset when deployment is the main goal.
- `interpretable`: fit interpretable rule-based models; requires the relevant optional dependencies.
- `ignore_text`: disable automatic text-derived features in tabular feature generation.

Avoid mixing multiple quality presets unless there is a deliberate override strategy. If using a list, put broad quality first and utility presets later, such as `presets=["good_quality", "optimize_for_deployment"]`.

## Hyperparameter Dictionaries

Use a dictionary to include, exclude, or customize model families:

```python
hyperparameters = {
    "GBM": [
        {},
        {"extra_trees": True, "ag_args": {"name_suffix": "XT"}},
    ],
    "CAT": {},
    "XGB": {},
    "RF": {"n_estimators": 200},
}
predictor.fit(train_data, hyperparameters=hyperparameters, time_limit=900)
```

Rules:

- Missing model-family keys are not trained.
- A list under a model key trains multiple variants.
- Search spaces require `hyperparameter_tune_kwargs`; fixed values do not.
- Add `ag_args` for model naming, priority, problem-type constraints, HPO behavior, and stack/base validity.
- Add `ag_args_fit` for per-model resources, maximum rows/features/classes, and per-model time/memory constraints.
- Add `ag_args_ensemble` for stack-ensemble behavior such as original-feature usage and fold settings.

## Bagging, Stacking, And Dynamic Stacking

Accuracy-oriented pattern:

```python
predictor = TabularPredictor(label="target").fit(
    train_data,
    presets="best_quality",
    time_limit=3600,
    auto_stack=True,
    dynamic_stacking="auto",
)
```

Manual pattern:

```python
predictor.fit(
    train_data,
    num_bag_folds=5,
    num_bag_sets=1,
    num_stack_levels=1,
    dynamic_stacking=True,
    time_limit=1800,
)
```

Guidance:

- `num_bag_folds=1` is invalid; use `0` to disable bagging or `>=2` to enable it.
- Stacking requires bagging; otherwise AutoGluon raises or disables stacking depending on settings.
- `dynamic_stacking=True` can spend part of the time budget checking for stacked overfitting.
- `groups` only matters when bagging is enabled.
- Bagging and stacking can multiply training and inference cost; use `refit_full` or deployment presets when latency matters.

## HPO And Parallel Fit

```python
predictor.fit(
    train_data,
    hyperparameters={"GBM": {}, "CAT": {}, "XGB": {}},
    hyperparameter_tune_kwargs={
        "num_trials": 10,
        "scheduler": "local",
        "searcher": "auto",
    },
    time_limit=1800,
    fit_strategy="sequential",
)
```

Use HPO when the user has enough time budget and asks for tuning. Avoid it for small smoke tests. If `fit_strategy="parallel"`, Ray is required, the feature is experimental, and memory pressure is more likely. Prefer sequential fit when reproducibility and readable logs matter.

## Resource-Constrained Training

- Set `num_gpus=0` to prevent GPU use.
- Set `num_cpus` for shared machines or CI.
- Set `memory_limit` in GB when running under cgroups, job schedulers, or constrained containers.
- Reduce model families with `included_model_types`, `excluded_model_types`, or a small `hyperparameters` dictionary.
- Use `infer_limit` and `infer_limit_batch_size` to force latency-aware model selection.
- Use `presets="ignore_text"` when text ngram features make fitting or inference too expensive.
- Use `hyperparameters="light"`, `"very_light"`, or a custom dictionary for low-latency/low-disk tasks.

## Leaderboard-Driven Model Selection

```python
leaderboard = predictor.leaderboard(
    test_data,
    extra_info=True,
    extra_metrics=["accuracy", "roc_auc", "log_loss"],
    only_pareto_frontier=True,
)
```

Use `only_pareto_frontier=True` when choosing an accuracy/latency tradeoff. Use `score_format="error"` when users reason in lower-is-better errors. Use `skip_score=True` only when labels are unavailable and latency columns are still useful.

## Feature Importance And Schema Diagnostics

```python
importance = predictor.feature_importance(
    test_data,
    feature_stage="original",
    subsample_size=1000,
    num_shuffle_sets=5,
)
transformed = predictor.transform_features(test_data.drop(columns=[label]))
```

Use held-out data for feature importance. Do not use training data unless the user explicitly accepts biased importances. For schema drift, compare:

- training columns excluding label/sample weight/groups,
- inference columns supplied to `predict`,
- `predictor.feature_metadata_in`, and
- `predictor.transform_features(new_data).columns`.

## Save, Move, And Load A Predictor

```python
predictor.save()
loaded = TabularPredictor.load("ag-tabular-model", check_packages=True)
```

Safe moved-predictor procedure:

1. Load only trusted predictor directories.
2. Try strict defaults: `require_version_match=True`, `require_py_version_match=True`.
3. If loading fails, inspect AutoGluon/Python/package versions and optional model packages.
4. Retry with `check_packages=True` to log mismatches.
5. Relax version flags only for a controlled migration test, then validate predictions and leaderboard behavior on a known holdout sample.

## Deployment Cleanup

Best-practice compact predictor:

```python
predictor = TabularPredictor(label=label, path="ag-deploy").fit(
    train_data,
    presets=["good_quality", "optimize_for_deployment"],
    time_limit=1800,
)
```

Manual cleanup:

```python
predictor.delete_models(models_to_keep="best", dry_run=True)
predictor.delete_models(models_to_keep="best", dry_run=False)
predictor.save_space()
predictor.save()
```

Warn users that cleanup can remove unused models, cached train/validation data, out-of-fold predictions, and artifacts required by `leaderboard(extra_info=True)`, `fit_summary`, `fit_extra`, refit, or feature importance without supplied data.

## Distillation Notes

`predictor.distill` can train smaller student models from a trained teacher predictor. Treat distillation as an advanced post-fit workflow: keep a validation/test set, compare leaderboard before/after, and avoid it when a simple `refit_full` or `optimize_for_deployment` is enough. Distillation can use unlabeled data and can change model-management assumptions, so inspect resulting model names before deployment.

## Troubleshooting Workflow For Optional Model Dependency Missing

1. Re-run with a CPU-safe model dictionary such as `RF`/`XT` only to prove the tabular pipeline works.
2. Inspect which model key failed in logs or `predictor.info()["model_info"]` / failure summaries.
3. Route install/backend details to the root troubleshooting reference if the fix involves package extras.
4. Use `excluded_model_types=["CAT"]` or omit a model key to unblock training while the optional package is unavailable.
5. Re-enable the model after package installation and verify with a small time-limited fit.

## Usability Case: Mixed Features, Custom Metric, Tight Time Limit

When a user has mixed numeric/categorical/text columns, asks for a custom metric, uses a short time limit, and misses optional model packages:

- Use `eval_metric` or an AutoGluon scorer if the metric is supported.
- Start with `presets="medium_quality"`, `num_gpus=0`, and `hyperparameters={"RF": {}, "XT": {}}` to establish a baseline.
- Add `ignore_text` if text feature generation dominates runtime.
- Add optional `GBM`, `CAT`, or `XGB` only after checking packages.
- Evaluate with `leaderboard(test_data, extra_metrics=[...])` on a true holdout set.

## Usability Case: Saved Predictor Moved Across Machines

When load fails after moving a predictor:

- Do not disable all checks immediately.
- Verify the predictor directory is trusted and complete.
- Inspect installed `autogluon.tabular`, Python, and optional package versions.
- Try `TabularPredictor.load(path, check_packages=True)`.
- If strict version mismatch blocks a controlled migration, retry with one relaxed flag at a time and validate predictions on known input rows.
- If optional model packages are missing, either install matching extras or select a different available model only if the predictor contains one that can infer.
