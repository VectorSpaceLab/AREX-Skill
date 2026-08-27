# Supervised Data and Results

## Inputs

Lazy Predict supervised estimators expect an already split supervised learning
dataset:

```python
scores, predictions = clf.fit(X_train, X_test, y_train, y_test)
```

Validation checks catch common mistakes:

- Empty `X_train` or `X_test` raises `ValueError`.
- Mismatched sample counts between `X_*` and `y_*` raise `ValueError`.
- Mismatched feature counts between train and test arrays/DataFrames raise
  `ValueError`.
- PySpark and Dask inputs may be auto-converted by the package-level distributed
  helper; read the integrations sub-skill before collecting large distributed
  data to one driver process.

## Pandas, NumPy, booleans, and categoricals

NumPy arrays are converted to DataFrames internally. Pandas DataFrames preserve
column names and let Lazy Predict build a preprocessing `ColumnTransformer`.
The tests cover boolean-only and mixed boolean/numeric DataFrames.

Categorical encoding is controlled by `categorical_encoder`:

| Value | When to use | Dependency note |
|---|---|---|
| `"onehot"` | Low-cardinality nominal columns; safest default. | Base dependencies. |
| `"ordinal"` | Ordered or high-cardinality categories where integer codes are acceptable. | Base dependencies. |
| `"target"` | Target encoding for supervised categorical signal. | Requires `category_encoders`. |
| `"binary"` | Binary encoding for high-cardinality categories. | Requires `category_encoders`. |

If `category_encoders` is missing and the workflow requires target or binary
encoding, install the optional dependency explicitly or switch to `onehot` or
`ordinal` for the current run.

## Metrics and sorting

Classification result tables are sorted by `Balanced Accuracy`. Regression
result tables are sorted by `R-Squared` descending. Each row is one fitted model
that did not fail or time out.

Custom metrics must be callables with the shape:

```python
def my_metric(y_true, y_pred):
    return float(...)
```

If the custom metric raises for a model and `ignore_warnings=True`, Lazy Predict
stores `None` for that metric and continues.

## Cross-validation

Set `cv` to an integer `>= 2` to add cross-validation metric columns. Use
`n_jobs` to control parallelism. The constructor validates:

- `cv` must be `None` or an integer at least 2.
- `timeout` must be `None` or a positive number.
- `n_jobs` must be an integer or `None`.
- `max_models` must be a positive integer when supplied.

Cross-validation can make a quick leaderboard much slower. For an initial
agent answer, prefer `max_models`, explicit model lists, or a tiny fixture
before running all models with CV.

## Predictions DataFrame

Set `predictions=True` to request per-model predictions:

```python
clf = LazyClassifier(predictions=True, classifiers=[LogisticRegression])
scores, predictions = clf.fit(X_train, X_test, y_train, y_test)
```

The predictions DataFrame has one column per successful model and one row per
test sample. When `predictions=False`, the DataFrame is intentionally empty.
Use `estimator.predict(X_test, model_name=...)` for later predictions from
stored fitted pipelines.

## Progress callbacks

`progress_callback` receives `(model_name, current, total, metrics)` after each
model attempt. `metrics` is `None` when the model failed. This is useful for
long interactive sweeps, but keep callback code lightweight because it runs in
the fitting loop.
