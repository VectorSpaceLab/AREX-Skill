# Training Core API Reference

This reference covers the public `supervised.AutoML` training and prediction surface owned by `training-core`. Report extraction, persistence details, app generation, fairness, and detailed preprocessing are routed to sibling sub-skills.

## Import and estimator shape

```python
from supervised import AutoML
```

`AutoML` is a scikit-learn-style estimator for supervised tabular tasks:

- binary classification,
- multiclass classification,
- regression.

The verified package distribution is `mljar-supervised`; Python imports use the `supervised` package. There are no package CLI entry points for the training workflow.

## Constructor

Primary signature:

```python
AutoML(
    results_path=None,
    total_time_limit=3600,
    mode="Explain",
    ml_task="auto",
    model_time_limit=None,
    algorithms="auto",
    train_ensemble=True,
    stack_models="auto",
    eval_metric="auto",
    validation_strategy="auto",
    explain_level="auto",
    golden_features="auto",
    features_selection="auto",
    start_random_models="auto",
    hill_climbing_steps="auto",
    top_models_to_improve="auto",
    boost_on_errors="auto",
    kmeans_features="auto",
    mix_encoding="auto",
    max_single_prediction_time=None,
    optuna_time_budget=None,
    optuna_init_params={},
    optuna_verbose=True,
    fairness_metric="auto",
    fairness_threshold="auto",
    privileged_groups="auto",
    underprivileged_groups="auto",
    n_jobs=-1,
    verbose=1,
    random_state=1234,
)
```

Training-core normally uses all parameters through the public constructor. Fairness-specific constructor parameters are owned by `../../fairness-workflows/`; app/report methods are routed below.

### Task selection

`ml_task` values:

| Value | Use when |
| --- | --- |
| `"auto"` | Let AutoML infer the task from `y`: 2 unique target values means binary classification, 3-20 unique values means multiclass classification, and larger/continuous target values mean regression. |
| `"binary_classification"` | Force binary classification when labels might be ambiguous. |
| `"multiclass_classification"` | Force multiclass classification when class-count inference is risky. |
| `"regression"` | Force regression for continuous targets or integer targets with many possible values. |

For ambiguous integer targets, explicitly set `ml_task`. A target with few unique numeric values can be interpreted as classification.

### Modes and auto defaults

| Mode | Best fit | Default validation | Default algorithms | Default explanations | Search intensity |
| --- | --- | --- | --- | --- | --- |
| `Explain` | Understanding data and model behavior quickly. | 75/25 split, shuffled, stratified for classification. | `Baseline`, `Linear`, `Decision Tree`, `Random Forest`, `Xgboost`, `Neural Network`. | `explain_level=2`. | Lowest: one default model per algorithm, no hill climbing. |
| `Perform` | Production-style tabular model selection. | 5-fold CV, shuffled, stratified for classification. | `Linear`, `Random Forest`, `LightGBM`, `Xgboost`, `CatBoost`, `Neural Network`. | `explain_level=1`. | Moderate: random search and hill climbing. |
| `Compete` | Competition/performance search when time is available. | Usually 10-fold CV, but can auto-adjust under `total_time_limit`. | `Decision Tree`, `Linear`, `Random Forest`, `Extra Trees`, `LightGBM`, `Xgboost`, `CatBoost`, `Neural Network`, `Nearest Neighbors`. | `explain_level=0`. | High: larger random search, hill climbing, ensembling, stacking when feasible. |
| `Optuna` | Expensive per-algorithm hyperparameter optimization. | 10-fold CV. | `Random Forest`, `Extra Trees`, `LightGBM`, `Xgboost`, `CatBoost`, `Neural Network`. | `explain_level=0`. | Highest: Optuna per selected algorithm and data variant. |

`mode="Optuna"` uses `optuna_time_budget=3600` seconds per algorithm if no budget is supplied. Always set a smaller explicit value for bounded experiments.

### Algorithm names

Use exact strings:

```python
[
    "Baseline",
    "Linear",
    "Decision Tree",
    "Random Forest",
    "Extra Trees",
    "LightGBM",
    "Xgboost",
    "CatBoost",
    "Neural Network",
    "Nearest Neighbors",
]
```

All listed names are registered for binary classification, multiclass classification, and regression. Some algorithms import heavier backend packages (`LightGBM`, `Xgboost`, `CatBoost`, `Neural Network`), so start bounded runs with `Baseline`, `Decision Tree`, or `Linear` when diagnosing basic workflow issues.

## Fit and prediction methods

### `fit()`

```python
automl.fit(X, y, sample_weight=None, cv=None, sensitive_features=None) -> AutoML
```

Accepted training inputs:

- `X`: NumPy array or pandas DataFrame.
- `y`: NumPy array or pandas Series/DataFrame-like target.
- `sample_weight`: optional NumPy array or pandas Series.
- `cv`: optional iterable/list of `(train_indices, validation_indices)` splits. Use only with `validation_strategy={"validation_type": "custom"}`.
- `sensitive_features`: fairness input; route to `../../fairness-workflows/` for metric and group setup.

`fit()` returns `self`, so chained use is valid:

```python
pred = AutoML(...).fit(X_train, y_train).predict(X_test)
```

For dtype handling, missing values, text/categorical/datetime columns, and target preprocessing, read `../../data-preprocessing/`.

### `predict()`

```python
automl.predict(X) -> numpy.ndarray
```

Returns a one-dimensional NumPy array:

- class labels for classification,
- numeric predictions for regression.

The model must be fitted or loaded from a valid `results_path` before calling.

### `predict_proba()`

```python
automl.predict_proba(X) -> numpy.ndarray
```

Classification only. Returns an array of shape `(n_samples, n_classes)` with class probabilities. Calling this method on a regression model raises an `AutoMLException`; use `predict()` or `predict_all()` instead.

### `predict_all()`

```python
automl.predict_all(X) -> pandas.DataFrame
```

Returns a DataFrame:

- binary/multiclass classification: probability columns plus `label`,
- regression: a `prediction` column.

Use this when downstream code needs both class labels and probabilities, or when a compact DataFrame is easier to inspect than raw arrays.

### `score()`

```python
automl.score(X, y=None, sample_weight=None) -> float
```

`y` is required. The returned value is higher-is-better:

- classification: mean accuracy,
- regression: R².

Do not confuse `score()` with the internal optimization metric; model selection still follows `eval_metric`.

### `need_retrain()`

```python
automl.need_retrain(X, y, sample_weight=None, decrease=0.1) -> bool
```

Compares performance on new labeled data with the trained model's stored performance. With the default `decrease=0.1`, it returns true when performance decreases by roughly 10% according to the model's metric. Treat it as a quick retraining signal, then validate with project-specific monitoring.

## Evaluation metrics

`eval_metric="auto"` chooses:

- binary classification: `logloss`,
- multiclass classification: `logloss`,
- regression: `rmse`.

Allowed string metrics:

| Task | Metrics |
| --- | --- |
| Binary classification | `logloss`, `auc`, `f1`, `average_precision`, `accuracy` |
| Multiclass classification | `logloss`, `f1`, `accuracy` |
| Regression | `rmse`, `mse`, `mae`, `r2`, `mape`, `spearman`, `pearson` |

### Custom metric function

Pass a Python function directly:

```python
def my_metric(y_true, y_predicted, sample_weight=None):
    return value

automl = AutoML(eval_metric=my_metric)
```

Rules:

- Return one numeric scalar.
- Handle `sample_weight=None`.
- Be deterministic and fast; it can be used during early stopping/model selection.
- AutoML minimizes the returned value. For higher-is-better metrics, return the negative value.
- Classification predictions passed to the metric can be probabilities, so threshold or `argmax` inside the metric when label-based scoring is needed.

## Validation strategies

### Auto validation

```python
AutoML(validation_strategy="auto")
```

The mode determines split/CV defaults. Regression removes `stratify` even if supplied.

### Explicit train/validation split

```python
validation_strategy = {
    "validation_type": "split",
    "train_ratio": 0.75,
    "shuffle": True,
    "stratify": True,  # omit or False for regression
}
```

`repeats` is supported when `shuffle=True`. If `shuffle=False`, repeated validation is disabled.

### Explicit k-fold CV

```python
validation_strategy = {
    "validation_type": "kfold",
    "k_folds": 5,
    "shuffle": True,
    "stratify": True,  # omit or False for regression
    "random_seed": 123,
}
```

`repeats` can multiply the number of trained learners: `k_folds * repeats`.

### Custom CV

```python
cv = [(train_idx, valid_idx), ...]
automl = AutoML(validation_strategy={"validation_type": "custom"})
automl.fit(X, y, cv=cv)
```

Each split must contain index arrays compatible with the rows of `X`, `y`, and optional `sample_weight`/`sensitive_features`. Custom validation disables some automatic stacking/boost-on-errors behavior.

## Time and budget parameters

| Parameter | Meaning |
| --- | --- |
| `total_time_limit` | Overall training limit in seconds. Ignored when `model_time_limit` is not `None`; set to `None` only when intentionally unbounded. |
| `model_time_limit` | Limit per model, including all learners/folds for that model. If set, the overall `total_time_limit` is not respected. |
| `optuna_time_budget` | Per-algorithm Optuna tuning budget in seconds for `mode="Optuna"`; default is expensive. |
| `n_jobs` | CPU parallelism for supported learners. Use `1` for predictable small smokes. |
| `max_single_prediction_time` | Optional single-row prediction-time constraint; `Perform` defaults to a 0.5 second target when not set. |

For fast checks, use `algorithms=["Baseline"]` or `algorithms=["Baseline", "Decision Tree"]`, `explain_level=0`, `train_ensemble=False`, `stack_models=False`, and short time limits.

## Methods routed to other sub-skills

- `report()` and `report_structured(format="markdown"|"dict"|"json", model_name=...)`: `../../artifacts-reports/`.
- Saved-run loading through `results_path`, leaderboard files, and artifact layout: `../../artifacts-reports/`.
- `app(path=..., overwrite=..., title=..., verbose=...)`, `local_app()`, and `publish_app(...)`: `../../app-deployment/`.
- Fairness constructor parameters and `fit(..., sensitive_features=...)`: `../../fairness-workflows/`.

## Minimal bounded template

```python
from supervised import AutoML

automl = AutoML(
    mode="Explain",
    ml_task="binary_classification",
    algorithms=["Baseline", "Decision Tree"],
    total_time_limit=30,
    explain_level=0,
    train_ensemble=False,
    stack_models=False,
    start_random_models=1,
    hill_climbing_steps=0,
    top_models_to_improve=0,
    results_path="AutoML_safe_smoke",
    random_state=123,
)
automl.fit(X_train, y_train)
labels = automl.predict(X_test)
probabilities = automl.predict_proba(X_test)
summary = automl.predict_all(X_test)
score = automl.score(X_test, y_test)
```
