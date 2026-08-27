---
name: supervised-benchmarking
description: "Use Lazy Predict LazyClassifier and LazyRegressor for low-code
  supervised classification and regression model benchmarking, result
  interpretation, categorical data handling, and fitted model access."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Supervised Benchmarking

Use this sub-skill when the task is to compare many sklearn-style classifiers or
regressors quickly with Lazy Predict, interpret the ranked result table, recover
failed models, or extract fitted pipelines for downstream prediction.

## Start here

1. Decide whether the target is classification or regression.
2. Split data yourself with scikit-learn or an equivalent deterministic split.
3. Bound the run when speed matters: choose a small explicit model list,
   `max_models`, and/or `timeout` rather than using every estimator.
4. Run the bundled smoke helper if the environment or API contract is in doubt:

   ```bash
   python scripts/smoke_supervised.py --task both --max-models 1
   ```

## Main APIs

Read [references/api-reference.md](references/api-reference.md) for verified
constructor signatures, `fit()` return shapes, selected-model syntax,
`provide_models()`, `predict()`, and joblib persistence.

Typical bounded classification pattern:

```python
from lazypredict.Supervised import LazyClassifier
from sklearn.linear_model import LogisticRegression

clf = LazyClassifier(
    classifiers=[LogisticRegression],
    verbose=0,
    ignore_warnings=True,
    predictions=True,
    max_models=1,
)
scores, predictions = clf.fit(X_train, X_test, y_train, y_test)
```

Typical bounded regression pattern:

```python
from lazypredict.Supervised import LazyRegressor
from sklearn.linear_model import Ridge

reg = LazyRegressor(regressors=[Ridge], verbose=0, ignore_warnings=True)
scores, _ = reg.fit(X_train, X_test, y_train, y_test)
```

## Data and results

Read [references/data-and-results.md](references/data-and-results.md) when the
data has pandas categorical columns, boolean columns, custom metrics,
cross-validation, prediction output, or model ranking columns that must be
validated.

Key reminders:

- `fit()` returns a tuple `(scores, predictions_df)` for both classifiers and
  regressors. The predictions DataFrame is empty unless `predictions=True`.
- `categorical_encoder` accepts `"onehot"`, `"ordinal"`, `"target"`, or
  `"binary"`; target and binary encoding require the optional
  `category_encoders` package.
- Inspect `.errors` after fitting when important models are absent from the
  result table.

## Troubleshooting

Read [references/troubleshooting.md](references/troubleshooting.md) for slow or
failing estimators, invalid constructor arguments, empty/mismatched datasets,
missing optional dependencies, hidden model errors, ROC-AUC surprises, GPU
fallback, and model persistence failures.

## Route elsewhere

- Use [time-series-forecasting](../time-series-forecasting/SKILL.md) for
  `LazyForecaster` or forecast metrics.
- Use [advanced-workflows](../advanced-workflows/SKILL.md) for detailed tuning,
  search spaces, SHAP, and advanced explainability choices.
- Use [cli-and-integrations](../cli-and-integrations/SKILL.md) for the CSV CLI,
  MLflow tracking setup, Dask/PySpark conversion, Spark classes, and package
  environment checks.
