# API reference

This sub-skill covers the stable public classification path for binary and multiclass noisy-label workflows.
Keep `multi_label=False` for the direct route here.

## 1) `CleanLearning`

Constructor:

```python
CleanLearning(
    clf=None,
    *,
    seed=None,
    cv_n_folds=5,
    converge_latent_estimates=False,
    pulearning=None,
    find_label_issues_kwargs={},
    label_quality_scores_kwargs={},
    verbose=False,
    low_memory=False,
)
```

What it does:

- wraps an sklearn-compatible classifier
- computes out-of-sample `pred_probs` when needed
- finds and caches label issues
- prunes label issues and fits the final classifier on the cleaned data

Important validation behavior:

- `clf` must define `fit`, `predict_proba`, and `predict`.
- `score` is optional; if missing, cleanlab falls back to accuracy.
- `labels` must be zero-based integers for the standard route.
- `pred_probs` must be shaped `(N, K)` and aligned to label indices.
- `sample_weight` is only allowed if the estimator supports it.
- `clf_kwargs` must not contain `sample_weight`; pass that directly to `fit` or via `clf_final_kwargs`.
- `low_memory=True` routes label finding through the batched helper and ignores `thresholds`, `noise_matrix`, and `inverse_noise_matrix`.
- `find_label_issues_kwargs` should be used for options such as `min_examples_per_class`, `filter_by`, `frac_noise`, or `n_jobs`.

`fit` signature:

```python
fit(
    X,
    labels=None,
    *,
    pred_probs=None,
    thresholds=None,
    noise_matrix=None,
    inverse_noise_matrix=None,
    label_issues=None,
    sample_weight=None,
    clf_kwargs={},
    clf_final_kwargs={},
    validation_func=None,
    y=None,
)
```

`find_label_issues` signature:

```python
find_label_issues(
    X=None,
    labels=None,
    *,
    pred_probs=None,
    thresholds=None,
    noise_matrix=None,
    inverse_noise_matrix=None,
    save_space=False,
    clf_kwargs={},
    validation_func=None,
)
```

Returned label-issue DataFrame columns:

- `is_label_issue`
- `label_quality`
- `given_label`
- `predicted_label`
- `sample_weight` when automatic reweighting is available and used

Common pitfalls:

- `cv_n_folds` must not exceed the number of examples available per class.
- `pulearning` is only for binary classification when one class is known to be perfectly labeled.
- `validation_func` is only a fold-time adapter for estimators that need validation kwargs.
- `save_space()` removes non-sklearn state, including cached issue tables.

## 2) Direct issue finding and ranking

Public functions:

- `cleanlab.filter.find_label_issues(labels, pred_probs, ...)`
- `cleanlab.count.num_label_issues(labels, pred_probs, ...)`
- `cleanlab.rank.get_label_quality_scores(labels, pred_probs, ...)`
- `cleanlab.rank.get_label_quality_ensemble_scores(labels, pred_probs_list, ...)`
- `cleanlab.rank.order_label_issues(label_issues_mask, labels, pred_probs, ...)`
- `cleanlab.rank.find_top_issues(quality_scores, top=10)`

`find_label_issues` notes:

- Standard route uses `multi_label=False`.
- `return_indices_ranked_by` can be `self_confidence`, `normalized_margin`, or `confidence_weighted_entropy`.
- `filter_by` options include `prune_by_noise_rate`, `prune_by_class`, `both`, `confident_learning`, `predicted_neq_given`, `low_normalized_margin`, and `low_self_confidence`.
- `n_jobs=1` is the safest choice when multiprocessing causes trouble.

`num_label_issues` notes:

- `estimation_method='off_diagonal'` is the usual count estimate.
- `off_diagonal_calibrated` is more conservative and often preferable on tiny class counts.
- `off_diagonal_custom` uses a supplied confident joint.

`get_label_quality_scores` notes:

- methods: `self_confidence`, `normalized_margin`, `confidence_weighted_entropy`
- `adjust_pred_probs=True` is supported for the first two methods only
- lower scores indicate more likely label problems

## 3) Dataset health helpers

Public functions:

- `cleanlab.dataset.rank_classes_by_label_quality(...)`
- `cleanlab.dataset.find_overlapping_classes(...)`
- `cleanlab.dataset.overall_label_health_score(...)`
- `cleanlab.dataset.health_summary(...)`

What they return:

- `rank_classes_by_label_quality`: class-level DataFrame ordered by label quality.
- `find_overlapping_classes`: class-pair DataFrame that estimates which classes are often confused.
- `overall_label_health_score`: a single number in `[0, 1]`.
- `health_summary`: a dict with `overall_label_health_score`, `joint`, `classes_by_label_quality`, and `overlapping_classes`.

Important note:

- If the user wants a dataset audit that spans multiple issue types, do not stretch this route; point them to `datalab`.

## 4) Cross-validated probabilities and latent estimation

Public functions:

- `cleanlab.count.compute_confident_joint(labels, pred_probs, ...)`
- `cleanlab.count.calibrate_confident_joint(confident_joint, labels, ...)`
- `cleanlab.count.estimate_joint(labels, pred_probs, ...)`
- `cleanlab.count.estimate_latent(confident_joint, labels, ...)`
- `cleanlab.count.estimate_py_and_noise_matrices_from_probabilities(labels, pred_probs, ...)`
- `cleanlab.count.estimate_cv_predicted_probabilities(X, labels, ...)`
- `cleanlab.count.estimate_noise_matrices(X, labels, ...)`
- `cleanlab.count.estimate_py_noise_matrices_and_cv_pred_proba(X, labels, ...)`
- `cleanlab.count.get_confident_thresholds(labels, pred_probs, ...)`

Return shapes to remember:

- `estimate_cv_predicted_probabilities` -> `(N, K)` predicted probabilities.
- `compute_confident_joint` -> `(K, K)` confident joint.
- `estimate_latent` -> `(py, noise_matrix, inverse_noise_matrix)`.
- `estimate_py_noise_matrices_and_cv_pred_proba` -> `(py, noise_matrix, inverse_noise_matrix, confident_joint, pred_probs)`.

Internal latent-algebra helpers exist in cleanlab's implementation, but they are not the normal operating route. Prefer the public `cleanlab.count.*` functions above. Only inspect internal helpers when maintaining cleanlab itself or debugging a version-specific inconsistency, and do not make a user workflow depend on them.

## 5) Benchmarking noise generation

Public functions:

- `cleanlab.benchmarking.noise_generation.noise_matrix_is_valid(noise_matrix, py, ...)`
- `cleanlab.benchmarking.noise_generation.generate_noise_matrix_from_trace(...)`
- `cleanlab.benchmarking.noise_generation.generate_noisy_labels(true_labels, noise_matrix)`

Notes:

- `generate_noise_matrix_from_trace(..., valid_noise_matrix=True)` requires `trace > 1`.
- For `K > 2`, `py` should be provided when asking for a valid matrix.
- These helpers are for deterministic synthetic smoke tests and benchmark fixtures.

## 6) Classification-support utilities

- `cleanlab.data_valuation.data_shapley_knn(labels, features=..., knn_graph=..., metric=..., k=...)`
- `cleanlab.rank.find_top_issues(...)` when you already have quality scores
- `cleanlab.rank.get_label_quality_ensemble_scores(...)` when combining several model outputs

Keep this as the main public classification route; only hand off to the specialized sub-skills when the problem statement clearly leaves this scope.
