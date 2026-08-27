# API reference

This sub-skill covers two direct families: multilabel classification and regression.

## Multilabel APIs

### `cleanlab.multilabel_classification.filter.find_label_issues(...)`

```python
find_label_issues(
    labels: list,
    pred_probs: np.ndarray,
    return_indices_ranked_by: Optional[str] = None,
    rank_by_kwargs={},
    filter_by: str = "prune_by_noise_rate",
    frac_noise: float = 1.0,
    num_to_remove_per_class: Optional[List[int]] = None,
    min_examples_per_class=1,
    confident_joint: Optional[np.ndarray] = None,
    n_jobs: Optional[int] = None,
    verbose: bool = False,
    low_memory: bool = False,
) -> np.ndarray
```

- `labels` is a list of lists of zero-based class IDs.
- `pred_probs` is a 2D array with shape `(N, K)`; rows do not need to sum to 1.
- `filter_by` chooses the multilabel pruning route; `predicted_neq_given` is the most literal mismatch check.
- Returns a boolean mask when `return_indices_ranked_by=None`.
- Returns ranked issue indices when `return_indices_ranked_by` is set.

### `cleanlab.multilabel_classification.filter.find_multilabel_issues_per_class(...)`

```python
find_multilabel_issues_per_class(
    labels: list,
    pred_probs: np.ndarray,
    return_indices_ranked_by: Optional[str] = None,
    rank_by_kwargs={},
    filter_by: str = "prune_by_noise_rate",
    frac_noise: float = 1.0,
    num_to_remove_per_class: Optional[List[int]] = None,
    min_examples_per_class=1,
    confident_joint: Optional[np.ndarray] = None,
    n_jobs: Optional[int] = None,
    verbose: bool = False,
    low_memory: bool = False,
)
```

- Returns a `(N, K)` boolean mask when `return_indices_ranked_by=None`.
- Returns `(label_issues_list, labels_list, pred_probs_list)` when ranking is requested.
- Each class is handled one-vs-rest.

### `cleanlab.multilabel_classification.get_label_quality_scores(...)`

```python
get_label_quality_scores(
    labels: List[List[int]],
    pred_probs: np.ndarray,
    *,
    method: str = "self_confidence",
    adjust_pred_probs: bool = False,
    aggregator_kwargs: Dict[str, Any] = {"method": "exponential_moving_average", "alpha": 0.8},
)
```

- Returns one score per example.
- Scores are in `[0, 1]`; lower scores mean more suspect labels.
- Methods: `self_confidence`, `normalized_margin`, `confidence_weighted_entropy`.

### `cleanlab.multilabel_classification.rank.get_label_quality_scores_per_class(...)`

- Returns one score per example per class.
- Output shape matches `pred_probs`.
- Use this when you want per-class annotation quality rather than one aggregate score.

### Dataset-health helpers

- `cleanlab.multilabel_classification.dataset.common_multilabel_issues(...)`
- `cleanlab.multilabel_classification.dataset.rank_classes_by_multilabel_quality(...)`
- `cleanlab.multilabel_classification.dataset.overall_multilabel_health_score(...)`
- `cleanlab.multilabel_classification.dataset.multilabel_health_summary(...)`

`rank_classes_by_multilabel_quality(...)` produces columns such as `Label Issues`, `Inverse Label Issues`, `Label Noise`, `Inverse Label Noise`, and `Label Quality Score`.

## Regression APIs

### `cleanlab.regression.rank.get_label_quality_scores(...)`

```python
get_label_quality_scores(
    labels,
    predictions,
    *,
    method: str = "outre",
)
```

- `labels` and `predictions` are numeric 1D array-like values of the same length.
- `method="outre"` is the default.
- `method="residual"` is the simpler alternative.
- Returns one score per example in `[0, 1]`; lower scores mean a more suspicious numeric target.

### `cleanlab.regression.learn.CleanLearning`

```python
CleanLearning(
    model: Optional[BaseEstimator] = None,
    *,
    cv_n_folds: int = 5,
    n_boot: int = 5,
    include_aleatoric_uncertainty: bool = True,
    verbose: bool = False,
    seed: Optional[bool] = None,
)
```

- Wraps an sklearn-compatible regression model.
- The model should be clonable with `sklearn.base.clone`.
- Use `fit(X, y, label_issues=..., sample_weight=...)` to refit on cleaned data.
- `find_label_issues(X, y, ...)` returns a DataFrame with `is_label_issue`, `label_quality`, `given_label`, and `predicted_label`.
- `score(X, y, sample_weight=None)` delegates to the wrapped model's `score` when available, otherwise falls back to `r2_score`.
- `get_label_issues()` returns the cached issue table, and `save_space()` clears it.

## Datalab cross-reference

- `Datalab(..., task="multilabel")` and `Datalab(..., task="regression")` use the same tabular label semantics but provide the broader audit router.
- Direct modules are the right choice when the only question is label quality or noisy-target refitting.
- Datalab issue rows use `label_score`; regression `CleanLearning` uses `label_quality`.
