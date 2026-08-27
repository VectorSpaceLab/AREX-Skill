# Datasets and metrics workflows

Use these workflows without depending on raw benchmark data, notebooks, or source checkout files. Start with synthetic data to prove the dataset and metric mechanics, then move to raw wrappers only when data availability and usage constraints are explicit.

## Workflow 1: Build an in-memory binary dataset

```python
import pandas as pd
from aif360.datasets import BinaryLabelDataset

raw = pd.DataFrame({
    "score_feature": [0.10, 0.40, 0.75, 0.90, 0.35, 0.80],
    "sex":           [0.0, 0.0, 0.0, 1.0, 1.0, 1.0],
    "approved":      [1.0, 1.0, 0.0, 1.0, 0.0, 0.0],
})

dataset = BinaryLabelDataset(
    df=raw,
    label_names=["approved"],
    protected_attribute_names=["sex"],
    favorable_label=1.0,
    unfavorable_label=0.0,
)

privileged_groups = [{"sex": 1.0}]
unprivileged_groups = [{"sex": 0.0}]
```

Immediate checks:

```python
assert dataset.labels.shape == (len(raw), 1)
assert dataset.protected_attribute_names == ["sex"]
assert set(dataset.labels.ravel()) <= {dataset.favorable_label, dataset.unfavorable_label}
```

Use this pattern whenever the task is about AIF360 mechanics or regression tests. It is also the pattern used by the bundled [metric smoke script](../scripts/metric_report_smoke.py).

## Workflow 2: Compute dataset bias metrics

```python
from aif360.metrics import BinaryLabelDatasetMetric

metric = BinaryLabelDatasetMetric(
    dataset,
    unprivileged_groups=unprivileged_groups,
    privileged_groups=privileged_groups,
)

summary = {
    "n": metric.num_instances(),
    "base_rate": metric.base_rate(),
    "base_rate_unprivileged": metric.base_rate(privileged=False),
    "base_rate_privileged": metric.base_rate(privileged=True),
    "statistical_parity_difference": metric.statistical_parity_difference(),
    "disparate_impact": metric.disparate_impact(),
}
```

Interpretation tips:

- `statistical_parity_difference` is unprivileged minus privileged. Values near `0` indicate parity under this definition.
- `disparate_impact` is unprivileged divided by privileged. Values near `1` indicate parity under this definition.
- If a denominator group has no favorable labels, the ratio may be infinite or undefined. Inspect `base_rate(privileged=True/False)` before trusting ratios.

## Workflow 3: Compute classification metrics from predictions

Construct predictions by copying the true dataset so the feature/protected schema stays identical.

```python
import numpy as np
from aif360.metrics import ClassificationMetric

classified = dataset.copy(True)
classified.labels = np.array([[1.0], [0.0], [1.0], [1.0], [0.0], [0.0]])
classified.scores = classified.labels.copy()  # replace with probabilities if available

classification = ClassificationMetric(
    dataset,
    classified,
    unprivileged_groups=unprivileged_groups,
    privileged_groups=privileged_groups,
)

report = {
    "balanced_accuracy": 0.5 * (
        classification.true_positive_rate() + classification.true_negative_rate()
    ),
    "statistical_parity_difference": classification.statistical_parity_difference(),
    "disparate_impact": classification.disparate_impact(),
    "average_odds_difference": classification.average_odds_difference(),
    "equal_opportunity_difference": classification.equal_opportunity_difference(),
    "theil_index": classification.theil_index(),
}
```

Use `classified.scores` for calibrated probabilities when generalized confusion counts, postprocessing, or MDSS metrics need expectations. For hard-label-only reports, copying labels into scores is acceptable for a mechanical smoke but should not be described as calibrated.

## Workflow 4: Load built-in legacy wrappers only after raw-data checks

Built-in wrappers are convenient but can terminate the process on missing raw files or trigger network-bound behavior. Use this checklist:

1. Decide whether a raw public dataset is truly needed; otherwise use the in-memory workflow.
2. Confirm the current runtime package has the required raw files or documented cache for the wrapper.
3. Instantiate the wrapper with a narrow feature/protected-attribute scope if possible.
4. Immediately inspect `label_names`, `protected_attribute_names`, `privileged_protected_attributes`, `unprivileged_protected_attributes`, and `metadata`.
5. Compute `BinaryLabelDatasetMetric` before running mitigation or classification workflows.

Example after raw data is known available:

```python
from aif360.datasets import GermanDataset
from aif360.metrics import BinaryLabelDatasetMetric

german = GermanDataset(
    protected_attribute_names=["sex"],
    privileged_classes=[["male"]],
)
metric = BinaryLabelDatasetMetric(
    german,
    unprivileged_groups=[{"sex": 0.0}],
    privileged_groups=[{"sex": 1.0}],
)
print(metric.base_rate(privileged=False), metric.base_rate(privileged=True))
```

If the task asks for pandas DataFrames, caching, or `fetch_*` helpers rather than legacy dataset classes, route to [sklearn-interface](../../sklearn-interface/SKILL.md).

## Workflow 5: Sample distortion metrics

Use `SampleDistortionMetric` after a preprocessing transformation that changes features or labels but should preserve instance order and protected attributes.

```python
from aif360.datasets import StructuredDataset
from aif360.metrics import SampleDistortionMetric

original = StructuredDataset(
    df=raw,
    label_names=["approved"],
    protected_attribute_names=["sex"],
)
distorted = original.copy(True)
distorted.features = original.features.copy()
distorted.features[:, 0] = distorted.features[:, 0] + 0.10

sdm = SampleDistortionMetric(
    original,
    distorted,
    unprivileged_groups=unprivileged_groups,
    privileged_groups=privileged_groups,
)

overall = sdm.average_manhattan_distance()
unpriv = sdm.average_manhattan_distance(privileged=False)
priv = sdm.average_manhattan_distance(privileged=True)
manual_difference = unpriv - priv
manual_ratio = unpriv / priv if priv else float("inf")
```

Prefer manual group differences/ratios as shown above. The direct distance aggregate methods are the reliable primitives.

## Workflow 6: Regression/ranking metrics

`RegressionDatasetMetric` expects a `RegressionDataset`. The order of rows matters for ranking metrics such as DCG.

```python
import pandas as pd
from aif360.datasets import RegressionDataset
from aif360.metrics import RegressionDatasetMetric

ranked = pd.DataFrame({
    "group": ["A", "B", "B", "A", "B"],
    "score": [90, 80, 70, 60, 50],
})
reg = RegressionDataset(
    ranked,
    dep_var_name="score",
    protected_attribute_names=["group"],
    privileged_classes=[["A"]],
)
rdm = RegressionDatasetMetric(
    reg,
    unprivileged_groups=[{"group": 0.0}],
    privileged_groups=[{"group": 1.0}],
)

infeasible_index, violating_positions = rdm.infeasible_index(
    target_prop={0.0: 0.5, 1.0: 0.5}
)
dcg = rdm.discounted_cum_gain()
ndcg = rdm.discounted_cum_gain(normalized=True, full_dataset=reg)
```

Troubleshoot `target_prop` with `reg.protected_attribute_names` and `reg.convert_to_dataframe()[0]` if keys do not match observed encoded protected values.

## Workflow 7: MDSS classification metric score for known groups

Use `MDSSClassificationMetric` when you already know which privileged or unprivileged groups to score inside a classification metric object.

```python
from aif360.metrics import MDSSClassificationMetric

classified_with_scores = dataset.copy(True)
classified_with_scores.labels = classified.labels.copy()
classified_with_scores.scores = np.array([[0.8], [0.4], [0.7], [0.6], [0.2], [0.3]])

mdss_metric = MDSSClassificationMetric(
    dataset,
    classified_with_scores,
    scoring="Bernoulli",
    unprivileged_groups=unprivileged_groups,
    privileged_groups=privileged_groups,
)
unprivileged_score = mdss_metric.score_groups(privileged=False)
privileged_score = mdss_metric.score_groups(privileged=True)
```

Use probabilities or expectation-like scores in `classified_dataset.scores`. For discovering a highest-scoring subgroup rather than scoring the already supplied groups, route to [detectors-and-explainers](../../detectors-and-explainers/SKILL.md).

## Workflow 8: Decide when to compute metrics around mitigation

Legacy mitigation workflows usually follow this shape:

1. Build or load a `BinaryLabelDataset`.
2. Define `privileged_groups` and `unprivileged_groups`.
3. Compute `BinaryLabelDatasetMetric` to report original label imbalance.
4. Split into train/test with `dataset.split(...)` if training a model.
5. Fit a mitigation algorithm or baseline classifier.
6. Convert predictions into a copied `BinaryLabelDataset` and compute `ClassificationMetric`.

When the task reaches step 5, route to [mitigation-algorithms](../../mitigation-algorithms/SKILL.md). Return here for step 6 metric reporting.
