# Metric Explainer Reference

## When to read

Read this when a user wants human-readable or structured explanations for
AIF360 metric outputs, or when a metric object already exists and the task is to
turn its values into report text/JSON.

## Verified constructors

```text
MetricTextExplainer(metric)
MetricJSONExplainer(metric)
```

The constructor argument must be an AIF360 legacy `Metric` instance, such as
`BinaryLabelDatasetMetric`, `ClassificationMetric`, `SampleDistortionMetric`,
or a compatible subclass. It is not a pandas Series, a sklearn metric function,
or a raw numeric value.

## Text explanations

```python
from aif360.explainers import MetricTextExplainer

explainer = MetricTextExplainer(metric)
print(explainer.statistical_parity_difference())
print(explainer.disparate_impact())
```

Text methods call the corresponding metric method and return explanatory
strings. Method availability still depends on the wrapped metric object. For
example, `ClassificationMetric` supports `accuracy`, but a plain
`BinaryLabelDatasetMetric` does not.

## JSON explanations

```python
import json
from aif360.explainers import MetricJSONExplainer

explainer = MetricJSONExplainer(metric)
payload = json.loads(explainer.statistical_parity_difference())
print(payload["metric"], payload["message"])
```

`MetricJSONExplainer` methods return JSON strings, not Python dictionaries.
Parse them with `json.loads` before indexing fields. Common fields include:

- `metric`: display name.
- `message`: the text explainer's sentence.
- `description`: how the metric is computed or interpreted.
- `ideal`: ideal or target direction.
- Metric-specific counts or rates when the method can expose them.

Some older JSON payloads omit a generic `value` field and store the numeric
result inside `message` or metric-specific fields. Do not assume all methods
share one schema.

## Good report pattern

1. Compute the underlying metric directly and store the numeric value.
2. Use `MetricTextExplainer` for concise prose in a notebook/report.
3. Use `MetricJSONExplainer` for a structured API response or downstream UI.
4. Preserve group definitions and favorable-label semantics alongside the
   explanation so readers know what unprivileged and privileged mean.

## Safe smoke

Run:

```bash
python sub-skills/detectors-and-explainers/scripts/explainer_smoke.py --json
```

The helper creates a synthetic `BinaryLabelDatasetMetric`, renders statistical
parity difference through both explainers, parses the JSON string, and checks
that the text contains the expected metric name.

## Route away

- If the user needs to compute metric values first, route to
  [datasets-and-metrics](../../datasets-and-metrics/SKILL.md).
- If the user has pandas/sklearn metric functions, route to
  [sklearn-interface](../../sklearn-interface/SKILL.md); these explainers wrap
  legacy metric objects.
- If the user asks to identify anomalous subgroups, use MDSS or FACTS instead of
  explainers.
