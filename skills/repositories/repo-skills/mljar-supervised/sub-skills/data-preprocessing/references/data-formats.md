# Data formats and validation inputs

This reference covers data contracts for `supervised.AutoML` preprocessing. For training options after the data is ready, route to `../training-core/`.

## Public API shape

Primary training call:

```python
from supervised import AutoML

automl = AutoML(ml_task="auto", validation_strategy="auto")
automl.fit(X, y, sample_weight=None, cv=None)
```

`fit()` also accepts `sensitive_features`; route fairness-specific meaning and metrics to `../fairness-workflows/`.

Accepted practical inputs:

| Input | Preferred form | Notes |
| --- | --- | --- |
| `X` for `fit()`/`score()` | pandas `DataFrame` or 2D NumPy array | DataFrames preserve column names and dtypes. NumPy arrays are converted to a DataFrame with generated feature names. Empty inputs fail. |
| `X` for `predict()`, `predict_proba()`, `predict_all()` | pandas `DataFrame`, NumPy array, or list-like rows | Prediction data is converted to a DataFrame and checked against the trained feature count and stored training columns. |
| `y` | 1D pandas `Series` or 1D NumPy array | A one-column DataFrame is converted internally, but a clear 1D target is safer. Missing target rows are dropped. |
| `sample_weight` | 1D pandas `Series` or NumPy array | Keep length and row order aligned with `X` and `y`; rows removed for missing targets remove the matching weights too. |
| `cv` | iterable/list of `(train_idx, validation_idx)` arrays | Used only when `validation_strategy={"validation_type": "custom"}` is set in `AutoML(...)`. Indices must match the final row order after target-row filtering. |

## Column schema rules

- Pandas `DataFrame` column names are converted to strings. Non-string column names therefore work, but stable string names are easier to debug.
- NumPy inputs receive generated feature names like `feature_1`, `feature_2`, and so on. Prefer DataFrames if downstream reports, apps, or feature routing need meaningful names.
- At prediction time, the trained feature columns must be present. If a stored training column is missing, prediction raises a missing-column error.
- Prediction data is reordered to the stored training column order. Extra columns can be present, but they do not replace missing trained columns and should be removed for clarity.
- DataFrame indices are reset during input preparation. Do not rely on index labels to align `X`, `y`, weights, sensitive features, or split indices.

## Target and task inference

With `ml_task="auto"`, the task is inferred from the number of unique non-missing target values:

- exactly 2 unique values: `binary_classification`
- 3 through 20 unique values: `multiclass_classification`
- more than 20 unique values: `regression`

This inference is convenient but can surprise users:

- A small regression problem with only a few distinct target values can be inferred as classification. Use `AutoML(ml_task="regression")` when the target is continuous in meaning.
- A classification problem with more than 20 classes can be inferred as regression unless the task is forced.
- Binary labels do not need to be `0`/`1`. Strings, booleans, `-1`/`1`, and labels with special characters can be encoded internally and mapped back in predictions.
- Multiclass targets are encoded internally for learners and mapped back for public predictions. Use `predict_all()` to see probability columns with labels.

## Missing target rows

Feature missing values are imputed by preprocessing, but target missing values are different: rows with missing `y` are removed before training. The same removal is applied to `X`, `sample_weight`, and `sensitive_features` when present.

Before fitting, decide whether row removal is acceptable:

```python
mask = y.notna() if hasattr(y, "notna") else ~pd.isna(y)
X_clean = X.loc[mask].reset_index(drop=True)
y_clean = y.loc[mask].reset_index(drop=True)
```

You do not have to perform this manually for ordinary `fit()`, but doing it explicitly is safer when you also construct custom CV splits, holdout files, or external sample weights.

## Validation strategy design

`AutoML(validation_strategy="auto")` chooses defaults by mode:

- `Explain`: train/test split, typically 75%/25%.
- `Perform`: 5-fold cross-validation.
- `Compete` and `Optuna`: more intensive cross-validation defaults.
- Regression validation removes classification stratification settings.

For explicit validation:

```python
automl = AutoML(
    validation_strategy={
        "validation_type": "split",
        "train_ratio": 0.8,
        "shuffle": True,
        "stratify": True,
    }
)
```

or:

```python
automl = AutoML(validation_strategy={"validation_type": "kfold", "k_folds": 5})
```

For group-aware, time-aware, or leakage-controlled validation, use custom splits:

```python
automl = AutoML(validation_strategy={"validation_type": "custom"})
automl.fit(X_clean, y_clean, cv=[(train_idx, valid_idx)])
```

Custom split checklist:

1. Create splits after removing missing targets and resetting row positions.
2. Ensure every index is in range `[0, len(X_clean) - 1]`.
3. Ensure train and validation indices do not overlap within a fold.
4. Keep group/time leakage out of validation folds before passing them to AutoML.
5. Remember that some advanced training features can be disabled automatically or become less useful with custom validation; route exact training tradeoffs to `../training-core/`.

## Prediction data contract

For a fitted model, pass raw columns with the same meaning as training. Do not manually replay fitted encoders or scalers before prediction; the stored pipeline applies them.

Use this quick schema check before prediction:

```python
missing = [c for c in training_columns if c not in new_X.columns]
extra = [c for c in new_X.columns if c not in training_columns]
if missing:
    raise ValueError(f"Prediction data is missing trained columns: {missing}")
new_X = new_X[training_columns]
```

The fitted pipeline can handle new missing feature values and, depending on the learned encoder, unseen categorical values. It cannot infer a missing trained feature column.
