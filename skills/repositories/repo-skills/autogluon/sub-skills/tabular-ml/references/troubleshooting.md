# Tabular Troubleshooting

Use this reference for workflow-specific `autogluon.tabular` failures. For package installation, environment repair, CUDA/backend compatibility, and optional extras that affect multiple AutoGluon subpackages, route to the root `references/troubleshooting.md`.

## Quick Triage

1. Reproduce with a tiny CPU-safe run using `scripts/tabular_smoke.py`.
2. Confirm `label`, `problem_type`, `eval_metric`, `sample_weight`, `groups`, and data columns.
3. Reduce model families to `RF`/`XT` or another installed family.
4. Add optional model families back one at a time.
5. Inspect `leaderboard`, `fit_summary`, `predictor.info()`, and logs if a predictor was created.
6. For moved predictors, start with strict `TabularPredictor.load` checks and only relax flags after inspection.

## Missing Optional Model Packages

Symptoms:

- Fit logs say model family was skipped or failed to import.
- `CAT`, `XGB`, `GBM`, neural, foundation-model, or AutoMM-backed model keys fail while `RF`/`XT` works.
- `presets="best_quality"`, `"extreme_quality"`, `"interpretable"`, or `hyperparameters="multimodal"` fails in a minimal environment.

Actions:

```python
safe_hyperparameters = {
    "RF": {"n_estimators": 30, "ag_args": {"name_suffix": "Safe"}},
    "XT": {"n_estimators": 30, "ag_args": {"name_suffix": "Safe"}},
}
predictor.fit(train_data, hyperparameters=safe_hyperparameters, num_gpus=0, time_limit=60)
```

Then:

- Omit the missing model key from `hyperparameters` or add it to `excluded_model_types`.
- Verify optional packages with `scripts/inspect_tabular_predictor.py --show-optional`.
- Use root troubleshooting for installation extras and backend compatibility.
- Avoid `extreme_quality` unless tabular foundation-model extras and GPU expectations are satisfied.

## Wrong Label Or Problem Type

Symptoms:

- `label` not found.
- `predict_proba` raises because the task is regression or quantile.
- Binary classification is inferred as regression because labels are numeric continuous-looking values.
- Multiclass task drops rare classes or has too few examples per class.

Actions:

- Check `label in train_data.columns` before fit.
- Set `problem_type="binary"`, `"multiclass"`, `"regression"`, or `"quantile"` explicitly when inference is ambiguous.
- Use `positive_class` when F1/precision/recall should treat a specific binary label as positive.
- Use `predictor.can_predict_proba` before calling `predict_proba`.
- For multiclass class-frequency problems, inspect label counts and consider learner kwargs only if the user understands the tradeoff.

## Invalid Sample Weights

Symptoms:

- Fit or evaluate fails around sample weights.
- Weighted evaluation behaves unexpectedly.
- Metrics cannot be computed on evaluation data.

Actions:

- Ensure the weight column exists in training data when `sample_weight` is a column name.
- Ensure all weights are non-negative and non-missing.
- If `weight_evaluation=True`, include the weight column in test/evaluation data.
- Avoid naming a real column `"auto_weight"` or `"balance_weight"` if it is intended as a normal custom weight column.
- Prefer a metric aligned with weighting goals; do not blindly combine automatic class weights and weighted evaluation.

## Invalid Groups

Symptoms:

- Bagging fails with group split errors.
- Some folds lack required classes.
- `groups` appears ignored.

Actions:

- Confirm bagging is enabled with `num_bag_folds >= 2` or `auto_stack=True`.
- Ensure the groups column exists in training data.
- Inspect group counts and class counts per group.
- Avoid groups when each group is too small or class coverage differs sharply by group.
- Use explicit `tuning_data` without groups when the user only needs a validation set and not grouped bagging.

## Predictor Path Overwrite

Symptoms:

- A new fit overwrites or mixes with an old predictor.
- Loading returns unexpected models.
- Files disappear after `delete_models` or deployment cleanup.

Actions:

- Use a fresh `path` per independent fit.
- Do not store user files inside AutoGluon model directories; `delete_models(delete_from_disk=True)` can delete entire model subdirectories.
- Use `delete_models(..., dry_run=True)` before destructive cleanup.
- Call `predictor.save()` after mutating model-best, cleanup, or other persistent predictor state.

## Saved Predictor Version Or Python Mismatch

Symptoms:

- `TabularPredictor.load` raises an assertion about AutoGluon version or Python version.
- Loading succeeds but optional model packages are missing or predictions fail.
- A predictor moved across machines cannot infer.

Safe load sequence:

```python
from autogluon.tabular import TabularPredictor

predictor = TabularPredictor.load(path, check_packages=True)
```

If strict loading fails:

1. Confirm the predictor directory is trusted; loading uses pickle.
2. Inspect installed `autogluon.tabular`, Python version, and optional packages.
3. Retry with `check_packages=True` to get mismatch warnings.
4. Relax only one of `require_version_match=False` or `require_py_version_match=False` for controlled migration testing.
5. Validate predictions on known input rows and run a small `leaderboard` if labels are available.
6. Recreate the predictor in the target environment if compatibility is not trustworthy.

Never load untrusted predictor artifacts.

## Memory, Time, And Resource Limits

Symptoms:

- Fit skips large models.
- Training exceeds expected resources.
- Parallel fit crashes or Ray errors appear.
- Feature importance takes longer than training.

Actions:

- Set `time_limit`, `num_cpus`, `num_gpus=0`, and `memory_limit` explicitly.
- Prefer `fit_strategy="sequential"` for stability.
- Reduce model families with `included_model_types`, `excluded_model_types`, or explicit `hyperparameters`.
- Use `light`, `very_light`, `toy`, or `RF`/`XT` baselines for constrained runs.
- Disable text ngrams or use `ignore_text` for expensive text columns.
- For feature importance, lower `subsample_size`, `num_shuffle_sets`, or set `time_limit`.
- For online inference latency, use `infer_limit`, `refit_full`, `persist`, deployment presets, and Pareto leaderboard filtering.

## CUDA, GPU, And Foundation Model Extras

Symptoms:

- `extreme_quality`, tabular foundation-model keys, `AG_AUTOMM`, `FASTAI`, or `NN_TORCH` fails.
- Torch/CUDA errors occur despite tabular data.
- Model download/cache errors occur in no-network environments.

Actions:

- Use `num_gpus=0` and classical model families for CPU-only tasks.
- Avoid `extreme_quality` unless GPU and tabular foundation-model extras are confirmed.
- Route full multimodal text/image/foundation-model workflows to `../multimodal-automl/`.
- Use root troubleshooting for CUDA/Torch/package installation compatibility.
- Confirm whether pretrained model downloads are allowed before using foundation-model portfolios.

## HPO Or Ray Extras

Symptoms:

- `hyperparameter_tune_kwargs` or `fit_strategy="parallel"` fails.
- Ray import/runtime errors appear.
- HPO consumes the time budget without improving results.

Actions:

- Remove HPO and use fixed hyperparameters to establish a baseline.
- Use `hyperparameter_tune_kwargs={"num_trials": N, "scheduler": "local", "searcher": "random"}` for bounded local HPO.
- Prefer sequential fit unless the user explicitly needs parallel fit and Ray is verified.
- Reduce model families before HPO.
- Ensure search spaces are only used when HPO is enabled.

## Feature Metadata And Schema Drift

Symptoms:

- Prediction data has missing/renamed columns.
- Text or categorical inference changed after data export.
- Feature importance references unexpected features.
- A string ID is treated as text and creates huge ngram features.

Actions:

- Compare `train_data.columns` and inference `data.columns` after removing label, sample weight, and groups columns.
- Check `predictor.feature_metadata_in`.
- Use `predictor.transform_features(sample)` to inspect transformed columns.
- Use explicit `FeatureMetadata` for ambiguous raw/special types.
- Disable text features with `ignore_text` or feature-generator kwargs if needed.
- Rename user data to match training feature names; do not mutate the saved predictor to match changed names.

## Leaderboard Or Evaluation Errors

Symptoms:

- `leaderboard(data)` fails because label is missing.
- Extra metrics fail.
- Regression errors appear as negative scores.

Actions:

- Include the label column for `evaluate`, scored `leaderboard`, and `feature_importance`.
- Use `leaderboard(data_without_label, skip_score=True)` only when latency columns are needed and labels are absent.
- Pass `extra_metrics` only when labels are present.
- Remember score columns are higher-is-better; RMSE/log-loss style metrics are sign-flipped as scores.
- Use `score_format="error"` when users need lower-is-better error columns.

## Refit, Fit Extra, And Cleanup Failures

Symptoms:

- `refit_full`, `fit_extra`, or `fit_weighted_ensemble` fails after deployment cleanup.
- `_FULL` models have no validation score.
- Stacker refit cannot find cached data or out-of-fold predictions.

Actions:

- Keep `cache_data=True` and avoid `save_space` until post-fit expansion is finished.
- Validate `_FULL` models on held-out test data; do not rely on missing validation scores.
- Use `predictor.model_refit_map()` to map original models to refit-full names.
- Refit before `optimize_for_deployment` when deployment latency is the target.

## Decision Threshold Problems

Symptoms:

- F1, precision, recall, or balanced accuracy are poor despite good probabilities.
- Predictions look too biased toward one class.

Actions:

```python
threshold = predictor.calibrate_decision_threshold(metric="f1")
metrics = predictor.evaluate(test_data, decision_threshold=threshold)
predictions = predictor.predict(test_data, decision_threshold=threshold)
```

Use threshold calibration only for binary classification. Validate the chosen threshold on held-out data when possible.

## When To Refit From Scratch

Refit from scratch when:

- source training schema changed materially,
- AutoGluon/Python/package mismatch is not trusted,
- optional model families used by the predictor cannot be installed on the target machine,
- deployment cleanup removed artifacts needed for new training/introspection,
- the original predictor path was overwritten or corrupted, or
- schema drift cannot be fixed by deterministic user-side column/dtype normalization.
