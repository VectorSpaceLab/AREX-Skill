# Datalab API reference

## Constructor

```python
Datalab(data, task="classification", label_name=None, image_key=None, verbosity=1)
```

| Argument | Meaning |
| --- | --- |
| `data` | Dataset-like object: `datasets.Dataset`, `pandas.DataFrame`, `dict`, `list[dict]`, local path, or Hugging Face dataset id. |
| `task` | One of `classification`, `regression`, or `multilabel`. |
| `label_name` | Name of the label column. Omit only for unlabeled audits. |
| `image_key` | Hugging Face dataset column containing PIL images. Enables CleanVision checks. |
| `verbosity` | `0` to `4`; higher values print more detail during auditing. |

Notes:
- Public callers usually pass the task as a string.
- The internal `Task` enum uses the same three values: `classification`, `regression`, `multilabel`.
- `image_key` is only supported for `datasets.Dataset` inputs.

## `find_issues`

```python
lab.find_issues(*, pred_probs=None, features=None, knn_graph=None, issue_types=None) -> None
```

This method mutates the `Datalab` object in place.
It updates:
- `lab.issues`
- `lab.issue_summary`
- `lab.info`

### Inputs

| Argument | Meaning |
| --- | --- |
| `pred_probs` | Model outputs. Classification and multilabel expect 2D arrays; regression expects a 1D prediction vector. |
| `features` | 2D feature matrix or embedding matrix for the dataset. |
| `knn_graph` | Square CSR distance matrix. Takes precedence over `features` when both are supplied. |
| `issue_types` | Dict mapping issue names to constructor kwargs. Use `None` for the task default set. Use `{}` to run nothing. |

### `pred_probs` shapes

- **Classification:** 2D probabilities with shape `(N, K)` and columns ordered to match lexicographically sorted class names.
- **Regression:** 1D predictions with shape `(N,)`.
- **Multilabel:** 2D probabilities with shape `(N, K)`.

### Task-level default checks

| Task | Base default checks in this release | Notes |
| --- | --- | --- |
| Classification | `null`, `label`, `outlier`, `near_duplicate`, `non_iid`, `class_imbalance`, `underperforming_group` | `data_valuation` is supported and can be requested explicitly. |
| Regression | `null`, `label`, `outlier`, `near_duplicate`, `non_iid` | `pred_probs` means 1D predictions. No class imbalance or underperforming group checks. |
| Multilabel | `null`, `label`, `outlier`, `near_duplicate`, `non_iid` | `label` uses multilabel probabilities. |

### Behavior notes

- `issue_types=None` means run the task default set.
- `issue_types={}` is a no-op and emits a warning.
- If labels are missing, label-based checks may be skipped.
- Some default issue types are conditional: for example, `underperforming_group` needs `pred_probs` plus one of `features`, `knn_graph`, or `cluster_ids`.
- If both `features` and `knn_graph` are given, the precomputed graph wins.
- The multilabel `data_valuation` registry entry is currently fragile because the manager expects NumPy labels; check the troubleshooting note before relying on it.

## Readout methods

### `report`

```python
lab.report(
    num_examples=5,
    verbosity=None,
    include_description=True,
    show_summary_score=False,
    show_all_issues=False,
)
```

- Prints a report to stdout; returns `None`.
- `show_summary_score=True` keeps the dataset-level severity score column in the summary.
- `show_all_issues=True` includes issue types even when `num_issues == 0`.
- `verbosity` overrides the constructor verbosity for that call.

### `get_issues`

```python
lab.get_issues(issue_name=None) -> pandas.DataFrame
```

- `None` returns the combined per-example issue table.
- A name like `"label"` returns just the columns for that issue type.
- Label issues add `given_label` and `predicted_label`.
- Near-duplicate issues add `near_duplicate_sets` and `distance_to_nearest_neighbor`.
- Class-imbalance issues add `given_label`.
- Raises if the requested issue was not run successfully.

### `get_issue_summary`

```python
lab.get_issue_summary(issue_name=None) -> pandas.DataFrame
```

- `None` returns the full summary table.
- A name returns the matching row.
- Lower `score` values mean a more severe issue overall.
- Do not compare scores across different issue types.

### `get_info`

```python
lab.get_info(issue_name=None) -> dict
```

- Returns the stored metadata for one issue type or the full `info` dict.
- `spurious_correlations` is returned here, not in `issue_summary`.

## Issue-type helpers

- `list_possible_issue_types()` returns every issue type the current task can run.
- `list_default_issue_types()` returns the base default set for the current task.
- When `image_key` is set, both helpers also include CleanVision image issue names.

## Persistence

```python
lab.save(path, force=False)
Datalab.load(path, data=None)
```

- `save()` writes the audit state to a folder.
- `load()` restores the audit state.
- The original dataset must be supplied again on load.
