# Detectors and Explainers Troubleshooting

## MDSS scan returns an empty or surprising subgroup

Likely causes:

- Candidate features are continuous and were not binned into interpretable
  subgroup values.
- `overpredicted` is reversed for the policy question.
- `pos_label` / `favorable_value` is inconsistent with the target labels.
- Expectations are probabilities for a different row order than observations.
- The penalty is too high or `num_iters` is too low for the signal.

Recovery:

1. Verify index alignment among `X`, observed labels, and expectations.
2. Print unique values for each scan feature and bin continuous columns.
3. Rerun with both `overpredicted=True` and `False` on a tiny slice to confirm
   direction.
4. Lower the penalty or increase `num_iters` only after input alignment is
   correct.

## `AssertionError` about mode or favorable value

MDSS supports `binary`, `continuous`, `nominal`, and `ordinal` modes. The
favorable/positive value must be compatible with the selected mode and observed
labels.

Recovery:

- For binary labels, set `pos_label`/`favorable_value` to the exact positive
  value or use `high`/`low` where documented.
- For nominal mode, ensure expectations are a DataFrame with one column per
  class and matching categories.
- For continuous/ordinal mode, verify that higher or lower values really mean
  better outcomes before selecting scan direction.

## FACTS import or runtime failure

Symptoms:

- Warning: `FACTS will be unavailable. To install, run: pip install 'aif360[FACTS]'`.
- Import errors for `mlxtend`, `colorama`, or `tqdm`.
- Rule mining returns no actions or recommends changes to immutable attributes.

Recovery:

1. Install the `FACTS` extra only if the user needs counterfactual recourse.
2. Verify the classifier has a working `predict(X)` method on the same columns.
3. Set `categorical_features` explicitly when dtype inference is unreliable.
4. Use `feats_allowed_to_change` or `feats_not_allowed_to_change` for immutable
   features such as protected attributes, age, or historical outcomes.
5. Reduce itemset support or inspect feature discretization if no rules are
   found.

## Explainer raises `TypeError: metric must be a Metric`

The explainers require legacy AIF360 metric objects, not raw floats or sklearn
metric functions.

Recovery:

```python
from aif360.metrics import BinaryLabelDatasetMetric
from aif360.explainers import MetricTextExplainer

metric = BinaryLabelDatasetMetric(dataset, unprivileged_groups=ug, privileged_groups=pg)
text = MetricTextExplainer(metric).statistical_parity_difference()
```

If the user's data are pandas `Series`, first decide whether to stay in the
sklearn API or convert to a legacy `BinaryLabelDataset`.

## JSON explainer output is a string

`MetricJSONExplainer` returns JSON text. Parse it before treating it as a
dictionary:

```python
import json
payload = json.loads(MetricJSONExplainer(metric).disparate_impact())
```

Payload schemas differ by metric method. Some methods include `value`; others
include counts/rates and a message. Keep your downstream parser defensive.

## Need mitigation after detection

Detectors identify candidate subgroups or recourse disparities. They do not
mitigate bias. After interpreting the detector output, route mitigation work to
[mitigation-algorithms](../../mitigation-algorithms/SKILL.md) or
[sklearn-interface](../../sklearn-interface/SKILL.md) depending on API family.
