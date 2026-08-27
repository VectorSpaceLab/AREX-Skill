# Training Workflows

These workflows are self-contained patterns for `supervised.AutoML` training and prediction. They assume the package is installed and importable as `supervised`; see `../../../references/package-overview.md` for package assumptions.

## 1. Pick the right training recipe

| Situation | Recommended starting point |
| --- | --- |
| First run on unknown tabular data | `mode="Explain"`, `explain_level=0` or `1`, a short algorithm list, and a new `results_path`. |
| Need a reasonable production-style model | `mode="Perform"`, explicit `total_time_limit`, and keep `train_ensemble=True` unless speed matters more than model quality. |
| Competition/high-performance search | `mode="Compete"`, explicit time budget, and verify that stacking/feature engineering will not exceed budget. |
| Expensive tuning with Optuna | `mode="Optuna"` only with explicit `optuna_time_budget` and a small algorithm list. |
| Parser or installation smoke | Use `../scripts/mljar_automl_smoke.py --task binary --algorithms Baseline --total-time-limit 20`. |

For messy input tables, pause here and use `../../data-preprocessing/` before fitting.

## 2. Binary classification

```python
from pathlib import Path

import pandas as pd
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from supervised import AutoML

X, y = make_classification(
    n_samples=200,
    n_features=8,
    n_informative=5,
    n_redundant=1,
    n_classes=2,
    random_state=123,
)
X = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(X.shape[1])])
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=123
)

automl = AutoML(
    results_path=str(Path("AutoML_binary")),
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
    random_state=123,
)
automl.fit(X_train, y_train)

labels = automl.predict(X_test)
probabilities = automl.predict_proba(X_test)
all_predictions = automl.predict_all(X_test)
accuracy = automl.score(X_test, y_test)
```

Expected signals:

- `labels` has one label per input row.
- `probabilities.shape == (len(X_test), 2)`.
- `all_predictions` contains class-probability columns and `label`.
- `accuracy` is a finite float.

For imbalanced labels, consider `eval_metric="auc"`, `"average_precision"`, or `"f1"` and validate threshold-dependent decisions outside AutoML.

## 3. Multiclass classification

```python
import pandas as pd
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from supervised import AutoML

X, y = make_classification(
    n_samples=240,
    n_features=10,
    n_informative=6,
    n_redundant=1,
    n_classes=3,
    n_clusters_per_class=1,
    random_state=123,
)
X = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(X.shape[1])])
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=123
)

automl = AutoML(
    results_path="AutoML_multiclass",
    mode="Explain",
    ml_task="multiclass_classification",
    algorithms=["Baseline", "Decision Tree"],
    total_time_limit=45,
    explain_level=0,
    train_ensemble=False,
    stack_models=False,
    eval_metric="logloss",
    random_state=123,
)
automl.fit(X_train, y_train)

labels = automl.predict(X_test)
probabilities = automl.predict_proba(X_test)
all_predictions = automl.predict_all(X_test)
accuracy = automl.score(X_test, y_test)
```

Multiclass notes:

- `predict_proba()` returns one column per class.
- `score()` returns accuracy, not log loss.
- Allowed multiclass `eval_metric` values are `logloss`, `f1`, and `accuracy`.
- If labels are strings, AutoML encodes them internally and returns labels through the prediction interface.

## 4. Regression

```python
import pandas as pd
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split
from supervised import AutoML

X, y = make_regression(
    n_samples=220,
    n_features=8,
    n_informative=6,
    noise=10.0,
    random_state=123,
)
X = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(X.shape[1])])
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=123
)

automl = AutoML(
    results_path="AutoML_regression",
    mode="Explain",
    ml_task="regression",
    algorithms=["Baseline", "Decision Tree"],
    total_time_limit=45,
    explain_level=0,
    train_ensemble=False,
    stack_models=False,
    eval_metric="rmse",
    random_state=123,
)
automl.fit(X_train, y_train)

values = automl.predict(X_test)
all_predictions = automl.predict_all(X_test)
r2 = automl.score(X_test, y_test)
```

Regression notes:

- Do not call `predict_proba()`; it is classification-only.
- `score()` returns R², which can be negative for weak models or distribution shift.
- Allowed regression `eval_metric` values are `rmse`, `mse`, `mae`, `r2`, `mape`, `spearman`, and `pearson`.

## 5. Bounded model comparison

Start with a minimal list, then add heavier algorithms after the basic fit works:

```python
safe_algorithms = ["Baseline", "Decision Tree", "Linear"]
heavier_algorithms = ["Random Forest", "LightGBM", "Xgboost", "CatBoost"]

automl = AutoML(
    algorithms=safe_algorithms,
    mode="Explain",
    total_time_limit=60,
    explain_level=0,
    train_ensemble=False,
    stack_models=False,
    results_path="AutoML_compare_safe",
)
```

Escalation pattern:

1. Run `Baseline` to make sure task, target, and result directory are valid.
2. Add `Decision Tree` or `Linear` for quick model behavior.
3. Add one heavy learner at a time.
4. Re-enable `train_ensemble=True` only after individual learners work.
5. Use `mode="Perform"` or `"Compete"` when the time budget can absorb CV and extra search.

## 6. Explicit validation

### Split validation

```python
automl = AutoML(
    validation_strategy={
        "validation_type": "split",
        "train_ratio": 0.8,
        "shuffle": True,
        "stratify": True,
    },
    results_path="AutoML_split",
)
```

Use a split when the dataset is small, runtime must be short, or stacking is not required. For regression, omit `stratify` or set it false.

### K-fold validation

```python
automl = AutoML(
    validation_strategy={
        "validation_type": "kfold",
        "k_folds": 5,
        "shuffle": True,
        "stratify": True,
        "random_seed": 123,
    },
    results_path="AutoML_kfold",
)
```

K-fold validation is more reliable but multiplies runtime by the number of folds. `repeats` multiplies it again.

### Custom CV

```python
from sklearn.model_selection import StratifiedKFold

splitter = StratifiedKFold(n_splits=3, shuffle=True, random_state=123)
cv = list(splitter.split(X_train, y_train))

automl = AutoML(
    validation_strategy={"validation_type": "custom"},
    stack_models=False,
    results_path="AutoML_custom_cv",
)
automl.fit(X_train, y_train, cv=cv)
```

Custom CV must use row indices for the exact data passed into `fit()`. If `sample_weight` or fairness `sensitive_features` are supplied, they must align to the same row positions.

## 7. Sample weights

```python
automl.fit(X_train, y_train, sample_weight=weights_train)
score = automl.score(X_test, y_test, sample_weight=weights_test)
```

`sample_weight` should have one value per row. Use it for observation importance, not for target encoding or class relabeling.

## 8. Custom metric

```python
import numpy as np
from sklearn.metrics import f1_score

def negative_macro_f1(y_true, y_predicted, sample_weight=None):
    y_predicted = np.asarray(y_predicted)
    if y_predicted.ndim == 1:
        labels = (y_predicted > 0.5).astype(int)
    else:
        labels = np.argmax(y_predicted, axis=1)
    return -f1_score(y_true, labels, average="macro", sample_weight=sample_weight)

automl = AutoML(eval_metric=negative_macro_f1, results_path="AutoML_custom_metric")
```

Return a value to minimize. For a higher-is-better metric, return its negative value.

## 9. Retraining signal

```python
should_retrain = automl.need_retrain(X_new, y_new, decrease=0.05)
if should_retrain:
    print("Performance decreased enough to justify retraining review.")
```

Use `need_retrain()` only on labeled new data. Tune `decrease` to project risk tolerance and combine it with data drift, class balance, and error-analysis checks.

## 10. Safe bundled smoke helper

The bundled helper trains on synthetic data and avoids network or checkout-specific files:

```bash
python sub-skills/training-core/scripts/mljar_automl_smoke.py --help
python sub-skills/training-core/scripts/mljar_automl_smoke.py --task binary --algorithms Baseline --total-time-limit 20
python sub-skills/training-core/scripts/mljar_automl_smoke.py --task multiclass --algorithms "Baseline,Decision Tree" --results-path AutoML_smoke_multi --overwrite
python sub-skills/training-core/scripts/mljar_automl_smoke.py --task regression --algorithms Baseline --results-path AutoML_smoke_reg --overwrite
```

Use this helper to verify import, fit, `predict`, `predict_proba` where valid, `predict_all`, `score`, and `need_retrain` before moving to user data.
