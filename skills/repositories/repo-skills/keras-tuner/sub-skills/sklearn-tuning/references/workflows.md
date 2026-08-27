# SklearnTuner workflows

These patterns are intentionally small. Start with the bundled
[`scripts/smoke_sklearn.py`](../scripts/smoke_sklearn.py) before scaling up.

## 1. Conditional estimator factory

Use one parent choice and conditional scopes for parameters that only apply to
one estimator. Every branch must return an object implementing the scikit-learn
`fit`, `predict`, and (for the default scoring path) `score` protocol.

```python
from sklearn import ensemble, linear_model


def build_model(hp):
    family = hp.Choice("family", ["logistic", "forest"])
    if family == "logistic":
        with hp.conditional_scope("family", "logistic"):
            return linear_model.LogisticRegression(
                C=hp.Float("C", 0.1, 10.0, sampling="log"),
                max_iter=200,
            )
    with hp.conditional_scope("family", "forest"):
        return ensemble.RandomForestClassifier(
            n_estimators=hp.Int("n_estimators", 10, 30, step=10),
            max_depth=hp.Int("max_depth", 2, 6),
            random_state=7,
        )
```

Do not read branch-only hyperparameters outside their active branch. Keep
estimator defaults deterministic where possible so trial differences reflect
hyperparameters rather than random seeds.

## 2. Explicit objective and consistent scoring

Use a non-neural Oracle and optimize the exact metric name returned by
`SklearnTuner`:

```python
import keras_tuner
from sklearn import metrics

oracle = keras_tuner.oracles.BayesianOptimizationOracle(
    objective=keras_tuner.Objective("score", "max"),
    max_trials=8,
)
tuner = keras_tuner.SklearnTuner(
    oracle=oracle,
    hypermodel=build_model,
    scoring=metrics.make_scorer(metrics.balanced_accuracy_score),
    directory="artifacts",
    project_name="sklearn-demo",
)
```

The explicit scorer is important when `family` spans estimators whose
`model.score` defaults are not semantically identical. `metrics=` may report
additional metrics, but those values do not choose the best trial. Never use
`Hyperband` for this route.

## 3. Custom stratified or group CV

Choose a splitter that matches the sampling design:

```python
from sklearn import model_selection

cv = model_selection.StratifiedKFold(
    n_splits=4, shuffle=True, random_state=11
)
# For grouped observations instead:
cv = model_selection.GroupKFold(n_splits=4)

tuner.search(X, y, groups=groups)  # required for GroupKFold
```

When `cv` is omitted, the implementation uses
`KFold(5, shuffle=True, random_state=1)`. For group-aware CV, ensure there are
at least as many distinct groups as splits and pass a group label per sample.
The tuner forwards `groups` to the splitter; it does not validate or create
those labels for you.

## 4. Sample weights

Pass one weight per sample:

```python
weights = np.asarray(weights, dtype=float)
tuner.search(X, y, sample_weight=weights)
```

The tuner slices train and test weights with the same fold indices. A normal
estimator whose `fit` signature advertises `sample_weight` receives the train
weights. The test weights are passed to `model.score` or the explicit scorer.
Additional metrics also receive test weights. Pipelines and estimators without
that fit parameter are fit without weights; do not assume a pipeline forwards
weights automatically.

If weighted fitting through a pipeline is required, test the behavior against
the installed scikit-learn version and consider a custom estimator wrapper or
an explicit pipeline design rather than assuming `SklearnTuner` will route
`step__sample_weight`.

## 5. NumPy and DataFrame inputs

NumPy is the least-dependency path:

```python
X = np.asarray(X, dtype=float)
y = np.asarray(y)
tuner.search(X, y)
```

DataFrames are also accepted for both `X` and `y` when pandas is installed:

```python
X_df = pd.DataFrame(X, columns=["f0", "f1", "f2"])
y_df = pd.DataFrame({"label": y})
tuner.search(X_df, y_df)
```

The implementation preserves DataFrame row selection through `.iloc`. Keep
feature names and dtypes consistent across the eventual deployment path.
Python lists, tuples, and arbitrary containers are outside the accepted
contract and should be converted before calling `search`.

## 6. Inspect and restore

After search, inspect the objective and restore the best artifact:

```python
best_trial = tuner.oracle.get_best_trials()[0]
best_model = tuner.get_best_models(num_models=1)[0]
assert best_trial.metrics.exists("score")
assert best_model is not None
```

A trial directory contains `model.pickle`. Treat restore as a compatibility
check: the same estimator class and importable custom code must be available.
Evaluate the restored model on a held-out split rather than treating the CV
score alone as an unbiased deployment estimate. Remember that the serialized
model is from the last CV fold; retrain on all available training data if the
application requires a full-data final fit.
