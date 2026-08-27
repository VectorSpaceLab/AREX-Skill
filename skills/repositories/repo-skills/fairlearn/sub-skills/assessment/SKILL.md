---
name: assessment
description: "Use Fairlearn assessment APIs for MetricFrame, group fairness
  metrics, bootstrapped confidence intervals, model comparison, and subgroup
  plots."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Fairlearn assessment

Use this sub-skill when the task is about assessing model behavior across groups: `MetricFrame`, `sensitive_features`, group metrics, demographic parity/equalized odds metrics, intersections, control features, confidence intervals, `plot_model_comparison`, `plot_roc_curve_by_group`, or the experimental `plot_metric_frame` helper.

## Quick workflow

1. Align `y_true`, `y_pred` or scores, and `sensitive_features` row-for-row.
2. Choose overall utility metrics and fairness-sensitive group metrics before mitigation.
3. Build a `MetricFrame` with a metric callable or a metric dictionary.
4. Inspect `overall`, `by_group`, `group_min()`, `group_max()`, `difference()`, and `ratio()`.
5. For uncertainty, set both `n_boot` and `ci_quantiles`; if either is set alone Fairlearn raises a bootstrap parameter error.
6. For plots, confirm matplotlib is installed, then use pandas plotting, `plot_roc_curve_by_group`, `plot_model_comparison`, or the experimental `plot_metric_frame` import path.

## Read these references

- [`references/metricframe-workflows.md`](references/metricframe-workflows.md) for `MetricFrame` inputs/outputs, metric helpers, derived metrics, sample parameters, intersections, and persistence patterns.
- [`references/plotting-and-confidence-intervals.md`](references/plotting-and-confidence-intervals.md) for plotting helpers, headless plotting, ROC-by-group, model comparison, and bootstrap confidence intervals.
- [`references/troubleshooting.md`](references/troubleshooting.md) for missing matplotlib, length mismatches, custom metric failures, bootstrap errors, and experimental plotting import issues.
- [`scripts/smoke_assessment.py`](scripts/smoke_assessment.py) for a tiny synthetic assessment and optional plot smoke check.

## Core APIs to recognize

- `fairlearn.metrics.MetricFrame`
- Base metrics: `selection_rate`, `count`, `true_positive_rate`, `true_negative_rate`, `false_positive_rate`, `false_negative_rate`, `mean_prediction`
- Fairness metrics: `demographic_parity_difference`, `demographic_parity_ratio`, `equalized_odds_difference`, `equalized_odds_ratio`, `equal_opportunity_difference`, `equal_opportunity_ratio`
- Dynamic helpers: `make_derived_metric`, generated `<metric>_{difference,ratio,group_min,group_max}` functions
- Plots: `plot_model_comparison`, `plot_roc_curve_by_group`, and `plot_metric_frame` from `fairlearn.experimental.enable_metric_frame_plotting`

## Boundary rules

- This sub-skill owns assessment only. If the user asks how to change the model, route to preprocessing, reductions, postprocessing, or adversarial after summarizing the assessment target.
- This sub-skill can evaluate any sklearn-compatible model's predictions; it does not require Fairlearn mitigation algorithms.
- Dataset fetchers are owned by `../datasets/`; use this sub-skill only after the data is loaded and predictions/scores are available.
- Plot dependency diagnosis starts here for assessment plots, but package-wide install recovery lives in `../../references/troubleshooting.md` and `../installation/`.

## Operating rules

- Always name the sensitive features and their intended grouping semantics in the report.
- Do not report a single fairness metric as a final fairness verdict. Include overall utility, subgroup metrics, and context limitations.
- Use `control_features` when comparing sensitive-feature disparities within slices such as model version, region, or time bucket.
- For multiple sensitive features, prefer a pandas DataFrame with named columns so group/intersection labels are intelligible.
- For custom metrics that need `sample_weight` or other side inputs, pass `sample_params` with the same row alignment as `y_true` and `y_pred`.
- In headless environments set `MPLBACKEND=Agg` or call `matplotlib.use("Agg")` before plotting.

## Fast validation

Run a no-network smoke check:

```bash
python sub-skills/assessment/scripts/smoke_assessment.py
```

Run plot coverage in a matplotlib-capable environment:

```bash
python sub-skills/assessment/scripts/smoke_assessment.py --plot --output-dir /tmp/fairlearn-assessment-plots
```
