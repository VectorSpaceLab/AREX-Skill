---
name: evaluation-and-data
description: "Router for imbalanced-learn dataset fabrication, benchmark
  loading, imbalance-aware metrics, and categorical distance tools."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# evaluation-and-data

Use this sub-skill when the task is about preparing imbalanced datasets or
measuring model quality on imbalanced classification problems.

This sub-skill owns the package surfaces that shape or evaluate data:

- `make_imbalance`
- `fetch_datasets`
- `classification_report_imbalanced`
- `geometric_mean_score`
- `sensitivity_specificity_support`
- `sensitivity_score`
- `specificity_score`
- `make_index_balanced_accuracy`
- `macro_averaged_mean_absolute_error`
- `ValueDifferenceMetric`

It also owns the common-pitfalls guidance around data leakage and evaluation
order.

## What to do first

1. Decide whether the user wants to create an imbalanced dataset, load a cached
   benchmark dataset, or evaluate predictions.
2. If the task is about evaluation, decide whether the labels are binary,
   multiclass, or ordinal.
3. If the task is about categorical similarity, check whether the inputs are
   categorical-only and need `ValueDifferenceMetric`.
4. Keep any resampling inside the training branch; do not evaluate on a fully
   resampled dataset unless that is explicitly the point of the example.
5. Verify the output on a tiny dataset before applying the same pattern to a
   real one.

## Typical routing cues

- `make_imbalance`, `fetch_datasets`
- `classification_report_imbalanced`, `geometric_mean_score`
- `sensitivity_score`, `specificity_score`, `macro_averaged_mean_absolute_error`
- `ValueDifferenceMetric`
- `common_pitfalls`, leakage, balanced accuracy, pandas output

## When to read the bundled references

- `references/workflows.md` for dataset shaping and metric selection.
- `references/api-reference.md` for the compact dataset and metric catalog.
- `references/troubleshooting.md` when downloading, label encoding, or metric
  selection fails.

## Common choices

- Use `make_imbalance` when the task starts from a balanced dataset and needs a
  deliberate class-skew scenario.
- Use `fetch_datasets` when the task needs one of the curated benchmark
  datasets and offline cache behavior is acceptable.
- Use `classification_report_imbalanced` when the user wants a human-readable
  per-class summary.
- Use `geometric_mean_score` when class-wise balance matters more than overall
  accuracy.
- Use `sensitivity_*` and `specificity_*` when the domain is medical or recall-
  versus-specificity oriented.
- Use `macro_averaged_mean_absolute_error` for ordinal imbalance problems.
- Use `ValueDifferenceMetric` when the task is about categorical pairwise
  distances.

## Native evidence to keep in mind

These repo tests are the most relevant later verification anchors for this
sub-skill:

- `imblearn/datasets/tests/test_imbalance.py::test_make_imbalanced_iris`
- `imblearn/datasets/tests/test_zenodo.py::test_fetch`
- `imblearn/metrics/tests/test_classification.py::test_classification_report_imbalanced_multiclass`
- `imblearn/metrics/tests/test_classification.py::test_geometric_mean_multiclass`
- `imblearn/metrics/tests/test_classification.py::test_macro_averaged_mean_absolute_error`
- `imblearn/metrics/tests/test_pairwise.py::test_value_difference_metric`
- `imblearn/tests/test_common.py::test_pandas_column_name_consistency`

## Package-specific cautions

- `fetch_datasets` is a network/cache helper, not a pure offline primitive.
- Metric results depend on label order, averaging choice, and the selected
  positive label.
- `ValueDifferenceMetric` expects categorical values to be encoded in a way the
  metric can interpret.
- Leakage-safe evaluation means splitting before resampling.

## Use the scripts

- `scripts/dataset_imbalance_demo.py` for tiny `make_imbalance` and cached
  dataset checks.
- `scripts/metrics_report_demo.py` for compact metric output on fixed labels.
- `scripts/vdm_demo.py` for categorical distance checks.
