# API Reference — evaluation and data

## Core signatures confirmed in the private inspection environment

| Symbol | Signature / key arguments | Notes |
|---|---|---|
| `make_imbalance` | `make_imbalance(X, y, *, sampling_strategy=None, random_state=None, verbose=False, **kwargs)` | Turns a dataset into a skewed dataset. |
| `fetch_datasets` | `fetch_datasets(*, data_home=None, filter_data=None, download_if_missing=True, random_state=None, shuffle=False, verbose=False)` | Loads benchmark datasets, optionally from cache only. |
| `geometric_mean_score` | `geometric_mean_score(y_true, y_pred, *, labels=None, pos_label=1, average='multiclass', sample_weight=None, correction=0.0)` | Imbalance-aware score. |
| `classification_report_imbalanced` | `classification_report_imbalanced(y_true, y_pred, *, labels=None, target_names=None, sample_weight=None, digits=2, alpha=0.1, output_dict=False, zero_division='warn')` | Per-class summary report. |
| `sensitivity_specificity_support` | public metric helper | Returns sensitivity, specificity, and support. |
| `sensitivity_score` / `specificity_score` | public metric helpers | One-sided views of the above. |
| `make_index_balanced_accuracy` | public wrapper | Wraps another metric with class-balance weighting. |
| `macro_averaged_mean_absolute_error` | public metric | Ordinal-imbalance metric. |
| `ValueDifferenceMetric` | `ValueDifferenceMetric(n_categories='auto', k=1, r=2)` | Categorical pairwise distance. |

## Choice notes

- `make_imbalance` is the dataset-shaping mirror of a sampler.
- `fetch_datasets` is a benchmark loader and may rely on network or cache.
- `classification_report_imbalanced` is best for readable summaries.
- `geometric_mean_score` is a compact scalar when per-class balance matters.
- `ValueDifferenceMetric` is a specialized categorical distance tool, not a
  general replacement for Euclidean distance.

## Related behavior

- The package preserves pandas input/output in many sampler workflows, so
  evaluation examples can use DataFrames when that is the user-facing shape.
- The common-pitfalls guide is part of this sub-skill because leakage is an
  evaluation error, not just a preprocessing mistake.
