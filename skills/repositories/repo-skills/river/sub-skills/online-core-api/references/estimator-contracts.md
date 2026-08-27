# Estimator contracts

River works on data streams made of one sample at a time. A sample is usually a dictionary of features, and feature names must be hashable. Classification targets are `bool`, `str`, or `int`. Regression targets are numeric. Drift detectors consume scalar values, and anomaly detectors score feature dictionaries.

## Lifecycle matrix

| Family | Update method | Inference method | Return contract | Cold-start note |
| --- | --- | --- | --- | --- |
| `Estimator` | shared root for the concrete families below | shared root for the concrete families below | no standalone inference contract | type-based dispatch and checks use this root |
| `Classifier` | `learn_one(x, y)` | `predict_one(x)`, `predict_proba_one(x)` | learn returns `None`; `predict_proba_one` returns a label-to-probability dict; `predict_one` returns the max-probability label or `None` if the proba dict is empty | a fresh classifier may legally return `None` or `{}` before it has seen any label |
| `Regressor` | `learn_one(x, y)` | `predict_one(x)` | learn returns `None`; prediction is numeric | a fresh regressor usually emits a default numeric value rather than failing |
| `Transformer` | `learn_one(x)` | `transform_one(x)` | learn returns `None`; transform returns a feature dict | many transformers are stateless and keep `learn_one` as a no-op |
| `SupervisedTransformer` | `learn_one(x, y)` | `transform_one(x)` | learn returns `None`; transform returns a feature dict | still often stateless at the base level |
| `Clusterer` | `learn_one(x)` | `predict_one(x)` | learn returns `None`; prediction is an integer cluster id | a fresh clusterer may still assign the sample to an initial cluster |
| `AnomalyDetector` | `learn_one(x)` | `score_one(x)` | learn returns `None`; score is a float | a fresh detector can return a low or zero score until it has seen data |
| `SupervisedAnomalyDetector` | `learn_one(x, y)` | `score_one(x, y)` | learn returns `None`; score is a float | supervised anomaly scoring still uses the same mutating update pattern |
| `DriftDetector` | `update(x)` | `drift_detected`, and `warning_detected` on warning variants | update returns `None` | not part of the `Estimator` harness; use a manual smoke |

## Mini-batch counterparts

| Family | Batch input | Methods | Notes |
| --- | --- | --- | --- |
| `MiniBatchClassifier` | `X` plus `y` | `learn_many(X, y)`, `predict_many(X)`, `predict_proba_many(X)` | `predict_many` falls back to `predict_proba_many(...).idxmax(axis="columns")` when probabilities are available |
| `MiniBatchRegressor` | `X` plus `y` | `learn_many(X, y)`, `predict_many(X)` | batch predictions should agree with row-by-row predictions |
| `MiniBatchTransformer` | `X` | `learn_many(X)`, `transform_many(X)` | `learn_many` is often a no-op for stateless transformers |
| `MiniBatchSupervisedTransformer` | `X` plus `y` | `learn_many(X, y)`, `transform_many(X)` | batch and single-sample behavior should match closely |

Concrete mini-batch implementations in the current codebase use DataFrame/Series-like inputs and often accept pandas or other Narwhals-backed eager frames. The optional pandas extra is what unlocks the batch checks in the automated harness.

## State and return rules

- `learn_one`, `learn_many`, and `update` mutate estimator state in place.
- In the core API, those mutators are documented as returning `None`.
- Inference methods should not mutate the caller's input dictionary.
- If a method is not supported, raising `NotImplementedError` is preferable to returning a misleading value.
- A classifier's `predict_one` default path uses `predict_proba_one` and returns the argmax label when probabilities are available.

## Cold-start behavior

A cold classifier is allowed to be undecided. The canonical example is `dummy.NoChangeClassifier`:

```python
from river import dummy

model = dummy.NoChangeClassifier()

x = {"x": 1}
assert model.predict_one(x) is None
assert model.predict_proba_one(x) == {}
```

After the first label arrives, the same model starts returning a concrete label and a probability map that still includes every label it has seen.

Other families have their own cold-start conventions. For example, `preprocessing.StandardScaler` can transform a fresh sample immediately, `anomaly.HalfSpaceTrees` returns a zero score before its first window is ready, and `drift.ADWIN` starts with `drift_detected == False`.

## Clone, mutation, and testing hooks

- `clone()` returns a fresh estimator of the same class with the same constructor parameters and no learned state.
- `clone(new_params)` overlays a parameter tree onto the current one, including nested estimators.
- `mutate(new_attrs)` modifies state in place, but only for attributes listed in `_mutable_attributes`.
- `_unit_test_params()` yields constructor keyword dictionaries for test instantiation.
- `_unit_test_skips()` yields named checks that are genuinely inapplicable.
- `_tags` is a set assembled from `_more_tags()` and the method-resolution order.
- `_multiclass` is a boolean on classifiers.
- `_supervised` tells the pipeline and check harness whether a target is expected during learning.

## Pipeline unwrap note

`EstimatorMeta.__instancecheck__` unwraps pipeline-like objects through their `_last_step`. That is why a pipeline ending in a classifier behaves like a classifier in `isinstance` checks.

```python
from river import base, compose, linear_model, preprocessing

model = preprocessing.StandardScaler() | linear_model.LogisticRegression()
assert isinstance(model, base.Classifier)
```
