# API reference

## Core learner constructors

| Object | Signature | What it is for | Key notes |
| --- | --- | --- | --- |
| `ActiveLearner` | `ActiveLearner(estimator, query_strategy=uncertainty_sampling, X_training=None, y_training=None, bootstrap_init=False, on_transformed=False, **fit_kwargs)` | Single-model active learning for classification or regression-style workflows. | The estimator must expose `fit` and `predict`. Add `predict_proba` when the query strategy needs probabilities. `bootstrap_init=True` bootstraps the first fit. |
| `Committee` | `Committee(learner_list, query_strategy=vote_entropy_sampling, on_transformed=False)` | Query-by-committee classification ensemble. | `learner_list` must be a Python list of fitted `ActiveLearner`s. `classes_` becomes the union of learner class labels. |
| `CommitteeRegressor` | `CommitteeRegressor(learner_list, query_strategy=max_std_sampling, on_transformed=False)` | Ensemble regression with disagreement measured by prediction spread. | Use regressors with `predict`. `predict(return_std=True)` returns ensemble mean and std. |

## ActiveLearner methods

| Method | Signature | Returns | Notes |
| --- | --- | --- | --- |
| `query` | `query(X_pool, *query_args, return_metrics=False, **query_kwargs)` | `(query_idx, query_rows)` or `(query_idx, query_rows, metrics)` | The query strategy may return only indices or `(indices, metrics)`. If metrics are unavailable, the learner warns and returns `None` in the metrics slot. |
| `teach` | `teach(X, y, bootstrap=False, only_new=False, **fit_kwargs)` | `None` | Appends the new batch to stored history unless `only_new=True`. `bootstrap=True` refits on a bootstrap sample. |
| `fit` | `fit(X, y, bootstrap=False, **fit_kwargs)` | `self` | Replaces stored training history. |
| `predict` | `predict(X, **predict_kwargs)` | Estimator predictions | Delegates to the wrapped estimator. |
| `predict_proba` | `predict_proba(X, **predict_proba_kwargs)` | Class probabilities | Required by uncertainty, entropy, and disagreement strategies that use probabilities. |
| `score` | `score(X, y, **score_kwargs)` | Estimator score | Delegates to `estimator.score`. |

## Committee methods

| Method | Signature | Returns | Notes |
| --- | --- | --- | --- |
| `query` | `query(X_pool, return_metrics=False, *query_args, **query_kwargs)` | `(query_idx, query_rows)` or triple with metrics | Same return-metrics rule as `ActiveLearner.query`. |
| `teach` | `teach(X, y, bootstrap=False, only_new=False, **fit_kwargs)` | `None` | Updates every learner. `only_new=True` applies to every learner in the committee. |
| `fit` | `fit(X, y, **fit_kwargs)` | `self` | Replaces the history of every learner. |
| `rebag` | `rebag(**fit_kwargs)` | `None` | Bootstraps each learner from its own stored history. There is no public `bag()` method in this release. |
| `vote` | `vote(X, **predict_kwargs)` | `(n_samples, n_learners)` | Raw learner predictions. |
| `vote_proba` | `vote_proba(X, **predict_proba_kwargs)` | `(n_samples, n_learners, n_classes)` | Learner probabilities aligned to `committee.classes_`. Missing classes are zero-padded before averaging. |
| `predict_proba` | `predict_proba(X, **predict_proba_kwargs)` | `(n_samples, n_classes)` | Mean of `vote_proba` across learners. |
| `predict` | `predict(X, **predict_proba_kwargs)` | `(n_samples,)` | Picks the argmax over consensus probabilities. |
| `score` | `score(X, y, sample_weight=None)` | Accuracy | Uses `sklearn.metrics.accuracy_score`, not the wrapped estimator score. |

## CommitteeRegressor methods

| Method | Signature | Returns | Notes |
| --- | --- | --- | --- |
| `query` | `query(X_pool, return_metrics=False, *query_args, **query_kwargs)` | `(query_idx, query_rows)` or triple with metrics | Default strategy is `max_std_sampling`. |
| `teach` | `teach(X, y, bootstrap=False, only_new=False, **fit_kwargs)` | `None` | Same history semantics as `ActiveLearner` and `Committee`. |
| `fit` | `fit(X, y, **fit_kwargs)` | `self` | Replaces stored history. |
| `rebag` | `rebag(**fit_kwargs)` | `None` | Bootstraps each learner from its own stored history. |
| `vote` | `vote(X, **predict_kwargs)` | `(n_samples, n_learners)` | Raw learner predictions. |
| `predict` | `predict(X, return_std=False, **predict_kwargs)` | Mean or `(mean, std)` | `return_std=True` gives ensemble spread across learner predictions. |

## Estimator requirements by workflow

| Workflow | Minimum wrapped estimator API | Extra requirement when used with... |
| --- | --- | --- |
| `ActiveLearner` classification | `fit`, `predict` | `predict_proba` for uncertainty, entropy, disagreement, and other probability-based strategies. |
| `ActiveLearner` regression | `fit`, `predict` | A query strategy that works with the regressor output. Some workflows use `predict(return_std=True)` on the estimator or ensemble. |
| `Committee` classification | Every learner needs `fit`, `predict`, `predict_proba` | `vote_proba`, `predict_proba`, vote entropy, consensus entropy, and max disagreement. |
| `CommitteeRegressor` | Every learner needs `fit`, `predict` | `predict(return_std=True)` on the committee for std-based querying and diagnostics. |

## Single-row shape contract

| Source container | Safe way to teach one row | Safe way to keep one label |
| --- | --- | --- |
| NumPy array | `X_pool[idx].reshape(1, -1)` | `y_pool[idx].reshape(1,)` |
| Pandas DataFrame | `X_pool.iloc[[idx]]` | `y_pool.iloc[[idx]]` |
| Python list | convert to NumPy or pass a one-row nested list | keep one label in a 1-element array or list |

If the learner already stored a 2D target array, keep the replacement label in the same shape.

## `on_transformed`

- Use `on_transformed=True` when the query strategy needs transformed features.
- The learner or committee should wrap a transformable pipeline or ensemble.
- `transform_without_estimating(X)` applies the preprocessing part of the pipeline and skips the final estimator.
- For committees, transformed feature blocks from each learner are concatenated.
