# Metrics, scoring functions, dataset compression, and resampling

This reference covers the scoring and data-splitting configuration that should be settled before running `autosklearn` estimators.

## Built-in metrics

Import metrics from `autosklearn.metrics`.

```python
import autosklearn.metrics as askl_metrics
```

Classification metrics available in the inspected API:

| Metric name | Notes |
|---|---|
| `accuracy` | Default for binary and multiclass classification. |
| `balanced_accuracy` | Often better for imbalanced classification. |
| `roc_auc` | Uses threshold/decision values; binary and multilabel cases only where scorer support applies. |
| `average_precision` | Uses threshold/decision values. |
| `log_loss` | Uses probabilities (`needs_proba=True`); lower is better but scorer handles sign/loss conversion. |
| `precision_macro`, `precision_micro`, `precision_samples`, `precision_weighted` | Prefer averaged variants for multiclass/multilabel instead of binary-only `precision`. |
| `recall_macro`, `recall_micro`, `recall_samples`, `recall_weighted` | Prefer averaged variants for multiclass/multilabel instead of binary-only `recall`. |
| `f1_macro`, `f1_micro`, `f1_samples`, `f1_weighted` | Default for multilabel classification is `f1_macro`. |

Regression metrics available in the inspected API:

| Metric name | Notes |
|---|---|
| `r2` | Default for regression and multioutput regression. |
| `mean_absolute_error` | Loss metric; lower raw value is better, scorer sign is flipped for optimization. |
| `mean_squared_error` | Loss metric. |
| `root_mean_squared_error` | Loss metric. |
| `mean_squared_log_error` | Loss metric; invalid when targets/predictions contain negative values. |
| `median_absolute_error` | Loss metric. |

Default metric map:

- binary classification: `accuracy`;
- multiclass classification: `accuracy`;
- multilabel classification: `f1_macro`;
- regression: `r2`;
- multioutput regression: `r2`.

## Single metric versus multiple metrics

Constructor signature includes:

```python
AutoSklearnClassifier(..., metric=None, scoring_functions=None, ...)
AutoSklearnRegressor(..., metric=None, scoring_functions=None, ...)
```

Use `metric` for the optimization objective. In the inspected API, it can be one scorer or a sequence of scorers. Use `scoring_functions` for additional metrics to calculate and report for each run.

```python
from autosklearn.metrics import balanced_accuracy, precision_macro, recall_macro, f1_macro

automl = autosklearn.classification.AutoSklearnClassifier(
    metric=balanced_accuracy,
    scoring_functions=[precision_macro, recall_macro, f1_macro],
)
```

Multiple metric outputs appear in result dictionaries/DataFrames with `metric_`-prefixed columns and in multi-objective cost fields. Route result interpretation to `search-and-parallelism` if the user needs leaderboard or ensemble analysis.

Validation rules:

- Every metric must be an `autosklearn.metrics.Scorer`.
- At least one optimization metric must exist after defaulting.
- Reusing the exact same scorer object is allowed.
- Different scorer objects with the same `.name` are rejected with a duplicate-name error.
- Do not give a custom scorer the same name as a built-in scorer unless it is intentionally the same scorer object.

## `make_scorer` for custom metrics

Signature:

```python
from autosklearn.metrics import make_scorer

make_scorer(
    name,
    score_func,
    *,
    optimum=1.0,
    worst_possible_result=0.0,
    greater_is_better=True,
    needs_proba=False,
    needs_threshold=False,
    needs_X=False,
    **kwargs,
)
```

Scorer modes:

| Flags | Prediction passed to `score_func` | Use case |
|---|---|---|
| default flags | predicted labels/values after auto-sklearn scorer conversion | accuracy, F1-like label metrics, regression metrics. |
| `needs_proba=True` | probability estimates | log-loss and custom probability metrics. |
| `needs_threshold=True` | continuous decision values; binary/multilabel threshold scorer support | ROC AUC, average precision. |
| `needs_X=True` | scorer forwards `X_data=` keyword to `score_func` | metrics that score a subset or use feature values. |

Invalid flag combination:

```python
make_scorer("bad", func, needs_proba=True, needs_threshold=True)  # ValueError
```

because exactly one of probability or threshold mode can be active.

Loss metrics:

```python
error_rate = make_scorer(
    name="custom_error_rate",
    score_func=lambda y_true, y_pred: (y_true != y_pred).mean(),
    optimum=0,
    worst_possible_result=1,
    greater_is_better=False,
)
```

`greater_is_better=False` flips the sign for optimization; users should still set `optimum` and `worst_possible_result` to the raw metric meaning.

Metric with extra parameters and `X_data`:

```python
def accuracy_on_group(y_true, y_pred, X_data=None, column=0, threshold=0.0):
    if X_data is None:
        raise ValueError("X_data is required")
    mask = X_data[:, column] > threshold
    return (y_true[mask] == y_pred[mask]).mean()

group_accuracy = make_scorer(
    name="group_accuracy_col0_gt0",
    score_func=accuracy_on_group,
    optimum=1,
    worst_possible_result=0,
    greater_is_better=True,
    needs_X=True,
    column=0,
    threshold=0.0,
)
```

Rules for difficult custom scorer cases:

1. Pick a unique name that does not collide with built-ins or other custom scorers.
2. If the metric needs `X_data`, set `needs_X=True`; otherwise the scorer will call the function with `X_data=None`.
3. Use either `needs_proba=True` or `needs_threshold=True`, never both.
4. Ensure the score function accepts `sample_weight` or arbitrary `**kwargs` if it may receive extra keyword arguments.
5. For threshold metrics, confirm the target type is binary or multilabel-indicator; multiclass threshold scoring is skipped or fails depending on metric path.

## Programmatic metric checks without training

For synthetic validation of scorers:

```python
import numpy as np
from autosklearn.constants import BINARY_CLASSIFICATION, REGRESSION
from autosklearn.metrics import calculate_scores, calculate_losses, accuracy, r2

scores = calculate_scores(
    solution=np.array([0, 1, 1]),
    prediction=np.array([[1.0, 0.0], [0.0, 1.0], [0.2, 0.8]]),
    task_type=BINARY_CLASSIFICATION,
    metrics=[accuracy],
)
losses = calculate_losses(
    solution=np.array([1.0, 2.0, 3.0]),
    prediction=np.array([1.0, 2.5, 2.8]),
    task_type=REGRESSION,
    metrics=[r2],
)
```

Native test candidates for later verification include scorer behavior, sign flip, duplicate name rejection, `needs_X`, and `scoring_functions` calculations.

## `dataset_compression`

Estimator constructor parameter:

```python
AutoSklearnClassifier(..., memory_limit=3072, dataset_compression=True)
```

Valid values:

| Value | Meaning |
|---|---|
| `True` | Use default `{"memory_allocation": 0.1, "methods": ["precision", "subsample"]}`. |
| `False` | Disable dataset compression. |
| dict | Merge supplied keys with defaults and validate. |

Dict schema:

```python
dataset_compression = {
    "memory_allocation": 0.1,              # float in (0, 1), fraction of memory_limit
    "methods": ["precision", "subsample"], # non-empty sequence of allowed methods
}
```

`memory_allocation` may also be an integer number of MB, but it must be greater than 0 and less than `memory_limit`.

Allowed methods:

- `"precision"`: reduce supported floating dtypes, for example float64 to float32.
- `"subsample"`: reduce number of samples to fit into allocated memory.

Important behavior:

- Unknown dict keys are invalid.
- `memory_allocation` strings/lists/dicts are invalid.
- Float allocation must be strictly between 0 and 1.
- Integer allocation must be strictly between 0 and `memory_limit`.
- `methods` must be non-empty and contain only allowed methods.
- Compression does not support pandas DataFrames/Series in the fit path; pandas inputs are skipped for size reduction after validation.
- If X has an integer dtype, precision reduction is removed and only subsampling remains when requested.

Recipes:

```python
# Disable all dataset size changes, useful when exact sample order matters.
dataset_compression = False

# Preserve row count/order but allow float precision reduction.
dataset_compression = {"methods": ["precision"]}

# Allocate 20% of memory_limit to the dataset.
dataset_compression = {"memory_allocation": 0.2}

# Absolute allocation in MB; must be less than memory_limit.
dataset_compression = {"memory_allocation": 512, "methods": ["precision"]}
```

## Resampling strategies

Constructor parameters:

```python
AutoSklearnClassifier(
    resampling_strategy="holdout",
    resampling_strategy_arguments=None,
)
```

Known options:

| Strategy | Arguments | Notes |
|---|---|---|
| `"holdout"` | `{"train_size": 0.67, "shuffle": True}` by default | Default 67:33 optimization split. |
| `"holdout-iterative-fit"` | holdout arguments | Same holdout idea, with iterative fit where possible. |
| `"cv"` | `{"folds": 5}` by default/when missing | Cross-validation. Fold-trained models can predict as a soft-voting ensemble; call `refit()` for final whole-data training. |
| `"cv-iterative-fit"` | `{"folds": 5}` | CV with iterative fit where possible. |
| `"partial-cv"` | `{"folds": 5}` | CV-like strategy using intensification. |
| scikit-learn splitter object | depends on splitter | Examples include `KFold`, `StratifiedKFold`, `ShuffleSplit`, `PredefinedSplit`, repeated splitters. |

Holdout recipe:

```python
automl = autosklearn.classification.AutoSklearnClassifier(
    resampling_strategy="holdout",
    resampling_strategy_arguments={"train_size": 0.8, "shuffle": True},
)
```

CV recipe:

```python
automl = autosklearn.classification.AutoSklearnClassifier(
    resampling_strategy="cv",
    resampling_strategy_arguments={"folds": 5},
)
automl.fit(X_train, y_train)
# For final deployment predictions trained on all available data:
automl.refit(X_train.copy(), y_train.copy())
```

Predefined split recipe:

```python
from sklearn.model_selection import PredefinedSplit

# -1 means always training fold; non-negative values identify validation folds.
predefined = PredefinedSplit(test_fold=test_fold)

automl = autosklearn.classification.AutoSklearnClassifier(
    resampling_strategy=predefined,
    dataset_compression=False,  # Preserve row order/size for the splitter.
)
automl.fit(X_train, y_train)
automl.refit(X_train, y_train)
```

Custom splitter safety rules:

- If the splitter relies on sample positions, group alignment, or exact row count, disable subsampling: `dataset_compression=False` or `{"methods": ["precision"]}`.
- If using a splitter class that accepts `n_splits`, the value of `resampling_strategy_arguments["folds"]` is used.
- Call `refit()` after custom splitter workflows before final predictions on new data.
- Ensure train/test folds are compatible with target type; stratified splitters require classification-compatible labels.
- Keep route to `search-and-parallelism` for how CV/multiple metrics appear in `cv_results_` or leaderboards.

## `X_test`/`y_test` plus scoring outputs

Passing `X_test` and `y_test` to estimator `fit()` enables held-out test scores in performance-over-time outputs, separate from the optimization resampling strategy. They are also used by target validation to include test classes in classification target encoding.

```python
automl.fit(X_train, y_train, X_test=X_test, y_test=y_test)
```

Do this when:

- the user wants test-score traces during search;
- classification test split may contain labels absent from training split;
- you need metric calculations for `scoring_functions` on the test split.

Do not confuse `X_test`/`y_test` with `resampling_strategy`: they do not define the optimization folds unless the resampling strategy says so.
