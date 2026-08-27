---
name: data-preprocessing
description: "Prepare MLJAR-Supervised data, targets, preprocessing choices, and
  validation inputs safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data Preprocessing

Use this sub-skill when a task is about preparing data for `supervised.AutoML`, diagnosing automatic preprocessing, choosing feature-engineering flags, or designing validation inputs for tabular training and prediction.

## Route here for

- Valid `X`, `y`, `sample_weight`, and custom `cv` shapes for `AutoML.fit()` and prediction APIs.
- Missing feature values and missing target rows.
- Categorical, pandas `category`, string, text, and datetime columns.
- Target task inference and target label encoding for binary classification, multiclass classification, and regression.
- Preprocessing-related feature choices: golden features, feature selection, k-means features, and mixed categorical encoding.
- Validation-data design that keeps rows, weights, sensitive-feature rows, and custom split indices aligned.

## Route elsewhere

- To `../training-core/` for mode, algorithm, time-budget, metric, ensemble/stacking, `fit()`, `predict()`, `predict_proba()`, `predict_all()`, `score()`, or retraining decisions.
- To `../artifacts-reports/` for leaderboards, model folders, feature-importance interpretation, SHAP/explain outputs, persistence, `report()`, or `report_structured()`.
- To `../fairness-workflows/` for sensitive-feature semantics, fairness metrics, thresholds, privileged/underprivileged groups, or fairness report interpretation.
- To `../app-deployment/` for generated Mercury apps, local serving, or publishing.
- To root package references for install/import and optional dependency issues.

## Operating checklist

1. Prefer a pandas `DataFrame` for `X` when column names and dtypes matter. Use a one-dimensional pandas `Series` or NumPy array for `y` and keep `sample_weight` length aligned.
2. Remove leakage columns, identifiers that should not predict, and the target column from `X` before calling `fit()`.
3. Decide whether `ml_task="auto"` is safe. Force `ml_task` when a small-cardinality numeric regression target might be inferred as classification, or when many categorical classes might be inferred as regression.
4. Let MLJAR's stored preprocessing handle ordinary missing values, categoricals, text, datetime, and scaling unless the user has an external schema contract that requires manual preprocessing.
5. If using custom validation splits, create and validate `(train_idx, validation_idx)` arrays against the final row order that will reach `fit()`. Missing target rows are removed before training and can invalidate precomputed split indices.
6. Treat `golden_features`, `features_selection`, `kmeans_features`, and `mix_encoding` as feature-engineering choices that can add time, artifacts, and extra trained models. Disable them for fast smoke runs.
7. At prediction time, provide the same feature columns as training. Extra columns are not a substitute for missing trained columns.

## Read next

- [Data formats](references/data-formats.md) for `fit()`, prediction, targets, sample weights, custom CV, column schemas, and validation design.
- [Preprocessing guide](references/preprocessing-guide.md) for automatic missing/categorical/text/datetime/scaling/target transforms and feature-engineering flags.
- [Troubleshooting](references/troubleshooting.md) for common data, target, dtype, prediction-schema, and validation failures.
- [Preprocessing behaviour helper](scripts/inspect_preprocessing_behaviour.py) for safe tiny-fixture checks without a long AutoML training run.
- Root package assumptions: `../../references/package-overview.md`; cross-cutting install/import issues: `../../references/troubleshooting.md`.
