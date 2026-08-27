# Strategy reference

## Query contract

- Strategy callables are invoked as `(learner_or_estimator, X_pool, **kwargs)`.
- Valid return forms are:
  - a bare scalar index or index array
  - `(indices, metrics)`
- `BaseLearner.query(..., return_metrics=True)` only forwards metrics when the strategy returns them.
- The shared selectors behave as follows:
  - `multi_argmax`, `multi_argmin`, `shuffled_argmax`, `shuffled_argmin` return `(indices, selected_values)`.
  - `weighted_random` returns indices only.

## Uncertainty family

| Surface | Signature | Return | Notes |
| --- | --- | --- | --- |
| `classifier_uncertainty` | `(classifier, X, **predict_proba_kwargs)` | `np.ndarray` | `1 - max(p)`; unfitted classifiers return all ones. |
| `classifier_margin` | `(classifier, X, **predict_proba_kwargs)` | `np.ndarray` | Smaller margins are less certain; unfitted classifiers and single-class outputs return zeros. |
| `classifier_entropy` | `(classifier, X, **predict_proba_kwargs)` | `np.ndarray` | Unfitted classifiers return zeros. |
| `uncertainty_sampling` | `(classifier, X, n_instances=1, random_tie_break=False, **kwargs)` | `(indices, values)` | Uses `multi_argmax` unless `random_tie_break=True`, then `shuffled_argmax`. |
| `margin_sampling` | `(classifier, X, n_instances=1, random_tie_break=False, **kwargs)` | `(indices, values)` | Uses `multi_argmin` because smaller margin is better. |
| `entropy_sampling` | `(classifier, X, n_instances=1, random_tie_break=False, **kwargs)` | `(indices, values)` | Uses `multi_argmax`. |

## Disagreement family

| Surface | Signature | Return | Notes |
| --- | --- | --- | --- |
| `vote_entropy` | `(committee, X, **predict_proba_kwargs)` | `np.ndarray` | Needs a fitted committee; unfitted committees return zeros. |
| `consensus_entropy` | `(committee, X, **predict_proba_kwargs)` | `np.ndarray` | Averages committee probabilities before entropy. |
| `KL_max_disagreement` | `(committee, X, **predict_proba_kwargs)` | `np.ndarray` | Max KL divergence from consensus. |
| `vote_entropy_sampling` | `(committee, X, n_instances=1, random_tie_break=False, **kwargs)` | `(indices, values)` | Wrapper around `vote_entropy`. |
| `consensus_entropy_sampling` | `(committee, X, n_instances=1, random_tie_break=False, **kwargs)` | `(indices, values)` | Wrapper around `consensus_entropy`. |
| `max_disagreement_sampling` | `(committee, X, n_instances=1, random_tie_break=False, **kwargs)` | `(indices, values)` | Wrapper around `KL_max_disagreement`. |
| `max_std_sampling` | `(regressor, X, n_instances=1, random_tie_break=False, **predict_kwargs)` | `(indices, values)` | Requires `predict(..., return_std=True)`; useful for regressors or committee regressors. |

## Batch family

| Surface | Signature | Return | Notes |
| --- | --- | --- | --- |
| `uncertainty_batch_sampling` | `(classifier, X, n_instances=20, metric='euclidean', n_jobs=None, **uncertainty_measure_kwargs)` | `(indices, uncertainty_scores)` | Ranked batch uncertainty helper. |
| `ranked_batch` | `(classifier, unlabeled, uncertainty_scores, n_instances, metric, n_jobs)` | `(indices, uncertainty_scores)` | Uses the training pool to re-rank items after each pick. |
| `select_cold_start_instance` | `(X, metric, n_jobs)` | `(index, row)` | Used when no labeled data exist yet. |
| `select_instance` | `(X_training, X_pool, X_uncertainty, mask, metric, n_jobs)` | `(index, row, mask)` | Internal ranked-batch step helper. |

## Expected-error family

| Surface | Signature | Return | Notes |
| --- | --- | --- | --- |
| `expected_error_reduction` | `(learner, X, loss='binary', p_subsample=1.0, n_instances=1, random_tie_break=False)` | `(indices, values)` | `loss` must be `'binary'` or `'log'`; `p_subsample` must be in `[0, 1]`. It clones and refits the estimator repeatedly, so it is expensive. |

## Density family

| Surface | Signature | Return | Notes |
| --- | --- | --- | --- |
| `similarize_distance` | `(distance_measure)` | callable | Wraps a distance function as `1 / (1 + distance)`. |
| `information_density` | `(X, metric='euclidean')` | `np.ndarray` | Returns the mean similarity of each point to the pool. |

## Multilabel family

| Surface | Signature | Return | Notes |
| --- | --- | --- | --- |
| `SVM_binary_minimum` | `(classifier, X_pool, random_tie_break=False)` | scalar index or selector tuple | Expects `classifier.estimator.estimators_` with `decision_function`. The deterministic branch returns a scalar index. |
| `max_loss` | `(classifier, X_pool, n_instances=1, random_tie_break=False)` | `(indices, values)` | Requires `predict_proba` and `predict`; asserts `len(X_pool) >= n_instances`. |
| `mean_max_loss` | `(classifier, X_pool, n_instances=1, random_tie_break=False)` | `(indices, values)` | Same shape and estimator requirements as `max_loss`. |
| `min_confidence` | `(classifier, X_pool, n_instances=1, random_tie_break=False)` | `(indices, values)` | Selects the smallest minimum confidence. |
| `avg_confidence` | `(classifier, X_pool, n_instances=1, random_tie_break=False)` | `(indices, values)` | Selects the largest average confidence. |
| `max_score` | `(classifier, X_pool, n_instances=1, random_tie_break=1)` | `(indices, values)` | Pass `random_tie_break=False` if you need stable selection. |
| `avg_score` | `(classifier, X_pool, n_instances=1, random_tie_break=False)` | `(indices, values)` | Mean score over labels; used for multilabel ranking. |

## Utility combinators and selectors

| Surface | Signature | Return | Notes |
| --- | --- | --- | --- |
| `make_linear_combination` | `(*functions, weights=None)` | callable | Functions must share the same input signature and output shape. Useful when you want a single utility from several compatible measures. |
| `make_product` | `(*functions, exponents=None)` | callable | Multiplies compatible outputs raised to the given exponents. |
| `make_query_strategy` | `(utility_measure, selector)` | callable | The selector decides whether the strategy returns indices only or `(indices, metrics)`. |
| `multi_argmax` / `multi_argmin` | `(values, n_instances=1)` | `(indices, values)` | Lower-level deterministic selectors. |
| `shuffled_argmax` / `shuffled_argmin` | `(values, n_instances=1)` | `(indices, values)` | Tie-breaking selectors that randomize equal scores. Seed NumPy if you need reproducible ties. |
| `weighted_random` | `(weights, n_instances=1)` | indices | Samples without replacement using normalized weights. |

## Practical notes

- `information_density` is data-only; if you want to mix it with a learner-based utility, wrap it so it accepts `(learner, X_pool)`.
- `classifier_margin` is a loss-like signal, so it is often inverted or normalized before mixing with a positive utility such as density.
- `n_instances` cannot exceed the pool size for the selector helpers that rank a fixed batch.
- `expected_error_reduction` can return `np.array([0])` when the learner is not fitted; fit first if that appears unexpectedly.
