# Estimator workflows

These recipes are self-contained operating guidance for future agents. They assume `autosklearn` imports successfully and that a bounded AutoML fit is appropriate for the user's environment. For feature dtypes, metrics, custom scorers, and resampling details, route to [data-metrics-validation](../../data-metrics-validation/). For parallelism, search strategy, and deep result interpretation, route to [search-and-parallelism](../../search-and-parallelism/).

## Workflow 1: standard classification

Use this for binary, multiclass, and multilabel classification unless the user explicitly asks for Auto-sklearn 2.0.

```python
from pathlib import Path
from pprint import pprint

import autosklearn.classification
from sklearn.datasets import load_breast_cancer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

X, y = load_breast_cancer(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, random_state=1, stratify=y
)

tmp_folder = Path("runs") / "askl-classification"
tmp_folder.mkdir(parents=True, exist_ok=True)

automl = autosklearn.classification.AutoSklearnClassifier(
    time_left_for_this_task=120,
    per_run_time_limit=30,
    seed=1,
    tmp_folder=str(tmp_folder),
    delete_tmp_folder_after_terminate=False,
    disable_evaluator_output=False,
)
automl.fit(X_train, y_train, dataset_name="breast_cancer")

pred = automl.predict(X_test)
proba = automl.predict_proba(X_test)
print("prediction shape:", pred.shape)
print("probability shape:", proba.shape)
print("accuracy:", accuracy_score(y_test, pred))
print(automl.sprint_statistics())
print(automl.leaderboard(top_k=5, ensemble_only=True))
pprint(automl.show_models(), indent=2)
```

Validation checkpoints:

- `pred.shape[0] == X_test.shape[0]`.
- For binary/multiclass, `proba.shape == (n_samples, n_classes)`, values are in `[0, 1]`, and each row approximately sums to `1`.
- `sprint_statistics()` shows at least one successful run for a meaningful model; if the final ensemble is dummy-only, use [troubleshooting](troubleshooting.md#dummy-only-or-failed-runs).
- `leaderboard(top_k=5)` returns a `DataFrame` indexed by model id. If it is empty or only dummy entries are shown, inspect run failures and budgets.

## Workflow 2: regression

Use this for scalar regression targets.

```python
from pathlib import Path
from pprint import pprint

import autosklearn.regression
from sklearn.datasets import load_diabetes
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split

X, y = load_diabetes(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=1)

tmp_folder = Path("runs") / "askl-regression"
tmp_folder.mkdir(parents=True, exist_ok=True)

automl = autosklearn.regression.AutoSklearnRegressor(
    time_left_for_this_task=120,
    per_run_time_limit=30,
    seed=1,
    tmp_folder=str(tmp_folder),
    delete_tmp_folder_after_terminate=False,
)
automl.fit(X_train, y_train, dataset_name="diabetes")

pred = automl.predict(X_test)
print("prediction shape:", pred.shape)
print("R2:", r2_score(y_test, pred))
print(automl.sprint_statistics())
print(automl.leaderboard(top_k=5, ensemble_only=True))
pprint(automl.show_models(), indent=2)
```

Validation checkpoints:

- `pred.shape == (n_samples,)` for scalar regression.
- R2 can be negative for weak fits; a bounded smoke only verifies the workflow, not quality.
- `sprint_statistics()` should report successful runs before treating the model as useful.

## Workflow 3: choose among classifier, regressor, ASKL2, multilabel, and multioutput

Use this decision table before writing code:

| User's target/problem | Estimator | Target shape check | Output validation |
|---|---|---|---|
| Binary/multiclass labels | `AutoSklearnClassifier` | `type_of_target(y)` is `binary` or `multiclass` | `predict` returns one label per row; `predict_proba` rows sum to 1. |
| Multi-label classification | `AutoSklearnClassifier` | `type_of_target(y)` is `multilabel-indicator`; `y` is 2-D with positive labels encoded as `1` and negatives as `0`/`-1` | `predict` returns `(n_samples, n_labels)`; `predict_proba` values are in `[0, 1]`, but rows do not need to sum to 1. |
| Scalar regression | `AutoSklearnRegressor` | `type_of_target(y)` is `continuous` or numeric binary/multiclass treated as regression | `predict` returns `(n_samples,)`; evaluate with regression metrics. |
| Multioutput regression | `AutoSklearnRegressor` | `type_of_target(y)` is `continuous-multioutput`; `y` is 2-D | `predict` returns `(n_samples, n_outputs)`; evaluate each output or multioutput aggregate. |
| Hands-free ASKL2 classifier | `AutoSklearn2Classifier` | Classification target types only | Same classifier output checks, plus confirm ASKL2 cache/selector files are writable. |

Quick target probe:

```python
from sklearn.utils.multiclass import type_of_target
print(type_of_target(y))
```

Route target conversion, pandas categories, string columns, `feat_type`, and metric selection to [data-metrics-validation](../../data-metrics-validation/).

## Workflow 4: multilabel classification

Multilabel examples are fit-heavy in the original materials, so use this target-shape pattern instead of downloading external data during a quick task.

```python
import numpy as np
from sklearn.datasets import make_multilabel_classification
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.utils.multiclass import type_of_target

import autosklearn.classification

X, y = make_multilabel_classification(
    n_samples=600,
    n_features=20,
    n_classes=4,
    random_state=1,
)
y = y.astype(int)
assert type_of_target(y) == "multilabel-indicator"

X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=1)

automl = autosklearn.classification.AutoSklearnClassifier(
    time_left_for_this_task=120,
    per_run_time_limit=30,
    initial_configurations_via_metalearning=0,  # optional for bounded experimentation
    seed=1,
)
automl.fit(X_train, y_train, dataset_name="synthetic_multilabel")

pred = automl.predict(X_test)
proba = automl.predict_proba(X_test)
assert pred.shape == y_test.shape
assert proba.shape[0] == X_test.shape[0]
assert np.all((0 <= proba) & (proba <= 1))
print("macro F1:", f1_score(y_test, pred, average="macro"))
print(automl.sprint_statistics())
```

Notes:

- Do not coerce a true multilabel problem into multiclass labels; keep a 2-D indicator target.
- Multilabel probability rows represent label-wise probabilities and are not expected to sum to one.
- Use multilabel-aware metrics (`f1_macro`, `f1_micro`, etc.) rather than binary-only defaults; details belong in [data-metrics-validation](../../data-metrics-validation/).

## Workflow 5: multioutput regression

```python
from sklearn.datasets import make_regression
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from sklearn.utils.multiclass import type_of_target

from autosklearn.regression import AutoSklearnRegressor

X, y = make_regression(
    n_samples=600,
    n_features=12,
    n_informative=6,
    n_targets=3,
    random_state=1,
)
assert type_of_target(y) == "continuous-multioutput"

X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=1)

automl = AutoSklearnRegressor(
    time_left_for_this_task=120,
    per_run_time_limit=30,
    seed=1,
)
automl.fit(X_train, y_train, dataset_name="synthetic_multioutput")

pred = automl.predict(X_test)
assert pred.shape == y_test.shape
print("R2 weighted uniform:", r2_score(y_test, pred, multioutput="uniform_average"))
print(automl.leaderboard(top_k=5))
```

Notes:

- `AutoSklearnRegressor` accepts continuous multioutput targets; do not use `AutoSklearnClassifier` for multiclass-multioutput targets.
- Some model families may be unavailable for multioutput data; use the estimator's configuration space and leaderboard as diagnostics, then route search-space details to [search-and-parallelism](../../search-and-parallelism/).

## Workflow 6: AutoSklearn2Classifier

Use ASKL2 when the user asks for Auto-sklearn 2.0 or wants the system to choose its policy automatically. It is classification-only and intentionally omits several standard classifier knobs.

```python
from autosklearn.experimental.askl2 import AutoSklearn2Classifier
from sklearn.datasets import load_breast_cancer
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import train_test_split

X, y = load_breast_cancer(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, random_state=1, stratify=y
)

automl = AutoSklearn2Classifier(
    time_left_for_this_task=120,
    per_run_time_limit=30,
    seed=1,
)
automl.fit(X_train, y_train, dataset_name="breast_cancer")
pred = automl.predict(X_test)
print("balanced accuracy:", balanced_accuracy_score(y_test, pred))
print(automl.sprint_statistics())
```

ASKL2 operating notes:

- It may create selector cache files under the user's cache/home area. If that location is not writable, set a writable `XDG_CACHE_HOME` for the process or use `AutoSklearnClassifier` instead.
- It selects among packaged policies and sets `include`/`feature_preprocessor` internally. If the user needs explicit component filtering, use the standard classifier plus [search-and-parallelism](../../search-and-parallelism/) or [custom-components](../../custom-components/).

## Workflow 7: refit after validation or cross-validation

Call `refit(X, y)` when using cross-validation, or when a holdout run should be trained again on all available training data after model selection.

```python
automl.fit(X_train, y_train, dataset_name="my_dataset")
print(automl.sprint_statistics())

automl.refit(X_train_full, y_train_full)
pred = automl.predict(X_test)
```

Important constraints:

- `refit` requires a fitted estimator with saved model information.
- Do not use `disable_evaluator_output=True` if the workflow depends on prediction/refit/inspection.
- If `predict` after cross-validation complains that no model is fitted for new data, call `refit` on the intended training data.

## Workflow 8: post-hoc `fit_ensemble`

Use `fit_ensemble` only after a previous optimization run produced model and prediction outputs.

```python
from autosklearn.constants import MULTICLASS_CLASSIFICATION

automl.fit(X_train, y_train, dataset_name="iris")
# Rebuild a smaller ensemble from saved validation predictions.
automl.fit_ensemble(
    y_train,
    task=MULTICLASS_CLASSIFICATION,
    dataset_name="iris",
    ensemble_kwargs={"ensemble_size": 5},
)
print(automl.leaderboard(top_k=5))
```

Notes:

- The `task` argument uses constants such as `BINARY_CLASSIFICATION`, `MULTICLASS_CLASSIFICATION`, `MULTILABEL_CLASSIFICATION`, `REGRESSION`, or `MULTIOUTPUT_REGRESSION`.
- If `ensemble_class="default"`, single-objective runs use ensemble selection and multi-objective runs use a dummy multi-objective ensemble. Deep ensemble choices belong in [search-and-parallelism](../../search-and-parallelism/).
- `ensemble_size` as a direct argument is deprecated in the inspected API; prefer `ensemble_kwargs={"ensemble_size": n}` for ensemble selection.

## Workflow 9: temporary folder and cleanup control

Use explicit folders when the user needs logs, saved models, or reproducible inspection. Use automatic temporary folders for throwaway runs.

```python
from pathlib import Path

run_dir = Path("runs") / "askl-my-dataset-seed1"
run_dir.mkdir(parents=True, exist_ok=True)

automl = autosklearn.classification.AutoSklearnClassifier(
    time_left_for_this_task=300,
    per_run_time_limit=60,
    tmp_folder=str(run_dir),
    delete_tmp_folder_after_terminate=False,
    max_models_on_disc=20,
)
```

Operating rules:

- Give every independent run a distinct `tmp_folder`; auto-sklearn stores logs, data manager files, model outputs, and SMAC outputs there.
- `delete_tmp_folder_after_terminate=True` is suitable for disposable runs. Set it to `False` only if the user wants to inspect logs/models or run post-hoc workflows.
- `max_models_on_disc` limits retained model artifacts, but logs and other temporary files can still grow. Route disk/performance tuning to [search-and-parallelism](../../search-and-parallelism/).
- In this installed API, `output_directory` is not a constructor argument. Do not add it to examples unless a newer signature proves it exists.

## Workflow 10: bounded smoke helper

The bundled script [bounded_estimator_smoke.py](../scripts/bounded_estimator_smoke.py) adapts the basic classification and regression examples into a safe helper.

Dry-run only, default behavior:

```bash
python sub-skills/estimators/scripts/bounded_estimator_smoke.py --task classification
python sub-skills/estimators/scripts/bounded_estimator_smoke.py --task regression --time-left 45 --per-run-time-limit 10
```

Print help:

```bash
python sub-skills/estimators/scripts/bounded_estimator_smoke.py --help
```

Actually run a bounded smoke only when the user approves a small fit:

```bash
python sub-skills/estimators/scripts/bounded_estimator_smoke.py \
  --task classification \
  --time-left 60 \
  --per-run-time-limit 15 \
  --tmp-dir runs/askl-smoke \
  --run
```

Smoke acceptance signals:

- Script imports the selected estimator class.
- `fit` returns without exception on a small built-in scikit-learn dataset.
- `predict` shape matches the test target shape.
- Classification prints accuracy and probability shape; regression prints train/test R2.
- `sprint_statistics()` and a small `leaderboard()` table print. Treat dummy-only or no successful runs as a warning to increase budgets rather than as model quality evidence.
