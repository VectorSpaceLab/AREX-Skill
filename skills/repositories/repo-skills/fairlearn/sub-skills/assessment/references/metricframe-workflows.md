# MetricFrame and fairness metric workflows

## Minimal grouped assessment

`MetricFrame` computes one or more metrics overall and by group.

```python
from sklearn.metrics import accuracy_score
from fairlearn.metrics import MetricFrame, selection_rate

mf = MetricFrame(
    metrics={"accuracy": accuracy_score, "selection_rate": selection_rate},
    y_true=y_test,
    y_pred=y_pred,
    sensitive_features=sensitive_test,
)

print(mf.overall)
print(mf.by_group)
print(mf.difference(method="between_groups"))
print(mf.ratio(method="between_groups"))
```

Constructor fields verified for this source:

```text
MetricFrame(*, metrics, y_true, y_pred, sensitive_features,
            control_features=None, sample_params=None,
            n_boot=None, ci_quantiles=None, random_state=None)
```

Use a single callable when one metric is enough; use a dict when the report needs multiple metrics. Dict keys become output labels.

## Common Fairlearn metrics

| API | Use |
| --- | --- |
| `selection_rate(y_true, y_pred, pos_label=1)` | Fraction of positive predictions; central for demographic parity. |
| `count(y_true, y_pred)` | Group sample counts; always include when group sizes may be uneven. |
| `true_positive_rate`, `true_negative_rate`, `false_positive_rate`, `false_negative_rate` | Error-rate and quality-of-service diagnostics by group. |
| `mean_prediction` | Mean prediction value, useful for regression-style outputs or scores. |
| `demographic_parity_difference` / `ratio` | Direct disparity helper for selection-rate parity. |
| `equalized_odds_difference` / `ratio` | Direct helper comparing TPR/FPR behavior across groups. |
| `equal_opportunity_difference` / `ratio` | Direct helper focused on positive-label recall parity. |

Direct fairness metric helpers accept `sensitive_features` directly:

```python
from fairlearn.metrics import demographic_parity_difference, equalized_odds_difference

dp = demographic_parity_difference(y_true, y_pred, sensitive_features=sensitive)
eo = equalized_odds_difference(y_true, y_pred, sensitive_features=sensitive)
```

Use `MetricFrame` when you need a table; use direct helpers when the mitigation algorithm or report wants one scalar disparity.

## Derived metrics

`make_derived_metric` converts a metric into a difference, ratio, group-min, or group-max helper:

```python
from sklearn.metrics import accuracy_score
from fairlearn.metrics import make_derived_metric

accuracy_difference = make_derived_metric(metric=accuracy_score, transform="difference")
print(accuracy_difference(y_true, y_pred, sensitive_features=sensitive))
```

Generated convenience functions of the same pattern exist for many Fairlearn metrics. Prefer explicit `MetricFrame` when the user needs both scalar disparity and subgroup evidence.

## Intersections and control features

- Pass a pandas DataFrame as `sensitive_features` to evaluate intersections of multiple sensitive attributes.
- Pass `control_features` when you want separate group tables per control slice while keeping disparity calculations within each control level.
- Keep human-readable column names. Otherwise group labels can become hard to interpret.

Example shape:

```python
sensitive = data[["race", "sex"]]
control = data["model_version"]

mf = MetricFrame(
    metrics={"accuracy": accuracy_score, "selection_rate": selection_rate},
    y_true=y,
    y_pred=pred,
    sensitive_features=sensitive,
    control_features=control,
)
```

## Metrics with sample parameters

Some sklearn metrics accept `sample_weight` or other row-aligned arrays. Pass them through `sample_params`:

```python
mf = MetricFrame(
    metrics={"weighted_accuracy": accuracy_score},
    y_true=y,
    y_pred=pred,
    sensitive_features=sensitive,
    sample_params={"weighted_accuracy": {"sample_weight": weights}},
)
```

If all metrics share the same parameter name, a non-nested `sample_params` dict can be enough. For several metrics with different parameters, prefer the nested form keyed by metric name.

## Persistence pattern

For reports, persist output tables rather than depending on a live `MetricFrame` object:

```python
mf.overall.to_frame("value").to_csv("overall_metrics.csv")
mf.by_group.to_csv("by_group_metrics.csv")
```

If `mf.overall` is already a scalar or Series depending on the metric shape, normalize it before saving. Always save the metric definitions and sensitive-feature columns alongside the result tables.

## Interpretation checklist

Before reporting an assessment:

- State the prediction target and positive label.
- State each sensitive feature and any control feature.
- Include group counts.
- Include at least one utility metric and the fairness metric relevant to the user's harm model.
- Compare subgroup values and scalar differences/ratios.
- Note sample size limitations and whether confidence intervals were computed.
