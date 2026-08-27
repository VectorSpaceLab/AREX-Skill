# Workflows

This router is for direct outlier scoring only. If you want a broader audit with multiple issue types, use `datalab` instead.

## 1) Score feature embeddings

Use this when you already have numeric representations of each example.

```python
from cleanlab.outlier import OutOfDistribution
from cleanlab.rank import find_top_issues

ood = OutOfDistribution(params={"k": 10})
train_scores = ood.fit_score(features=train_features)

ood.fit(features=train_features)
test_scores = ood.score(features=test_features)
worst_idx = find_top_issues(test_scores, top=20)
```

Guidance:
- Keep features numeric and 2D.
- Use the returned scores as atypicality scores: smaller means more out-of-distribution.
- If you want a simple cutoff, choose a percentile from a clean reference score distribution.

## 2) Score classifier probabilities

Use this when you already have model `pred_probs`.

```python
from cleanlab.outlier import OutOfDistribution
from cleanlab.rank import find_top_issues

ood = OutOfDistribution()
train_scores = ood.fit_score(pred_probs=train_pred_probs, labels=train_labels)

ood.fit(pred_probs=train_pred_probs, labels=train_labels)
test_scores = ood.score(pred_probs=test_pred_probs)
worst_idx = find_top_issues(test_scores, top=20)
```

Guidance:
- Leave `adjust_pred_probs=True` when you want class-imbalance correction.
- Set `adjust_pred_probs=False` when you do not want to supply labels.
- `method="entropy"` is the default uncertainty score; `least_confidence` is the simplest max-softmax variant.

## 3) Rank the worst points

`cleanlab.rank.find_top_issues(scores, top=n)` sorts the lowest scores first.

- Pass the outlier score vector directly to get the most atypical points.
- If you ever want the most typical points, invert the scores before ranking.
- This is the same shared rank helper used by classification workflows.

## 4) When to switch to Datalab

Use Datalab’s outlier issue check when you want:

- outliers plus label issues or duplicates in the same audit,
- a dataset-level report and issue summary,
- `is_outlier_issue` flags in a combined workflow.

Datalab uses the same core outlier ideas, but this sub-skill stays focused on the direct `OutOfDistribution` API.
