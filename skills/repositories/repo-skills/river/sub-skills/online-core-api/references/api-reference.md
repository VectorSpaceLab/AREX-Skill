# API reference

This reference summarizes the River core API snapshot verified from the current checkout and the installed API inspection data.

## Verified public method signatures

| Base | Public methods |
| --- | --- |
| `Classifier` | `learn_one(self, x, y) -> None`; `predict_proba_one(self, x, **kwargs) -> dict`; `predict_one(self, x, **kwargs) -> Target | None` |
| `Regressor` | `learn_one(self, x, y) -> None`; `predict_one(self, x) -> RegTarget` |
| `Transformer` | `learn_one(self, x) -> None`; `transform_one(self, x) -> dict` |
| `SupervisedTransformer` | `learn_one(self, x, y) -> None`; `transform_one(self, x) -> dict` |
| `Clusterer` | `learn_one(self, x) -> None`; `predict_one(self, x) -> int` |
| `DriftDetector` | `update(self, x) -> None` |
| `AnomalyDetector` | `learn_one(self, x) -> None`; `score_one(self, x) -> float` |

Mini-batch siblings follow the same pattern with `learn_many`, `predict_many`, `predict_proba_many`, and `transform_many` over DataFrame/Series-like inputs.

## Verified constructor snapshot

| Symbol | Signature snapshot |
| --- | --- |
| `compose.Pipeline` | `(*steps)` |
| `preprocessing.StandardScaler` | `(with_std=True, window_size=None)` |
| `linear_model.LogisticRegression` | `(optimizer=None, loss=None, l2=0.0, l1=0.0, intercept_init=0.0, intercept_lr=0.01, clip_gradient=1000000000000.0, initializer=None)` |
| `cluster.KMeans` | `(n_clusters=5, halflife=0.5, mu=0, sigma=1, p=2, seed=None)` |
| `anomaly.HalfSpaceTrees` | `(n_trees=10, height=8, window_size=250, limits=None, seed=None)` |
| `drift.ADWIN` | `(delta=0.002, clock=32, max_buckets=5, min_window_length=5, grace_period=10)` |

These examples are the most useful core entry points for the online API contract.

## `check_estimator` and `yield_checks`

`river.checks.yield_checks(model)` returns the individual check callables that make up the harness. `river.checks.check_estimator(model)` simply iterates over those checks and runs each one against `model.clone()`, skipping only checks whose names appear in `model._unit_test_skips()`.

The harness starts with general checks and then adds dataset-backed checks according to the estimator family.

| Estimator kind | Dataset-backed checks |
| --- | --- |
| `Classifier` | Phishing; if `_multiclass` is `True` and the model lacks the `POSITIVE_INPUT` tag, ImageSegments is also used |
| `Regressor` | TrumpApproval |
| `Transformer` / `SupervisedTransformer` | TrumpApproval unless the model has the `TEXT_INPUT` tag |
| `AnomalyDetector` | CreditCard |
| `MiniBatchClassifier` / `MiniBatchRegressor` | batch consistency checks when pandas support is available |
| `MiniBatchTransformer` / `MiniBatchSupervisedTransformer` | batch consistency checks when pandas support is available |
| `MultiTargetRegressor` / `MultiLabelClassifier` | specialized dataset branches |
| `Clusterer` | no dedicated dataset branch in the current harness |
| `DriftDetector` | not part of the `Estimator` harness |

That means a new clusterer or drift detector still needs a manual smoke even when `check_estimator` is part of the workflow.

Useful named checks include:

- `check_repr`, `check_str`, and `check_doc`
- `check_tags` and `check_multiclass_is_bool`
- `check_clone_same_class`, `check_clone_is_idempotent`, and `check_clone_is_independent`
- `check_init_has_default_params_for_tests` and `check_init_default_params_are_not_mutable`
- `check_get_params_matches_signature` and `check_clone_with_new_params_applies`
- `check_predict_one_before_any_learn` and `check_predict_one_pure`
- `check_predict_proba_one` and `check_classifier_tracks_seen_labels`
- `check_transform_one`
- `check_learn_many_matches_learn_one`, `check_predict_many_matches_predict_one`, and `check_transform_many_matches_transform_one` when batch support is present

A quick inspection loop looks like this:

```python
from river import checks, preprocessing

model = preprocessing.StandardScaler()
for check in checks.yield_checks(model):
    print(check.__name__)
```

## Type routing and wrapper behavior

River's `Estimator` uses a custom metaclass that unwraps pipeline-like objects through `_last_step`. That is why `isinstance(pipeline, base.Classifier)` is true when the final step is a classifier.

Wrappers also delegate their key capability flags from the wrapped estimator:

- `_tags`
- `_supervised`
- `_multiclass`

The current public tag constants are `TEXT_INPUT` and `POSITIVE_INPUT`. The checker uses them to decide which dataset branches to exercise.
