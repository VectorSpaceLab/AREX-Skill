# Supervised API Reference

## Verified constructors

Installed-package inspection verified these public constructor signatures for
Lazy Predict `0.3.0`.

```python
LazyClassifier(
    verbose=0, ignore_warnings=True, custom_metric=None, predictions=False,
    random_state=42, classifiers="all", cv=None, timeout=None,
    categorical_encoder="onehot", n_jobs=-1, max_models=None,
    progress_callback=None, use_gpu=False,
    tune=False, tune_top_k=5, tune_trials=50, tune_timeout=None,
    tune_backend="optuna",
)
```

```python
LazyRegressor(
    verbose=0, ignore_warnings=True, custom_metric=None, predictions=False,
    random_state=42, regressors="all", cv=None, timeout=None,
    categorical_encoder="onehot", n_jobs=-1, max_models=None,
    progress_callback=None, use_gpu=False,
    tune=False, tune_top_k=5, tune_trials=50, tune_timeout=None,
    tune_backend="optuna",
)
```

Both classes inherit common behavior from Lazy Predict's base estimator.

## Fit contract

```python
scores, predictions_df = estimator.fit(X_train, X_test, y_train, y_test)
```

- `X_train` and `X_test` may be pandas DataFrames or NumPy arrays. Arrays are
  converted to DataFrames internally.
- `y_train` and `y_test` may be pandas Series or NumPy arrays.
- The method always returns a 2-tuple.
- `scores` is a pandas DataFrame indexed by model name.
- `predictions_df` is a pandas DataFrame. It is empty unless the estimator was
  constructed with `predictions=True`.
- Fitted pipelines are stored in `estimator.models`; per-model exceptions are
  stored in `estimator.errors`.

## Model selection

Use explicit model lists for deterministic, fast tasks:

```python
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.tree import DecisionTreeClassifier

clf = LazyClassifier(classifiers=[LogisticRegression, DecisionTreeClassifier])
reg = LazyRegressor(regressors=[Ridge])
```

The source accepts class objects and also supports string names in the model
list. `"all"` requests every available estimator after Lazy Predict removes
known-problem classes and adds installed optional estimators such as XGBoost,
LightGBM, CatBoost, PerpetualBooster, or InterpretML EBM.

`max_models` truncates the selected estimator list after it is assembled. Use it
for quick smoke runs, but prefer named model lists for reproducible user-facing
results.

## Result columns

Classifier scores include at least:

- `Accuracy`
- `Balanced Accuracy`
- `ROC AUC`
- `F1 Score`
- `Precision`
- `Recall`
- `Time Taken`

Regressor scores include at least:

- `Adjusted R-Squared`
- `R-Squared`
- `RMSE`
- `Time Taken`

When `custom_metric` is supplied, the custom metric column uses the callable's
`__name__`. When `cv` is supplied, extra cross-validation mean/std columns are
added.

## Accessing fitted models

After `fit()`, use the fitted sklearn pipelines directly:

```python
models = clf.provide_models(X_train, X_test, y_train, y_test)
rf = models["RandomForestClassifier"]
y_pred = rf.predict(X_test)
```

`provide_models()` calls `fit()` automatically only if no models have been
fitted yet. For already fitted estimators, it returns the existing
`estimator.models` dictionary.

The base estimator also exposes:

```python
all_predictions = clf.predict(X_test)
one_model_predictions = clf.predict(X_test, model_name="LogisticRegression")
```

Calling `predict()` before any model is fitted raises `ValueError`.

## Persistence

```python
clf.save_models("saved_models")
loaded = clf.load_models("saved_models")
```

- Models are saved as `<ModelName>.joblib` files.
- `save_models()` raises `ValueError` when no models were fitted.
- `load_models()` raises `FileNotFoundError` when the directory is missing.
- Persisted pipelines include Lazy Predict preprocessing steps; use compatible
  package versions when loading later.

## Tuning and explainability pointers

The supervised constructors accept tuning flags, but detailed choices for
Optuna/sklearn/FLAML tuning and explainability live in
[../../advanced-workflows/SKILL.md](../../advanced-workflows/SKILL.md).
For a quick post-fit feature-importance table without optional SHAP, use the
permutation path described there.
