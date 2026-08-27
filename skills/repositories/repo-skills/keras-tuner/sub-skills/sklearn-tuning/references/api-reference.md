# SklearnTuner API reference

This reference records behavior verified against the implementation and tests
for this checkout: `keras_tuner/tuners/sklearn_tuner.py` and
`keras_tuner/tuners/sklearn_tuner_test.py`. Keep the implementation details
below in mind when adapting a workflow.

## Constructor and objective

```python
SklearnTuner(
    oracle,
    hypermodel,
    scoring=None,
    metrics=None,
    cv=None,
    **kwargs,
)
```

- `oracle` must be a KerasTuner Oracle that can optimize a non-neural,
  cross-validated score. Configure its objective as
  `keras_tuner.Objective("score", "max")` (equivalently
  `direction="max"`). `BayesianOptimizationOracle` is the tested default
  pattern. Do not use `Hyperband`, whose Oracle behavior is specific to neural
  training budgets.
- `hypermodel` is a `HyperModel` or callable whose `build(hp)` returns a
  scikit-learn estimator or pipeline.
- `scoring=None` calls the estimator's `model.score`. Set an explicit scorer,
  commonly `sklearn.metrics.make_scorer(...)`, when branches return different
  model families so every trial is ranked on the same metric.
- `metrics` is optional. A single metric or list/tuple is accepted; these
  metrics are reported but do not control the search objective.
- `cv=None` creates `sklearn.model_selection.KFold(5, shuffle=True,
  random_state=1)`. Pass a splitter such as `StratifiedKFold` or `GroupKFold`
  when the default does not match the data.

Common constructor options inherited through `**kwargs` include
`directory`, `project_name`, `overwrite`, and the retry settings accepted by
`BaseTuner`.

## Search inputs

```python
search(X, y, sample_weight=None, groups=None)
```

- `X` and `y` must be `numpy.ndarray` or `pandas.DataFrame`. The tuner uses
  NumPy indexing or `DataFrame.iloc` to slice each fold; Python lists are not a
  supported input contract and fail with an expected-data-type error.
- `sample_weight` is optional and should be an array-like vector that supports
  integer-array slicing. The corresponding train/test portions are created for
  each fold. The training portion is passed only when the estimator's
  `fit` signature contains `sample_weight`.
- `groups` is optional and is forwarded to `cv.split(X, y, groups=groups)` when
  provided. Supply it for group-aware splitters such as `GroupKFold`; its
  length must match the samples.

The source implementation builds a fresh estimator for every fold. It averages
`score` and each additional metric over the folds and returns those means to
the Oracle. A `Pipeline` is deliberately fit without a `sample_weight`
argument, even when its final estimator may support one.

## Scoring and metrics

With an explicit `scoring` callable, each fold is evaluated as
`scoring(model, X_test, y_test, sample_weight=sample_weight_test)`. With no
scorer, the equivalent call is `model.score(...)`. Additional metric functions
receive `(y_test, y_test_pred, sample_weight=sample_weight_test)` and are
recorded under each function's `__name__`; they do not affect trial ranking.

For comparable classification branches, prefer a scorer with one metric:

```python
from sklearn import metrics

scoring = metrics.make_scorer(metrics.balanced_accuracy_score)
```

This prevents, for example, a classifier's accuracy-like default and another
estimator's different default from being compared as if they were the same
quantity.

## Persistence and model loading

Each completed trial writes:

```text
<directory>/<project_name>/<trial-id>/model.pickle
```

`save_model(trial_id, model)` uses the package backend's file wrapper and
`pickle.dump`. `load_model(trial)` reads the same file with `pickle.load`, and
`get_best_models()` uses this hook to restore the best trial estimators.
Models must therefore be pickleable, and custom classes/functions referenced by
an estimator must remain importable in the restore environment. The saved model
is the estimator from the last CV fold, not an automatic full-data refit.

## Dependency gates

- scikit-learn is required. The constructor raises `ImportError` with
  `Please install sklearn before using the SklearnTuner.` when it is missing.
- pandas is optional for the NumPy path. If pandas is absent, DataFrame inputs
  cannot satisfy the accepted input contract; install pandas before using
  them.
- NumPy is required by the tuner implementation and by the smoke fixture.

## Evidence-backed test coverage

The repository tests cover NumPy and DataFrame input, explicit scoring and
custom CV, additional metrics, sample weights, pipelines, group-aware CV,
model restoration, missing scikit-learn, and wrong input types. The bundled
[smoke script](../scripts/smoke_sklearn.py) adds a bounded two-trial fixture
with conditional estimator branches, explicit scoring, groups, weights, and a
pickle restore assertion.
