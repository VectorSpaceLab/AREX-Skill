# Data formats and validators

Use this reference to normalize feature and target data before fitting `autosklearn` estimators. It is self-contained for future operation; do not reopen source files for ordinary dtype/debug tasks.

## Validator model

`autosklearn` validates data inside estimator `fit()` via:

```python
from autosklearn.data.validation import InputValidator

validator = InputValidator(
    feat_type=None,
    is_classification=True,
    allow_string_features=True,
)
validator.fit(X_train, y_train, X_test=X_test, y_test=y_test)
X_checked, y_checked = validator.transform(X_train, y_train)
```

Key signatures:

- `InputValidator.__init__(feat_type=None, is_classification=False, logger_port=None, allow_string_features=True)`.
- `InputValidator.fit(X_train, y_train, X_test=None, y_test=None)`.
- `InputValidator.transform(X, y=None) -> (X_transformed, y_transformed_or_None)`.
- `FeatureValidator(feat_type=None, allow_string_features=True)` validates feature containers and inferred feature types.
- `TargetValidator(is_classification=False)` validates target containers and encodes classification targets.

`fit()` also checks:

- `len(X_train) == len(y_train)`.
- If `X_test` is not `None`, then `len(X_test) == len(y_test)`; provide both or neither.
- Train and test features have the same number of columns.
- Train and test targets have compatible dimensionality; pandas target train/test columns and dtypes must match.

## Supported containers

| Data role | Supported containers | Notes |
|---|---|---|
| Features `X` | `numpy.ndarray`, `pandas.DataFrame`, scipy sparse matrix, Python list | Sparse features are converted to CSR during transform if not already CSR. Lists are converted to a pandas DataFrame with inferred dtypes. |
| Targets `y` | `numpy.ndarray`, `pandas.Series`, `pandas.DataFrame`, scipy sparse matrix, Python list | Sparse targets must be numeric. Sparse targets are densified by the input-validation path when needed. |
| Test data | Same as train data | Type changes after fit produce warnings and may cause later estimator problems. Keep train/test schemas aligned. |

Unsupported feature containers include dicts and arbitrary objects. Unsupported target containers include dicts and arbitrary objects.

## Prefer pandas for mixed feature types

For heterogeneous datasets, use a pandas `DataFrame` and set each column dtype deliberately before `fit()`.

```python
import pandas as pd

X = pd.DataFrame({
    "age": [20, 40, 60],
    "plan": ["basic", "plus", "plus"],
    "is_member": [True, False, True],
    "review": ["short note", "long useful note", "none"],
    "event_time": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03"]),
})

X["age"] = pd.to_numeric(X["age"])
X["plan"] = X["plan"].astype("category")
X["is_member"] = X["is_member"].astype("bool")
X["review"] = X["review"].astype("string")
# Datetime is not supported directly. Convert first:
X["event_dayofweek"] = X["event_time"].dt.dayofweek.astype("int64")
X = X.drop(columns=["event_time"])
```

pandas feature-type inference:

| pandas column dtype | Inferred feature type | Behavior |
|---|---|---|
| Numeric dtype | `numerical` | Passed as numerical input to the preprocessing pipeline. |
| `category` | `categorical` | Treated as categorical and encoded by preprocessing. Use this for finite labels/codes. |
| `bool` | `categorical` | Treated as categorical. |
| pandas `string` | `string` if `allow_string_features=True`; otherwise `categorical` | String features are text-encoded when allowed. With `allow_string_features=False`, they are categorical and a warning is expected. |
| `object` | `string` if `allow_string_features=True`; otherwise `categorical` | A warning is emitted because object columns are ambiguous. Convert to `category`, `string`, or numeric explicitly. |
| datetime/timedelta | unsupported | Raises an error. Convert to numeric/calendar features before validation. |
| pandas sparse Series | unsupported | Raises an error. Convert to dense pandas/numpy or scipy sparse matrix. |
| all-NaN pandas column | cast to `category` during feature checks | Still consider whether the column carries usable signal. |

Important: never pass `feat_type` when `X` is a pandas `DataFrame`; the validator rejects this because pandas dtypes are the source of truth.

## NumPy arrays and Python lists

NumPy feature arrays must have numeric dtype. String/object NumPy arrays are rejected even if the strings represent categories.

```python
import numpy as np

X = np.array([
    [0.1, 1, 10.0],
    [0.4, 2, 12.5],
    [0.8, 1, 11.0],
], dtype=float)
feat_type = ["Numerical", "Categorical", "Numerical"]

automl.fit(X, y, feat_type=feat_type)
```

`feat_type` rules for non-pandas features:

- Pass a list with exactly one label per feature column.
- Valid labels are case-insensitive strings: `"Categorical"`, `"Numerical"`, `"String"`.
- If omitted, all NumPy columns are assumed numerical.
- Non-string labels raise an error.
- Wrong length raises an error.
- Unknown labels raise an error.
- For list input, the validator first converts to a pandas `DataFrame` with inferred dtypes; use the helper script to see what will be inferred.

If your source data is a NumPy array with categorical strings, convert to pandas and set `category`, or encode categories numerically and provide `feat_type`.

## `allow_string_features`

Estimator constructors expose `allow_string_features=True` by default.

```python
automl = autosklearn.classification.AutoSklearnClassifier(
    allow_string_features=False,
)
```

Behavior:

- `True`: pandas `string` and ambiguous `object` columns are treated as `string` features.
- `False`: pandas `string` and `object` columns are treated as categorical, with warnings.
- It does not make NumPy string/object arrays valid; NumPy features still must be numeric.

Use `allow_string_features=False` when object/string columns are really finite categories and text vectorization would be wrong. Prefer explicit `astype("category")` instead of relying on this flag.

## Target validation

Supported target types after scikit-learn `type_of_target` inspection:

- binary classification;
- multiclass classification;
- multilabel indicator classification;
- continuous regression;
- continuous multioutput regression.

Not supported:

- target values with missing/NaN values;
- legacy pandas Series that contains list-like multilabel rows;
- multiclass-multioutput classification target matrices;
- unknown target types from heterogeneous objects;
- train/test target matrices with different output dimensionality;
- pandas train/test target DataFrames with different columns or dtypes;
- sparse targets with non-numeric dtype.

Classification target behavior:

- Binary and multiclass targets are ordinal-encoded internally.
- If `y_test` is provided during `fit()`, its classes are included while fitting the encoder. This avoids transform failures when test data contains a class absent from `y_train`.
- Multilabel indicator targets are not encoded because encoding them would change the task semantics; use a multilabel indicator matrix directly.
- `TargetValidator.classes_` returns seen classes for single-output encoded classification, or an empty array if no encoder is used.

Regression target behavior:

- Regression targets are not encoded.
- Multioutput regression uses a 2D target with consistent number of outputs across train/test.

## `X_test` / `y_test` semantics

In estimator `fit()`, `X_train` and `y_train` drive model search/training. Optional `X_test` and `y_test` are used for evaluation and for producing test-score columns such as performance-over-time test metrics. They are also useful for target encoding in classification because they let the validator see test-only classes.

Rules:

```python
automl.fit(
    X_train,
    y_train,
    X_test=X_test,
    y_test=y_test,
    feat_type=feat_type_or_None,
    dataset_name="customer_churn",
)
```

- If `X_test` is supplied, supply `y_test` too.
- `X_test` must have the same number of feature columns as `X_train`.
- For pandas inputs, align column order, column names, and dtypes before fitting.
- `y_test` must match target dimensionality; pandas target columns and dtypes must match.
- Test data is not a replacement for `resampling_strategy`; AutoML still uses its own holdout/CV/custom split for optimization unless configured otherwise.

## No-training validation helper

Bundled script:

```bash
python scripts/validate_autosklearn_inputs.py --help
python scripts/validate_autosklearn_inputs.py
python scripts/validate_autosklearn_inputs.py --csv train.csv --target label --task classification
```

It reports:

- input shape and container choice;
- pandas dtypes or NumPy dtype;
- inferred auto-sklearn feature types;
- target `type_of_target` and NaN status;
- `feat_type` length/label checks;
- validator success/failure without starting AutoML training.

Use `--strict-object` to reject ambiguous pandas object columns instead of allowing the validator's default object-as-string warning. Use `--strict-datetime` to fail fast on datetime/timedelta columns. Use `--numpy-mode` to emulate NumPy fit input and catch string/object NumPy misuse.
