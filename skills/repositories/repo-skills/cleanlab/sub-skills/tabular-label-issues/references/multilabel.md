# Multilabel workflows

Use this route when each example can belong to one or more classes, or to none of them.
The direct multilabel APIs expect list-of-lists labels and class-wise probability columns.

## 1. Normalize the labels

If your source labels are multi-hot rows, convert each row to a list of zero-based class indices before calling the direct APIs.

```python
labels = [np.flatnonzero(row).tolist() for row in multi_hot_labels]
# [] is valid for an example with no labels.
```

`pred_probs` should have shape `(N, K)` and columns must stay aligned to class IDs `0..K-1`.
Unlike multiclass classification, multilabel rows do not need to sum to 1.

## 2. Find suspicious examples

Use `find_label_issues(...)` when you want a dataset-wide mask or ranked indices.
Use `find_multilabel_issues_per_class(...)` when you want to know which class annotation is wrong.
`filter_by="predicted_neq_given"` is a useful direct mismatch route when you want the most obvious label issue to surface in a tiny deterministic example; leave the default when you want the classic confident-learning style pruning.

```python
from cleanlab.multilabel_classification import filter as ml_filter
from cleanlab.multilabel_classification import get_label_quality_scores

issues_mask = ml_filter.find_label_issues(labels, pred_probs)
ranked_issues = ml_filter.find_label_issues(
    labels,
    pred_probs,
    return_indices_ranked_by="self_confidence",
)
per_class_mask = ml_filter.find_multilabel_issues_per_class(labels, pred_probs)
scores = get_label_quality_scores(labels, pred_probs)
```

Lower scores mean more suspect labels.

## 3. Inspect class-level quality

Use the dataset helpers when you want a broader summary of which classes are most problematic.

```python
from cleanlab.multilabel_classification.dataset import (
    common_multilabel_issues,
    multilabel_health_summary,
    overall_multilabel_health_score,
    rank_classes_by_multilabel_quality,
)

class_table = rank_classes_by_multilabel_quality(labels=labels, pred_probs=pred_probs)
issue_table = common_multilabel_issues(labels=labels, pred_probs=pred_probs)
health = overall_multilabel_health_score(labels=labels, pred_probs=pred_probs)
summary = multilabel_health_summary(labels=labels, pred_probs=pred_probs, verbose=False)
```

The most useful readouts are:
- `Label Quality Score` for class ranking
- `Issue Probability` for common issue patterns
- `overall_multilabel_health_score` for a quick dataset-level check

## 4. When to switch to Datalab

Use `Datalab(..., task="multilabel")` when you want a broader audit beyond label issues.
The same multilabel label format still applies, but Datalab also adds other issue types and a report-oriented router.

If you only need label quality, stay on the direct multilabel APIs in this sub-skill.

## 5. Practical reminders

- Keep the class order stable across labels and `pred_probs`.
- Do not normalize multilabel probabilities just to make them sum to 1.
- If you already have a multi-hot matrix, convert it before calling cleanlab.
- If you are actually cleaning standard single-label multiclass data, route to `classification` instead.
