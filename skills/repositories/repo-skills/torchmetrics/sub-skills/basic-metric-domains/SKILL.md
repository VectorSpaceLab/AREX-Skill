---
name: basic-metric-domains
description: "Use TorchMetrics classification, regression, retrieval,
  clustering, nominal, and aggregation metrics with the right shapes and
  parameters."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Basic Metric Domains

Use this sub-skill when the task is about a standard tensor-based TorchMetrics family rather than a custom metric or a model-backed metric.

## Route map

- Read [references/basic-domains-api.md](references/basic-domains-api.md) when you need constructor arguments, input shapes, return types, or family-specific parameter meanings for classification, regression, retrieval, clustering, nominal, and aggregation metrics.
- Read [references/domain-workflows.md](references/domain-workflows.md) when you need copyable usage patterns for binary/multiclass/multilabel classification, regression, retrieval queries, clustering labels, or nominal association scores.
- Read [references/troubleshooting.md](references/troubleshooting.md) when shapes, labels, indices, empty groups, optional clustering dependencies, or reduction settings go wrong.
- Run [scripts/basic_domain_metric_smoke.py](scripts/basic_domain_metric_smoke.py) for a no-download sanity check against representative metrics from each family.

## What this sub-skill covers

- Classification: `Accuracy`, `AUROC`, `F1Score`, `Precision`, `Recall`, `ConfusionMatrix`, calibration, hinge, Jaccard, Matthews correlation, and task-specific `Binary*`, `Multiclass*`, and `Multilabel*` classes.
- Regression: `MeanSquaredError`, `MeanAbsoluteError`, `R2Score`, `PearsonCorrCoef`, `SpearmanCorrCoef`, `KLDivergence`, `JensenShannonDivergence`, `ContinuousRankedProbabilityScore`, and related scalar reduction metrics.
- Retrieval: grouped-query metrics such as `RetrievalNormalizedDCG`, `RetrievalMAP`, `RetrievalPrecision`, `RetrievalRecall`, `RetrievalMRR`, and friends.
- Clustering: `ClusterAccuracy` and unsupervised clustering scores.
- Nominal/association: `CramersV`, `FleissKappa`, `PearsonsContingencyCoefficient`, `TheilsU`, and `TschuprowsT`.
- Aggregation helpers: `MeanMetric`, `SumMetric`, `RunningMean`, `RunningSum`, and related scalar accumulation helpers.

## Route elsewhere

- Read `../core-api/SKILL.md` for `Metric` lifecycle, device placement, distributed synchronization, `MetricCollection`, or custom metric states.
- Read `../vision-detection-metrics/SKILL.md` for image, segmentation, detection, or panoptic metrics.
- Read `../audio-text-metrics/SKILL.md` for waveform metrics, ASR metrics, or no-download text metrics.
- Read `../model-based-metrics/SKILL.md` for BERTScore, CLIPScore, FID, or any metric that loads pretrained assets.
- Read `../collections-wrappers-plotting/SKILL.md` for collections, wrappers, trackers, and plotting.

## Quick use

1. Choose the metric family by the shape and semantics of the inputs.
2. Match the constructor args to the task type, class count, label encoding, query grouping, or reduction mode.
3. Keep label and target shapes aligned; most families flatten additional dimensions in a documented way.
4. Check whether the metric returns a scalar, class vector, dict, or list before trying to log or plot it.
5. Install only the extra required by the family you actually need; avoid broad extras unless the task spans multiple families.

## Fast checks

- `python scripts/basic_domain_metric_smoke.py`
- `python -c "from torchmetrics.classification import Accuracy; print(Accuracy(task='multiclass', num_classes=3))"`

## Common signals

- `task=...`, `num_classes`, `num_labels`, `average`, `threshold`, `ignore_index`, `multidim_average` -> classification
- `num_outputs`, `multioutput`, `reduction` -> regression
- `indexes`, `empty_target_action`, `top_k`, `aggregation` -> retrieval
- `ClusterAccuracy`, `torch_linear_assignment` -> clustering
- `nan_strategy`, `nan_replace_value`, `bias_correction`, `mode='counts'` -> nominal
