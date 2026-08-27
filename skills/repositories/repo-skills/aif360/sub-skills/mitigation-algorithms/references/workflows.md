# Legacy Mitigation Workflows

Use these patterns after choosing a class in [algorithm-selection.md](algorithm-selection.md). Dataset schemas and metric objects are owned by [datasets-and-metrics](../../datasets-and-metrics/SKILL.md); sklearn/pandas workflows are owned by [sklearn-interface](../../sklearn-interface/SKILL.md).

## Base-safe Reweighing smoke

Run from the generated AIF360 skill root:

```bash
python sub-skills/mitigation-algorithms/scripts/reweighing_smoke.py --help
python sub-skills/mitigation-algorithms/scripts/reweighing_smoke.py --json
```

The script creates an in-memory `BinaryLabelDataset`, runs `Reweighing.fit_transform()`, and reports before/after weighted base rates, mean difference, disparate impact, and instance-weight preservation. It does not download data or train a model.

Minimal Reweighing pattern:

```python
from aif360.algorithms.preprocessing import Reweighing
from aif360.metrics import BinaryLabelDatasetMetric

unprivileged_groups = [{'group': 0.0}]
privileged_groups = [{'group': 1.0}]

before = BinaryLabelDatasetMetric(dataset, unprivileged_groups, privileged_groups)
weighted = Reweighing(unprivileged_groups, privileged_groups).fit_transform(dataset)
after = BinaryLabelDatasetMetric(weighted, unprivileged_groups, privileged_groups)
```

Remember: Reweighing changes `instance_weights`; downstream training must pass those weights explicitly.

## Preprocessing workflow

1. Build or split a `BinaryLabelDataset` with populated favorable/unfavorable labels and protected groups.
2. Count `(group, label)` buckets; avoid empty buckets for Reweighing and very sparse groups for optimization.
3. Choose a preprocessor:
   - `Reweighing`: update weights only.
   - `DisparateImpactRemover`: repair feature values with `repair_level`.
   - `LFR`: fit latent fair prototypes and transform features/labels/scores.
   - `OptimPreproc`: learn randomized feature/label mappings with an `OptTools`-style optimizer.
4. Fit/transform training data only.
5. Train a downstream model on transformed features or sample weights.
6. Transform validation/test data only when the algorithm supports a compatible transform and the schema matches.
7. Compare data metrics and prediction metrics before/after.

Avoid treating preprocessing as proof of fairness: compute metrics after the downstream model is trained.

## Inprocessing workflow

```python
from aif360.algorithms.inprocessing import MetaFairClassifier
from aif360.metrics import ClassificationMetric

model = MetaFairClassifier(tau=0.9, sensitive_attr='sex', type='sr', seed=123)
model.fit(train_dataset)
predicted = model.predict(test_dataset)

cm = ClassificationMetric(
    test_dataset,
    predicted,
    unprivileged_groups=[{'sex': 0.0}],
    privileged_groups=[{'sex': 1.0}],
)
```

Checklist:

- Keep a baseline classifier or baseline metric for comparison.
- Verify group dictionaries use encoded values present in the dataset.
- Reduce epochs/iterations for smoke checks on optional algorithms.
- For reduction methods, choose an estimator that supports `sample_weight`.
- For TensorFlow adversarial debiasing, create a clean session/scope and disable eager execution when required.
- For `IntersectionalFairness`, first verify module import and a tiny multi-protected-attribute dataset; do not start with multi-worker or full-size data.

## Postprocessing workflow

Postprocessors require aligned dataset copies:

- `dataset_true`: true labels for validation or test records.
- `dataset_pred`: a copy with baseline predicted labels, and for score-based classes, positive-class probabilities in `scores`.

Validation/test pattern:

```python
from aif360.algorithms.postprocessing import EqOddsPostprocessing
from aif360.metrics import ClassificationMetric

post = EqOddsPostprocessing(
    unprivileged_groups=[{'sex': 0.0}],
    privileged_groups=[{'sex': 1.0}],
    seed=123,
)
post.fit(validation_true, validation_pred)
adjusted = post.predict(test_pred)
cm = ClassificationMetric(test_true, adjusted,
                          unprivileged_groups=[{'sex': 0.0}],
                          privileged_groups=[{'sex': 1.0}])
```

| Postprocessor | Needs labels? | Needs scores? | Main gotcha |
| --- | --- | --- | --- |
| `EqOddsPostprocessing` | Yes | No for core optimization | Degenerate group confusion rates can make linear programming unstable. |
| `CalibratedEqOddsPostprocessing` | True labels plus prediction dataset | Yes, calibrated positive-class scores | Scores must be probabilities, not logits. |
| `RejectOptionClassification` | True labels plus prediction dataset | Yes, scores in `[0, 1]` | Threshold/margin grid and metric bounds must be feasible. |

Never fit postprocessing thresholds on the final test set when reporting final metrics.

## Deterministic reranking workflow

```python
from aif360.algorithms.postprocessing import DeterministicReranking

reranker = DeterministicReranking(
    unprivileged_groups=[{'s': 0.0}],
    privileged_groups=[{'s': 1.0}],
)
reranker.fit(scored_regression_dataset)
ranked = reranker.predict(scored_regression_dataset,
                          rec_size=20,
                          target_prop=[0.5, 0.5],
                          rerank_type='Constrained')
```

Checklist:

- Input is a `RegressionDataset`, not a binary classification dataset.
- The dataset has exactly one label/score column.
- `rec_size` is positive.
- `target_prop` length equals all unprivileged plus privileged group dictionaries.
- Protected group values match encoded dataset values; raw strings may have been mapped to floats.
- Accepted `rerank_type`: `Greedy`, `Conservative`, `Relaxed`, `Constrained`.

## Metric validation report template

For every mitigation attempt, report:

1. Selected lifecycle stage and class.
2. Dataset type, protected attributes, group dictionaries, favorable/unfavorable labels.
3. Optional extras installed or explicitly missing.
4. Baseline utility and fairness metrics.
5. Post-mitigation utility and fairness metrics.
6. Any limitations: unverified optional dependency, tiny smoke only, validation/test leakage risk, score calibration uncertainty, sparse protected groups, or unsupported intersectional configuration.
