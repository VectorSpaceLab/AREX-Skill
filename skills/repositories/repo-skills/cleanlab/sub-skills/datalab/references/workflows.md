# Datalab workflows

## When to choose Datalab

Use Datalab when you want one object to audit a dataset for several issue families at once, then inspect both dataset-level summaries and per-example rows.

Use a narrower sub-skill when the question is only about one family:

- classification → noisy labels, count/filter/rank, dataset health
- outlier → standalone outlier scoring
- multiannotator → consensus / annotator quality
- tabular-label-issues → direct multilabel or regression label issues
- structured-label-issues → token / object detection / segmentation label issues
- experimental → unstable helpers and span classification

## 1. Standard tabular / text / generic classification audit

```python
from cleanlab import Datalab

lab = Datalab(data, label_name="label")
lab.find_issues(
    features=X,
    pred_probs=pred_probs,
    issue_types={
        "label": {},
        "outlier": {"k": 3},
        "near_duplicate": {"k": 3},
        "class_imbalance": {},
        "data_valuation": {"k": 3},
    },
)
lab.report(num_examples=5, verbosity=0, show_summary_score=True)
```

Use this pattern when you want to inspect label quality, geometric outliers, duplicates, class balance, and KNN-Shapley value in one pass.

If you already have slice IDs, add a second pass for the underperforming group check:

```python
lab.find_issues(
    pred_probs=pred_probs,
    issue_types={"underperforming_group": {"cluster_ids": cluster_ids}},
)
```

## 2. Regression audit

```python
lab = Datalab(data, label_name="y", task="regression")
lab.find_issues(
    features=X,
    pred_probs=y_pred,
    issue_types={
        "label": {},
        "outlier": {"k": 3},
        "near_duplicate": {"k": 3},
        "data_valuation": {"k": 3},
    },
)
```

Regression Datalab uses 1D predictions instead of class probabilities.

## 3. Multilabel audit

```python
lab = Datalab(data, label_name="labels", task="multilabel")
lab.find_issues(
    features=X,
    pred_probs=pred_probs,
    issue_types={
        "label": {},
        "outlier": {"k": 3},
        "near_duplicate": {"k": 3},
    },
)
```

Multilabel label issues use `pred_probs` only.

## 4. Image audit with optional CleanVision checks

```python
lab = Datalab(data=dataset, label_name="label", image_key="image")
lab.find_issues(
    issue_types={
        "image_issue_types": {
            "dark": {},
            "blurry": {},
        },
        "spurious_correlations": {"threshold": 0.2},
    }
)
```

Key points:
- `image_issue_types` is the nested dict for CleanVision image checks.
- `spurious_correlations` is separate and only works after image-property scores exist.
- `lab.get_info("spurious_correlations")` is the right place to inspect the correlation table.

## 5. Reusing a precomputed kNN graph

If you already have a sparse kNN graph, pass it directly:

```python
lab.find_issues(knn_graph=knn_graph, issue_types={"outlier": {"k": 3}})
```

This is useful when:
- the feature matrix is large
- the same graph should be reused across several issue types
- you already have approximate neighbors from another system

Remember: when both `features` and `knn_graph` are present, the graph takes precedence.

## 6. Custom IssueManager workflow

1. Subclass `IssueManager`.
2. Define `issue_name`.
3. Populate `self.issues`, `self.summary`, and `self.info`.
4. Register the manager with `register(...)`.
5. Call `lab.find_issues(issue_types={"your_issue": {}})`.
6. Inspect `lab.report()` and `lab.get_issues("your_issue")`.

## 7. Readout strategy

- Start with `lab.report()` for a human-readable overview.
- Use `lab.get_issue_summary()` to compare issue severity across runs of the same issue type.
- Use `lab.get_issues(<issue>)` when you need row-level indices or to join results back to the original dataset.
- Use `lab.get_info(<issue>)` for auxiliary metadata, especially for spurious correlations.
