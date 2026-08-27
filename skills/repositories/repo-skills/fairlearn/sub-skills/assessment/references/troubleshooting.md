# Assessment troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError` about inconsistent numbers of samples | `y_true`, `y_pred`, `sensitive_features`, `control_features`, or `sample_params` are not row-aligned. | Split and filter all arrays together; compare lengths and indices before calling Fairlearn. |
| `MetricFrame` output group labels are hard to read | Sensitive features were passed as unnamed arrays. | Use pandas Series/DataFrames with names such as `sex`, `race`, `age_bucket`, or `region`. |
| `MetricFrame` with a sklearn metric fails for one subgroup | The subgroup lacks required class labels or inputs for that metric. | Include `count`; choose metrics robust to small groups; merge sparse groups only if analytically justified. |
| Bootstrap raises `Must specify both n_boot and ci_quantiles` | Only one bootstrap argument was set. | Supply both arguments or neither. |
| Bootstrap raises `Must have all ci_quantiles be floats in (0, 1)` | Invalid quantile values. | Use values like `[0.025, 0.975]` or `[0.159, 0.841]`. |
| Direct fairness metric returns a scalar but user wants subgroup table | Direct helpers compute one disparity number. | Use `MetricFrame` with the same metric and inspect `by_group`, `difference()`, and `ratio()`. |
| `plot_metric_frame` import fails | Experimental helper is not imported from `fairlearn.metrics` in this source. | Import `from fairlearn.experimental.enable_metric_frame_plotting import plot_metric_frame`. |
| Plotting raises a matplotlib installation error | Plot helper dependency is missing. | Install `matplotlib`; then rerun the assessment smoke script with `--plot`. |
| ROC plot gives misleading results | `y_score` is a hard label instead of a continuous score. | Pass classifier probabilities or decision scores; use `MetricFrame` for hard-label metrics. |
| Multiclass assessment is requested | Fairlearn assessment can use arbitrary sklearn metrics, but mitigation support differs by algorithm. | Use `MetricFrame` with an appropriate multiclass metric; route mitigation questions to reductions or another owning sub-skill. |

## Diagnostic snippet

```python
print(len(y_true), len(y_pred), len(sensitive_features))
print(getattr(y_true, "index", None))
print(getattr(sensitive_features, "index", None))
print(MetricFrame(metrics={"count": count}, y_true=y_true, y_pred=y_pred, sensitive_features=sensitive_features).by_group)
```

If this count-only frame fails, fix alignment before adding more metrics.
