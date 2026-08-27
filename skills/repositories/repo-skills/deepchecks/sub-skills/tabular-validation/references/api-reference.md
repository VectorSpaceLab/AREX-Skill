# Tabular API Reference

This reference distills the tabular APIs verified from Deepchecks package source, usage guides, examples, tests, and installed-package signature inspection. It is intended for future agents operating without the source checkout.

## Imports

```python
from deepchecks.tabular import Dataset, Suite
from deepchecks.tabular import checks
from deepchecks.tabular.suites import (
    data_integrity,
    train_test_validation,
    model_evaluation,
    full_suite,
)
```

## `Dataset` constructor

Verified signature:

```python
Dataset(
    df,
    label=None,
    features=None,
    cat_features=None,
    index_name=None,
    set_index_from_dataframe_index=False,
    datetime_name=None,
    set_datetime_from_dataframe_index=False,
    convert_datetime=True,
    datetime_args=None,
    max_categorical_ratio=0.01,
    max_categories=None,
    label_type=None,
    dataset_name=None,
    label_classes=None,
)
```

Key arguments:

| Argument | Use | Practical notes |
|---|---|---|
| `df` | Non-empty object castable to a pandas `DataFrame`. | Column names must be unique. Deepchecks copies the data. |
| `label` | Target column name, `Series`, single-column `DataFrame`, or numpy row/column vector. | If `Series`/array is supplied it is appended as a new column; length and index must match `df`. |
| `features` | Explicit model feature columns. | If omitted, every non-label, non-index, non-datetime column is treated as a feature. |
| `cat_features` | Categorical feature columns. | Prefer explicit list. Use `[]` to disable inference. If omitted, Deepchecks infers categorical columns using dtype/category-count heuristics. |
| `index_name` | Meaningful unique identifier column, or index level when `set_index_from_dataframe_index=True`. | The index column cannot also be a feature. For a DataFrame index, set `set_index_from_dataframe_index=True`. |
| `datetime_name` | Time column, or index level when `set_datetime_from_dataframe_index=True`. | The datetime column cannot also be a feature. `convert_datetime=True` applies `pandas.to_datetime` with `datetime_args`. |
| `label_type` | Task hint: `'binary'`, `'multiclass'`, or `'regression'`. | Useful when labels or predictions make task inference ambiguous. |
| `dataset_name` | Display name for results. | String or `None`; commonly `'Train'`, `'Test'`, or a domain-specific name. |
| `max_categorical_ratio`, `max_categories` | Tune categorical inference. | Avoid relying on inference when train/test cardinalities differ. |
| `label_classes` | Deprecated compatibility argument. | Prefer `model_classes` on `run(...)` for classification probabilities. |

Useful properties and methods:

| API | Purpose |
|---|---|
| `Dataset.from_numpy(features_array, labels_array=None, columns=None, label_name=None, **kwargs)` | Build from 2D feature array and optional 1D labels. |
| `dataset.train_test_split(train_size=None, test_size=0.25, random_state=42, shuffle=True, stratify=False)` | Split while preserving Dataset metadata. `stratify=True` uses the label column. |
| `dataset.copy(new_df)` | Reuse metadata for a new DataFrame with compatible columns. |
| `dataset.sample(n_samples=None, replace=False, random_state=None)` | Return a sampled Dataset. |
| `dataset.drop_na_labels()` | Return a Dataset excluding missing labels. |
| `dataset.data` | Internal DataFrame. |
| `dataset.features`, `dataset.features_columns` | Feature names and feature-only DataFrame. |
| `dataset.cat_features`, `dataset.numerical_features` | Categorical and numerical feature lists. |
| `dataset.label_name`, `dataset.label_col`, `dataset.has_label()` | Label metadata and values. |
| `dataset.index_name`, `dataset.index_col` | Configured index metadata and values. |
| `dataset.datetime_name`, `dataset.datetime_col` | Configured datetime metadata and values. |
| `dataset.columns_info` | Role/type map for every column. |

## Suite factories

Verified signatures:

```python
data_integrity(
    columns=None, ignore_columns=None, n_top_columns=None,
    n_samples=None, random_state=42, n_to_show=5, **kwargs
)

train_test_validation(
    columns=None, ignore_columns=None, n_top_columns=None,
    n_samples=None, random_state=42, n_to_show=5, **kwargs
)

model_evaluation(
    alternative_scorers=None,
    columns=None, ignore_columns=None, n_top_columns=None,
    n_samples=None, random_state=42, n_to_show=5, **kwargs
)

full_suite(**kwargs)
```

Factory arguments are propagated to included check constructors. Prefer `scorers=...` over the deprecated `alternative_scorers` name when customizing performance checks.

| Factory | Requires | Typical included checks |
|---|---|---|
| `data_integrity` | One Dataset; label helps checks such as conflicting labels and label correlation. | Single value, special characters, mixed nulls/types, string mismatch, data duplicates, string length outliers, conflicting labels, outlier samples, feature-label correlation, feature-feature correlation, identifier-label correlation. |
| `train_test_validation` | Train and test Datasets with shared features/categorical features/label/index/date metadata. | Dataset size, new labels/categories, string mismatch comparison, date/index leakage, sample mixing, feature-label correlation change, feature drift, label drift, multivariate drift. |
| `model_evaluation` | Train Dataset plus test Dataset for most checks, and a fitted model or precomputed predictions for model-dependent checks. | Train-test performance, ROC, confusion matrix, prediction drift, simple model comparison, weak segments, calibration, regression error distribution, unused features, boosting overfit, model inference time. |
| `full_suite` | Depends on included checks; it flattens model evaluation, train-test validation, and data integrity checks. | Broad first-pass validation; expect unsupported check failures if data/model inputs are intentionally partial. |

## `Suite.run(...)`

Tabular suite run signature:

```python
result = suite.run(
    train_dataset=None,
    test_dataset=None,
    model=None,
    feature_importance=None,
    feature_importance_force_permutation=False,
    feature_importance_timeout=120,
    with_display=True,
    y_pred_train=None,
    y_pred_test=None,
    y_proba_train=None,
    y_proba_test=None,
    run_single_dataset=None,
    model_classes=None,
)
```

Guidance:

- Use `train_dataset=ds` for single-dataset suites/checks, including data integrity.
- Provide both `train_dataset` and `test_dataset` for split validation and comparative model evaluation.
- Provide `model=` for fitted sklearn-style estimators; use precomputed prediction arrays when a model object is unavailable or expensive.
- Set `with_display=False` in scripts, CI, or agent automation to avoid heavy plotting/widget serialization during validation.
- `run_single_dataset='Train'` or `'Test'` restricts single-dataset checks inside a suite when both datasets are present.
- `model_classes` must be sorted in the same order as probability columns for classification; use it whenever probability order is not trivially inferred.

## Individual checks

Import practical check classes from the aggregate module:

```python
from deepchecks.tabular.checks import DataDuplicates, FeatureDrift, TrainTestPerformance
```

Run signatures by check family:

```python
# Single dataset checks
result = check.run(
    dataset,
    model=None,
    feature_importance=None,
    with_display=True,
    y_pred=None,
    y_proba=None,
    model_classes=None,
)

# Train/test checks
result = check.run(
    train_dataset,
    test_dataset,
    model=None,
    feature_importance=None,
    with_display=True,
    y_pred_train=None,
    y_pred_test=None,
    y_proba_train=None,
    y_proba_test=None,
    model_classes=None,
)

# Model-only checks
result = check.run(model, with_display=True)
```

Practical categories:

| Category | Useful checks |
|---|---|
| Data integrity | `ColumnsInfo`, `MixedNulls`, `StringMismatch`, `MixedDataTypes`, `IsSingleValue`, `SpecialCharacters`, `StringLengthOutOfBounds`, `DataDuplicates`, `ConflictingLabels`, `ClassImbalance`, `OutlierSampleDetection`, `FeatureLabelCorrelation`, `FeatureFeatureCorrelation`, `IdentifierLabelCorrelation`, `PercentOfNulls`. |
| Train/test validation | `DatasetsSizeComparison`, `NewCategoryTrainTest`, `NewLabelTrainTest`, `StringMismatchComparison`, `DateTrainTestLeakageDuplicates`, `DateTrainTestLeakageOverlap`, `IndexTrainTestLeakage`, `TrainTestSamplesMix`, `FeatureLabelCorrelationChange`, `FeatureDrift`, `LabelDrift`, `MultivariateDrift`, `TrainTestFeatureDrift`, `TrainTestLabelDrift`, `WholeDatasetDrift`. |
| Model evaluation | `TrainTestPerformance`, `SingleDatasetPerformance`, `RocReport`, `ConfusionMatrixReport`, `PredictionDrift`, `TrainTestPredictionDrift`, `SimpleModelComparison`, `WeakSegmentsPerformance`, `SegmentPerformance`, `CalibrationScore`, `RegressionErrorDistribution`, `RegressionSystematicError`, `UnusedFeatures`, `BoostingOverfit`, `ModelInferenceTime`, `ModelInfo`, `MultiModelPerformanceReport`. |

## Conditions and result inspection

Every check can carry conditions:

```python
check = DataDuplicates().add_condition_ratio_less_or_equal(max_ratio=0.01)
result = check.run(dataset, with_display=False)
ratio = result.value
condition_passed = result.passed_conditions()
```

Useful methods:

| API | Use |
|---|---|
| `check.add_condition(name, condition_func, **params)` | Add custom condition evaluated on `result.value`. The function returns `bool` or a Deepchecks condition result. |
| `check.add_condition_*` | Built-in condition helper methods implemented by many checks. |
| `check.remove_condition(index)` | Remove one condition by printed index. |
| `check.clean_conditions()` | Remove all conditions from a check. |
| `suite[index]` | Access a check by suite index after printing/inspecting the suite. |
| `suite.add(check_or_suite)` / `suite.remove(index)` | Customize suites. |
| `result.value` | Check-specific payload; inspect before writing custom conditions. |
| `result.passed_conditions()` | Whether conditions passed for a check result. |
| `suite_result.passed(fail_if_warning=True, fail_if_check_not_run=False)` | Overall condition status. |
| `suite_result.get_not_ran_checks()` | Checks skipped or failed due to unsupported inputs/exceptions. |

Route persistence, HTML, JSON, and CI gates to [results-and-integrations](../../results-and-integrations/SKILL.md).

## Models, predictions, probabilities, and feature importance

### Fitted model objects

A model should follow sklearn conventions:

- `predict(X)` receives a pandas DataFrame/array of shape `(n_samples, n_features)` and returns shape `(n_samples,)`.
- `predict_proba(X)` is optional but needed for classification checks/metrics that use class probabilities, such as ROC/AUC and calibration.
- Classifier objects should expose classes in the same order as probability columns, or the caller should pass sorted `model_classes` to `run(...)`.
- Tree/linear models can expose `feature_importances_` or `coef_`; Deepchecks may use these for display prioritization and checks such as `UnusedFeatures`.

### Precomputed predictions

Use precomputed predictions when the model is remote, unavailable, slow, or impossible to serialize locally:

```python
result = model_evaluation().run(
    train_dataset=train_ds,
    test_dataset=test_ds,
    y_pred_train=y_pred_train,
    y_pred_test=y_pred_test,
    y_proba_train=y_proba_train,
    y_proba_test=y_proba_test,
    model_classes=[0, 1],
    feature_importance=feature_importance,
    with_display=False,
)
```

Required shapes:

- `y_pred_*`: array-like `(n_samples,)`; one-column `(n_samples, 1)` is flattened.
- `y_proba_*`: array-like `(n_samples, n_classes)` for classification.
- Probability columns must follow `model_classes` order. For binary classification, the greater alphanumeric class is treated as the positive class by default.
- Provide predictions for every Dataset supplied to the suite/check. A train/test check with only `y_pred_train` is incomplete.

### Feature importance

Pass feature importance to avoid slow permutation calculations or to support prediction-only workflows:

```python
feature_importance = pd.Series(
    [0.55, 0.30, 0.15],
    index=train_ds.features,
)
```

Validation rules:

- Must be a pandas `Series`.
- Index must exactly match Dataset feature names.
- Values must be non-null and non-negative.
- Sum should be near `1.0`; Deepchecks normalizes non-unit sums with a warning.
- Set `feature_importance_timeout=0` to skip permutation importance when no explicit importance is available and speed matters.

### Scorers

Performance checks accept scorer lists or dictionaries through `scorers=`:

```python
from sklearn.metrics import make_scorer, fbeta_score

scorers = {
    "F0.5": make_scorer(fbeta_score, beta=0.5, average="binary"),
    "Accuracy": "accuracy",
}
result = model_evaluation(scorers=scorers).run(train_ds, test_ds, model, with_display=False)
```

Scorer rules:

- Built-in strings include common sklearn names plus Deepchecks aliases such as `accuracy`, `precision`, `precision_macro`, `precision_per_class`, `recall`, `f1`, `roc_auc`, `neg_rmse`, `neg_mae`, and `r2`.
- Custom tabular metrics should follow sklearn scorer API: callable `(model, X, y_true) -> score` with greater-is-better semantics.
- Lower-is-better names like `mae`, `mse`, and `rmse` may warn; prefer negative variants for pass/fail comparisons.
- Check JSON serialization supports built-in scorer strings more reliably than arbitrary Python callables; route serialization decisions to [results-and-integrations](../../results-and-integrations/SKILL.md).
