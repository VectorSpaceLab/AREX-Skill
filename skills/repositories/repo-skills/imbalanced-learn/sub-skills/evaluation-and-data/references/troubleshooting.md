# Troubleshooting — evaluation and data

## Download and cache issues

- If `fetch_datasets` fails, decide whether the user truly needs the benchmark
  loader or just a local toy dataset.
- For offline work, set `download_if_missing=False` and treat a cache miss as an
  expected skip rather than a failure in the rest of the workflow.

## Metric interpretation problems

- `classification_report_imbalanced` depends on `labels`, `target_names`, and
  averaging choices.
- `geometric_mean_score` can look unfamiliar when the class distribution is
  extreme; check the averaging mode.
- `sensitivity_score` and `specificity_score` are more meaningful when the user
  cares about false negatives or false positives explicitly.
- `macro_averaged_mean_absolute_error` is for ordinal labels, not generic
  classification.

## Categorical distance problems

- Encode categories consistently before using `ValueDifferenceMetric`.
- Make sure the training data actually contains the categories that the metric
  should compare.

## Leakage problems

- If the reported score is suspiciously high, verify that the sampler was not
  applied before the train/test split.
- Use the pipeline path from `model-workflows` when the goal is a realistic
  evaluation.

## Recovery steps

1. Reduce to a tiny fixed-label example.
2. Re-run `scripts/metrics_report_demo.py` or `scripts/vdm_demo.py`.
3. Check whether the issue is data shaping, metric choice, or evaluation order.
