---
name: metrics
description: "Routes Ignite metric attachment, arithmetic, family-specific
  evaluation, and compute/reset workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Ignite metrics workflows

Use this sub-skill when the task is about computing, validating, combining, or troubleshooting Ignite metrics rather than the training loop itself.

## Include here

- Metric attachment to an evaluator or custom engine, including `output_transform`, `skip_unrolling`, and distributed metric reduction behavior.
- Direct `reset` / `update` / `compute` usage for custom or ad hoc evaluation loops.
- Metric arithmetic with `MetricsLambda`, operator chaining, indexing, and derived metrics such as F-beta.
- Core classification metrics: `Accuracy`, `Precision`, `Recall`, `Fbeta`, `ConfusionMatrix`, `TopKCategoricalAccuracy`, `ClassificationReport`, `AveragePrecision`, `PrecisionRecallCurve`, `ROC_AUC`, and `RocCurve`.
- Regression, clustering, and distance metrics that live under `ignite.metrics.regression` and `ignite.metrics.clustering`.
- NLP, vision, GAN, fairness, and recommender-system metrics, including `Bleu`, `Rouge`, `SSIM`, `FID`, `InceptionScore`, `GpuInfo`, `SubgroupAccuracyDifference`, `DemographicParityDifference`, `HitRate`, and `NDCG`.
- Metric grouping and reuse patterns with `MetricGroup`.

## Exclude or route elsewhere

- Engine creation, event wiring, resume logic, and deterministic loop control belong in `sub-skills/engine/`.
- Checkpointing, schedulers, progress bars, profilers, and logger integrations belong in `sub-skills/handlers/`.
- Distributed launchers and backend selection belong in `sub-skills/distributed/`.
- Legacy `ignite.contrib` compatibility notes live in `references/legacy-contrib.md`.

## Start here

- Read `references/api-reference.md` for the metric families, dependencies, and shape expectations.
- Read `references/workflows.md` for end-to-end evaluator recipes, derived-metric patterns, and family-specific examples.
- Read `references/troubleshooting.md` when a metric raises `NotComputableError`, shape errors, missing optional dependency errors, or distributed reduction surprises.
- Run `scripts/metric_smoke.py` for a tiny synthetic check that exercises classification, binary ranking, fairness, image, and recommender-style metrics.

## Common triggers

- "How do I attach Accuracy, F-beta, ROC AUC, or SSIM to Ignite?"
- "Why does `NotComputableError` happen for this metric?"
- "How do I build a derived metric from Precision and Recall?"
- "Which optional dependency do I need for FID, ROC AUC, or GPU info?"
- "How do I evaluate subgroup fairness or recommender-system metrics?"

## Useful boundary notes

This route owns metric math and metric-specific validation, but it does not own the trainer/evaluator structure itself. If the metric is part of a larger loop or a checkpoint/logging problem, keep the loop in `sub-skills/engine/` and the side effects in `sub-skills/handlers/`.
