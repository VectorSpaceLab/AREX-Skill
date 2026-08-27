# SklearnTuner troubleshooting

## Dependency and import failures

### `Please install sklearn before using the SklearnTuner.`

`SklearnTuner` checks the module at construction time. Install scikit-learn in
the same environment that runs KerasTuner, then recreate the tuner:

```bash
python -m pip install scikit-learn
```

If Bayesian optimization is also being installed through KerasTuner's extras,
use the project's optional dependency set that includes the Bayesian and
scikit-learn packages. Verify with:

```bash
python -c "import sklearn, keras_tuner; print(sklearn.__version__)"
```

### DataFrame support is unavailable

pandas is optional. NumPy arrays work without pandas, but DataFrame inputs
require pandas to be importable by the tuner module:

```bash
python -m pip install pandas
```

Convert both `X` and `y` to NumPy if DataFrame semantics are not needed.

## Input and split failures

### Expected NumPy or DataFrame error

Symptoms include an error containing `Expected the data to be numpy.ndarray or
pandas.DataFrame`. `split_data` accepts only those two types because each fold
is sliced by array indexing or `DataFrame.iloc`. Convert lists before search:

```python
X = np.asarray(X)
y = np.asarray(y)
tuner.search(X, y)
```

Also check that `X`, `y`, `sample_weight`, and `groups` have the same number of
rows. The base tuner can wrap a fold-time type error as a trial/search runtime
error, so inspect the original error in the trial message.

### Group splitter rejects the search

Pass `groups` whenever the splitter needs it:

```python
cv = model_selection.GroupKFold(n_splits=5)
tuner = keras_tuner.SklearnTuner(..., cv=cv)
tuner.search(X, y, groups=groups)
```

Use at least as many distinct groups as folds. Do not pass per-row group labels
that leak the same logical group into train and test; the splitter, not the
factory, controls this boundary.

### Stratification or fold-size errors

`StratifiedKFold` needs enough examples in each class for every fold.
`KFold`/`GroupKFold` also require enough samples/groups. Reduce `n_splits` or
supply a fixture with adequate class and group coverage. The default is five
shuffled KFold splits, not stratified splits.

## Scoring and weighting failures

### Trials compare incompatible scores

With `scoring=None`, each estimator's `model.score` is used. Different model
families may therefore optimize different default metrics. Pass one explicit
`sklearn.metrics.make_scorer(...)` callable and keep the Oracle objective
exactly `Objective("score", "max")`.

### `sample_weight` is ignored by a pipeline

The implementation intentionally omits `sample_weight` when the returned model
is an `sklearn.pipeline.Pipeline`, and also omits it when `fit` does not expose
that parameter. This prevents an unsupported keyword error but means weights
are not automatically forwarded to the final pipeline step. Verify weighted
behavior with a custom wrapper or a direct estimator if it is required.

### Scorer or metric rejects `sample_weight=None`

The tuner passes the test weight value to the scorer and configured metrics,
including `None` when no weights were supplied. Use standard scikit-learn
scorers/metrics that accept the conventional optional argument, or provide a
callable compatible with `(estimator, X, y, sample_weight=...)` for `scoring`.

## Factory and persistence failures

### A trial fails during `build` or `fit`

Confirm every conditional branch returns a valid scikit-learn estimator and
that branch-only hyperparameters are declared inside the matching conditional
scope. Check estimator constraints such as `n_neighbors <=` the training fold
size and set sufficient `max_iter` for iterative estimators.

### Best model cannot be restored

Each trial expects `model.pickle` under its trial directory. Check that the
search directory is writable and that the trial completed. Restore requires
pickle-compatible estimator state and importable custom classes/functions in
the current process. Do not move or rename the trial directory between search
and `get_best_models()`.

The restored estimator is the model from the final CV fold, not a full-data
refit. Refit explicitly on all training data when that distinction matters.

### Hyperband or objective errors

Use a non-neural Oracle such as `BayesianOptimizationOracle` and optimize
`Objective("score", "max")`. `Hyperband` injects neural training-budget
parameters and is not supported for this estimator-oriented tuner.
