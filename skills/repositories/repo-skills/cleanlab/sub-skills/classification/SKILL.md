---
name: classification
description: "Route standard multiclass and binary noisy-label workflows for cleanlab."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# classification

Use this sub-skill for standard single-label binary or multiclass workflows centered on noisy labels,
cross-validated predicted probabilities, label-quality scoring, class-level dataset health,
latent/noise-matrix estimation, and synthetic noise benchmarks.

## Route here for

- `CleanLearning` fit/predict/get_label_issues workflows.
- Direct label-issue finding or ranking from `pred_probs`.
- Cross-validated predicted probabilities and latent noise estimation.
- Dataset health summaries, class overlap, and overall label-quality scores.
- Data valuation with `data_shapley_knn`.
- Benchmark noise generation with the synthetic noise helpers.

## Route elsewhere for

- Dataset audits that span multiple issue types -> [`../datalab/SKILL.md`](../datalab/SKILL.md).
- Outlier or OOD scoring from features or `pred_probs` alone -> [`../outlier/SKILL.md`](../outlier/SKILL.md).
- Multiannotator consensus, annotator quality, or active learning -> [`../multiannotator/SKILL.md`](../multiannotator/SKILL.md).
- Multi-label or regression label issues -> [`../tabular-label-issues/SKILL.md`](../tabular-label-issues/SKILL.md).
- Token, object-detection, or segmentation label issues -> [`../structured-label-issues/SKILL.md`](../structured-label-issues/SKILL.md).
- Explicitly unstable/deep-learning experimental helpers, including the batched low-memory helper itself -> [`../experimental/SKILL.md`](../experimental/SKILL.md).

## Operating rules

- Labels must be zero-based integers for the standard multiclass/binary route.
- `pred_probs` must be out-of-sample, aligned to the same examples, and ordered by class index.
- If you do not already have out-of-sample `pred_probs`, compute them with cross-validation first.
- Keep the classifier sklearn-compatible and clonable when using `CleanLearning`.
- If the user wants a full dataset audit, do not force this route; hand off to `datalab`.

## Read/run next

- Read [`references/api-reference.md`](references/api-reference.md) when you need signatures, return shapes, or function ownership for the classification APIs.
- Read [`references/workflows.md`](references/workflows.md) when you need a concrete `pred_probs`, `CleanLearning`, dataset-health, noise-estimation, or benchmarking recipe.
- Read [`references/data-valuation.md`](references/data-valuation.md) when the task asks for KNN-Shapley/data-valuation scores.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) when imports, labels, `pred_probs`, sklearn estimator compatibility, or cross-validation fail.
- Run [`scripts/smoke_classification.py`](scripts/smoke_classification.py) to verify a tiny deterministic classification, dataset-health, noise-generation, and data-valuation path.
