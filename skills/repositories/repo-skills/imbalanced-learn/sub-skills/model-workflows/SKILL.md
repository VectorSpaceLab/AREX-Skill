---
name: model-workflows
description: "Router for imbalanced-learn pipelines, leakage-safe resampling,
  balanced ensembles, and instance-hardness cross-validation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# model-workflows

Use this sub-skill when the request is about building a model workflow around
imbalanced-learn samplers.

This sub-skill owns the package surfaces that combine resampling with model
training and validation:

- `Pipeline` and `make_pipeline`
- `BalancedBaggingClassifier`
- `BalancedRandomForestClassifier`
- `EasyEnsembleClassifier`
- `RUSBoostClassifier`
- `InstanceHardnessCV`

## What to do first

1. Decide whether the user wants a pipeline, an ensemble, or a specialized
   cross-validation splitter.
2. Split the data first and keep resampling on the training side.
3. Check whether the final estimator supports `fit`, `predict`, and optionally
   `predict_proba` if the workflow uses `InstanceHardnessCV`.
4. If the workflow chains transforms and samplers, remember that imbalanced-learn
   pipeline semantics differ from plain scikit-learn in `fit_transform`.
5. Verify the assembled workflow on a tiny synthetic dataset before scaling up.

## Typical routing cues

- `fit_resample` inside `Pipeline`
- leakage-safe cross-validation
- `BalancedBaggingClassifier`, `BalancedRandomForestClassifier`
- `EasyEnsembleClassifier`, `RUSBoostClassifier`
- `InstanceHardnessCV`
- `transform_input`, `memory`, `sample_weight`

## When to read the bundled references

- `references/workflows.md` for safe pipeline patterns and decision points.
- `references/api-reference.md` for the compact workflow API catalog.
- `references/troubleshooting.md` when cross-validation, metadata routing, or
  estimator compatibility fails.

## Common choices

- Use `Pipeline` or `make_pipeline` when the main goal is to avoid leakage and
  let resampling happen only during fit.
- Use `BalancedBaggingClassifier` when a bagging-style ensemble should resample
  each bootstrap subset.
- Use `BalancedRandomForestClassifier` when the user wants a random-forest-like
  ensemble with balanced bootstrap samples.
- Use `EasyEnsembleClassifier` when the task wants an AdaBoost-based ensemble on
  balanced subsets.
- Use `RUSBoostClassifier` when the task wants boosting with under-sampling
  between iterations.
- Use `InstanceHardnessCV` when the task is binary classification and the user
  wants hard samples distributed across folds.

## Native evidence to keep in mind

These repo tests are the most relevant later verification anchors for this
sub-skill:

- `imblearn/tests/test_pipeline.py::test_make_pipeline`
- `imblearn/tests/test_pipeline.py::test_pipeline_methods_pca_svm`
- `imblearn/ensemble/tests/test_bagging.py::test_balanced_bagging_classifier`
- `imblearn/ensemble/tests/test_forest.py::test_balanced_random_forest`
- `imblearn/ensemble/tests/test_easy_ensemble.py::test_easy_ensemble_classifier`
- `imblearn/ensemble/tests/test_weight_boosting.py::test_rusboost`
- `imblearn/model_selection/tests/test_split.py::test_default_params`

## Package-specific cautions

- `Pipeline.fit_transform(X, y)` can resample, while `fit(X, y)` followed by
  `transform(X)` does not. Do not assume scikit-learn equivalence.
- `InstanceHardnessCV` only supports binary classification and needs an
  estimator with `predict_proba`.
- Some ensembles accept `sampler`/`sampling_strategy`/`replacement` parameters
  that change the internal balancing behavior; inspect the exact constructor.
- `sample_weight` support depends on the specific estimator.

## Use the scripts

- `scripts/pipeline_leakage_check.py` for a tiny leakage-safe pipeline smoke.
- `scripts/ensemble_smoke.py` for a representative balanced-ensemble check.
- `scripts/model_selection_smoke.py` for an `InstanceHardnessCV` sanity check.
