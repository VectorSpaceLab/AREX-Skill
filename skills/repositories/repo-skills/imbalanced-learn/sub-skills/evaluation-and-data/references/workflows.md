# Workflows — evaluation and data

## 1. Create a controlled imbalance

Use `make_imbalance` when you want to turn a balanced benchmark into a skewed
version of itself.

```python
from imblearn.datasets import make_imbalance

X_imb, y_imb = make_imbalance(X, y, sampling_strategy={0: 20, 1: 30})
```

A callable strategy is useful when the target counts should be derived from the
current label histogram.

## 2. Load benchmark datasets carefully

`fetch_datasets` is useful when the cache already contains the benchmark data
or when downloads are acceptable.
For offline or no-network use, pass `download_if_missing=False` and expect a
clean failure if the cache is empty.

## 3. Pick the metric that matches the task

| Task | Better metric choice |
|---|---|
| Human-readable model summary | `classification_report_imbalanced` |
| Single scalar for class balance | `geometric_mean_score` |
| Recall vs specificity emphasis | `sensitivity_score`, `specificity_score` |
| Ordinal labels | `macro_averaged_mean_absolute_error` |
| Categorical distance | `ValueDifferenceMetric` |

## 4. Keep evaluation leakage-free

A safe workflow is:

1. split the dataset,
2. resample only the training side,
3. train the model,
4. evaluate on the untouched test side.

The common-pitfalls guide exists because resampling before the split can make
scores look much better than they are.

## 5. Use the scripts

- `dataset_imbalance_demo.py` for a tiny `make_imbalance` example and cached
  dataset check.
- `metrics_report_demo.py` for fixed-label metric output.
- `vdm_demo.py` for pairwise categorical distance.

## Native evidence to match later

- `test_make_imbalanced_iris`
- `test_classification_report_imbalanced_multiclass`
- `test_geometric_mean_multiclass`
- `test_macro_averaged_mean_absolute_error`
- `test_value_difference_metric`
- `test_pandas_column_name_consistency`
