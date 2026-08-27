# Plotting and confidence intervals

## Plotting dependency

Fairlearn plotting helpers require matplotlib. In headless environments, set a non-interactive backend before importing pyplot:

```python
import matplotlib
matplotlib.use("Agg")
```

If a runtime error tells the user to install `fairlearn[customplots]`, direct `python -m pip install matplotlib` is the safest recovery. Extra names can vary by release.

## Grouped metric plots

The simplest grouped plot uses pandas on `MetricFrame.by_group`:

```python
ax = mf.by_group.plot(kind="bar", ylim=(0, 1), title="Grouped metrics")
fig = ax.get_figure()
fig.savefig("metricframe-by-group.png", bbox_inches="tight")
```

Use explicit `ylim` for rate metrics so narrow ranges do not visually exaggerate differences.

The experimental Fairlearn helper is imported from:

```python
from fairlearn.experimental.enable_metric_frame_plotting import plot_metric_frame

axs = plot_metric_frame(mf, kind="bar", metrics=["accuracy", "selection_rate"])
```

`plot_metric_frame` accepts `kind`, `metrics`, `conf_intervals`, `subplots`, and CI-label formatting parameters. In the inspected source it auto-detects bootstrap confidence intervals from a `MetricFrame` that was created with `n_boot` and `ci_quantiles`.

## Bootstrap confidence intervals

Create bootstrap estimates by setting both `n_boot` and `ci_quantiles`:

```python
mf_ci = MetricFrame(
    metrics={"accuracy": accuracy_score, "selection_rate": selection_rate},
    y_true=y_true,
    y_pred=y_pred,
    sensitive_features=sensitive,
    n_boot=100,
    ci_quantiles=[0.025, 0.975],
    random_state=0,
)

print(mf_ci.by_group)
print(mf_ci.by_group_ci)       # list indexed by ci_quantiles order
print(mf_ci.ci_quantiles)
```

Rules:

- `n_boot` and `ci_quantiles` must be supplied together.
- Every value in `ci_quantiles` must be a float in `(0, 1)`.
- Use more bootstrap samples for final reports than for smoke tests.
- If group counts are very small, bootstrap intervals can be unstable or missing for metrics that require both classes.

## ROC curves by sensitive feature

Use `plot_roc_curve_by_group` for binary classifiers with continuous scores:

```python
from fairlearn.metrics import plot_roc_curve_by_group

ax = plot_roc_curve_by_group(
    y_true,
    y_score,
    sensitive_features=sensitive,
    plot_overall=True,
    plot_chance_level=True,
)
ax.get_figure().savefig("roc-by-group.png", bbox_inches="tight")
```

The function draws curves; it does not return AUC values. For AUC values, pass `sklearn.metrics.roc_auc_score` into `MetricFrame` and use the scores as `y_pred`.

## Model comparison plots

`plot_model_comparison` compares multiple prediction vectors along two metrics:

```python
from sklearn.metrics import accuracy_score
from fairlearn.metrics import demographic_parity_difference, plot_model_comparison, selection_rate

ax = plot_model_comparison(
    y_preds={"baseline": pred_baseline, "mitigated": pred_mitigated},
    y_true=y_true,
    sensitive_features=sensitive,
    x_axis_metric=accuracy_score,
    y_axis_metric=demographic_parity_difference,
    axis_labels=True,
    point_labels=True,
)
ax.get_figure().savefig("model-comparison.png", bbox_inches="tight")
```

Use model-comparison plots after a mitigation workflow to show utility/disparity trade-offs, but keep ownership of the mitigation algorithm in its sub-skill.

## Plot selection guide

| Need | Use |
| --- | --- |
| Bar or point chart of existing grouped metrics | pandas `mf.by_group.plot(...)` or `plot_metric_frame`. |
| Confidence intervals around grouped metrics | `MetricFrame(..., n_boot=..., ci_quantiles=...)` plus `plot_metric_frame`. |
| Ranking quality by group for binary classifier scores | `plot_roc_curve_by_group`. |
| Compare baseline and mitigated models on utility/disparity axes | `plot_model_comparison`. |

## Headless validation

Run:

```bash
python sub-skills/assessment/scripts/smoke_assessment.py --plot --output-dir /tmp/fairlearn-assessment-plots
```

The script writes small PNG files and uses synthetic data only.
