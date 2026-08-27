# Data formats

This sub-skill handles two tabular label patterns: multilabel lists of class IDs and regression numeric targets.

## Multilabel labels

Expected form: `List[List[int]]`

- Each inner list contains the zero-based class IDs that apply to one example.
- The order of the inner list does not matter.
- Use `[]` for an example with no labels.

Example:

```python
multi_hot = np.array([
    [1, 0, 1],
    [0, 1, 0],
    [0, 0, 0],
])
labels = [np.flatnonzero(row).tolist() for row in multi_hot]
# [[0, 2], [1], []]
```

Do not pass a standard multiclass label vector here. Do not pass strings unless you first convert them to integer class IDs.

## Multilabel probabilities

Expected form: `np.ndarray` with shape `(N, K)`.

- Row `i` contains one probability per class for example `i`.
- Columns must line up with class IDs `0..K-1`.
- Rows do not need to sum to 1.
- Keep all `K` columns even if one class never appears in the labels.

If you are using Datalab, verify the class order before aligning `pred_probs` to the task's label encoding.

## Regression targets and predictions

Expected form: numeric 1D array-like values.

- `labels` / `y` is the observed numeric target.
- `predictions` is the out-of-sample regression prediction vector.
- Both must have the same length.
- `X` must have the same number of rows as `y` when you use `CleanLearning`.

Example:

```python
y = np.asarray([3.2, 4.0, 2.7], dtype=float)
y_pred = np.asarray([3.1, 3.8, 2.9], dtype=float)
```

## Sample weights for regression

`sample_weight` is optional, but when you use it:

- it must be 1D,
- it must have the same length as `y`, and
- the wrapped model must accept it.

## Output score semantics

- Multilabel `get_label_quality_scores(...)` returns one score per example.
- Multilabel `get_label_quality_scores_per_class(...)` returns one score per example per class.
- Regression `get_label_quality_scores(...)` returns one score per example.
- Higher scores mean cleaner labels.
- Lower scores mean examples more likely to be mislabeled or corrupted.

## Datalab vs direct modules

- Direct multilabel APIs use list-of-lists labels and class-index-aligned probability columns.
- Direct regression APIs use numeric targets and predictions, or `CleanLearning` with a regression model.
- `Datalab(task="multilabel")` and `Datalab(task="regression")` use the same label semantics, but they are the broader audit route and return `label_score` in the issue table.
