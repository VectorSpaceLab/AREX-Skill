# Data and Preprocessing Troubleshooting

Read this when a dataset, target, validation split, or preprocessing choice blocks an `mljar-supervised` `AutoML.fit()` or prediction workflow. For mode/algorithm/time-limit issues, route to `../training-core/references/troubleshooting.md`.

## `X`, `y`, sample weights, or sensitive features are misaligned

**Symptoms**

- `fit()` raises a length/shape/index error.
- Custom validation indices no longer refer to the intended rows.
- Fairness or sample-weight behavior appears shifted relative to labels.

**Likely causes**

- Rows were dropped from `X` or `y` after split construction.
- Missing targets were present; MLJAR excludes rows with missing targets during training.
- `sample_weight` or `sensitive_features` was built from the pre-filtered dataset.

**Recovery**

1. Create one final training table first.
2. Remove or account for missing target rows before building custom CV indices.
3. Slice `X`, `y`, `sample_weight`, and `sensitive_features` from the same final row order.
4. If using `cv`, pass it only with `validation_strategy={"validation_type": "custom"}` and verify every index is in range.

## Task inference surprises

**Symptoms**

- A small-cardinality numeric target is treated as binary or multiclass classification.
- A target expected to be classification is treated as regression.

**Recovery**

Set `ml_task` explicitly in `AutoML`: `binary_classification`, `multiclass_classification`, or `regression`. Do not rely on `ml_task="auto"` when the target cardinality is ambiguous or business semantics matter more than dtype.

## Missing target values

**Symptoms**

- Training uses fewer rows than expected.
- Custom split indices become invalid.

**Likely cause**

The preprocessing path excludes rows with missing targets.

**Recovery**

- Treat missing targets as an upstream data-quality issue for supervised learning.
- Drop or impute target rows before split generation if that matches the project contract.
- Regenerate `sample_weight`, `sensitive_features`, and custom validation splits after target cleanup.

## Missing feature values

**Symptoms**

- Missing values appear in raw `X` and users ask whether manual imputation is required.
- Model reports show preprocessing artifacts or feature transformations.

**Guidance**

MLJAR includes automatic missing-value preprocessing for ordinary numeric/categorical/text/datetime features. Manual imputation is only needed when the project has a required schema, audit, or domain-specific imputation rule.

**Recovery**

- For quick checks, leave ordinary missing features in `X` and use a fast bounded model.
- Use `scripts/inspect_preprocessing_behaviour.py` to inspect tiny missing-value fill behavior in the user's environment.
- If a production schema forbids missing values, validate the schema before calling `fit()` and document the transformation outside MLJAR.

## Categorical values or pandas categories behave unexpectedly

**Symptoms**

- New categories appear at prediction time.
- Integer-coded categories are treated as numeric.
- Special characters in category names or column names cause confusion in reports/artifacts.

**Recovery**

1. Prefer pandas `DataFrame` inputs with meaningful column names.
2. Convert integer-coded categories to string/category dtype when they are nominal, not ordinal/numeric.
3. Keep feature columns stable between training and prediction.
4. When new categories can appear, validate predictions with a representative sample before batch scoring.

## Text columns create too many features or slow runs

**Symptoms**

- Fitting becomes slow after including free-text columns.
- Reports contain many text-derived columns.

**Likely cause**

MLJAR can treat high-cardinality string columns as text and transform them into TF-IDF features.

**Recovery**

- Remove or pre-summarize text fields if they are not intended predictors.
- For smoke runs, select a smaller column subset or disable expensive feature engineering.
- If text is core to the task, increase the time budget and validate memory usage.

## Datetime columns are not interpreted as time features

**Symptoms**

- Datetime-looking strings remain categorical/text-like.
- Derived year/month/day features are absent.

**Recovery**

Convert date columns to pandas datetime dtype before `fit()`:

```python
X["event_time"] = pandas.to_datetime(X["event_time"], errors="coerce")
```

Then recheck missing timestamps and ensure train/predict data uses the same column names.

## Feature engineering flags add time, artifacts, or extra models

**Symptoms**

- Runs are slower than a small smoke should be.
- Extra files such as golden-feature metadata or additional models appear.

**Likely causes**

- `golden_features`, `features_selection`, `kmeans_features`, or `mix_encoding` is enabled by the selected mode or explicitly set.
- `Perform`, `Compete`, and `Optuna` modes enable more feature engineering than a minimal smoke.

**Recovery**

- For quick diagnostics, set `golden_features=False`, `features_selection=False`, `kmeans_features=False`, `mix_encoding=False`, `explain_level=0`, and a short algorithm list.
- For production or competition searches, leave the flags enabled deliberately and document the runtime/budget tradeoff.

## Prediction columns do not match training columns

**Symptoms**

- Prediction fails or produces suspicious output after adding/removing/renaming columns.

**Recovery**

- Persist the list of feature columns used for training.
- Before prediction, select and order the same columns in new data.
- Do not include the target column in prediction input.
- Route to `../artifacts-reports/` if a loaded model cannot find saved preprocessing/model files.
