# Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `NotFittedError` from an uncertainty or disagreement strategy | The estimator or committee has not been fitted yet, or a custom wrapper calls `predict_proba` too early. | Fit the learner first. For built-ins, the unfitted fallback often returns zeros or ones; for custom strategies, catch the error or avoid querying before fit. |
| `expected_error_reduction` returns `np.array([0])` | The learner is unfitted or `predict_proba` failed inside the strategy. | Fit the learner, and make sure the estimator supports `predict_proba`. |
| `AttributeError: predict_proba` | The estimator does not expose probability predictions. | Use a probabilistic classifier, calibrate it, or choose a strategy that only needs `predict`, `decision_function`, or `return_std`. |
| `BaseLearner.query(..., return_metrics=True)` has `None` metrics | The strategy returned only indices, or it returned a scalar and the query path retried without metrics. | Return `(indices, metrics)` from the strategy and make sure the selector preserves the metric array. |
| Scalar index vs index-array confusion | `SVM_binary_minimum` and some custom selectors can return a scalar index, while batch selectors usually return arrays. | Decide on one contract before wiring the strategy into downstream code. Remember that a scalar index often yields a 1-D row from `retrieve_rows`, not a 2-D batch. |
| `n_instances` larger than the pool size | The selector helpers assert that the requested batch fits in the pool. | Clamp `n_instances` or refill the pool before querying. |
| Ranked batch or expected-error feels slow | Both methods do extra work per candidate; expected-error clones and refits the estimator repeatedly. | Reduce pool size, use `p_subsample < 1` for expected-error, or switch to a cheaper strategy. |
| Multilabel strategy shape errors | The label matrix is not 2-D, or the chosen estimator does not expose the methods that the strategy needs. | Use a 2-D indicator matrix. `SVM_binary_minimum` needs `classifier.estimator.estimators_` with `decision_function`; the probability-based multilabel scorers need `predict_proba` and `predict`. |
| Random tie order changes between runs | `random_tie_break=True` or an unstable tie in a selector helper. | Seed NumPy before querying, disable tie breaking, or make the utilities non-equal before selection. |
| `max_std_sampling` fails | The regressor does not support `predict(..., return_std=True)`. | Use a Gaussian-process regressor or another regressor that returns standard deviations. |

## Fast checks

- If the strategy is supposed to return metrics, inspect the direct call before wiring it through `learner.query`.
- If the strategy mixes density and uncertainty, make sure every component accepts the same call signature.
- If the strategy is slow, test the same pool with a simpler selector first to confirm the learner itself is healthy.

## Where to read next

- [strategy reference](strategy-reference.md)
- [custom strategies](custom-strategies.md)
- [query smoke script](../scripts/query_strategy_smoke.py)
