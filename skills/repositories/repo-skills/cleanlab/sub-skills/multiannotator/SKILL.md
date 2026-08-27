---
name: multiannotator
description: "Route cleanlab workflows for consensus labeling, annotator
  quality, and active learning on multi-annotator classification data."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Multiannotator

Use this sub-skill when examples can have multiple annotators, you need a consensus label, or you want to prioritize relabeling.

## Route here for
- Convert long annotation tables into the wide matrix expected by `cleanlab.multiannotator`.
- Compute majority-vote or best-quality consensus labels from raw annotations plus a trained classifier's `pred_probs`.
- Inspect per-example quality, detailed per-annotator scores, annotator stats, and optional crowdlab weights.
- Rank labeled and unlabeled examples for relabeling with ActiveLab scores.
- Use the ensemble variants when you already have stacked predictions from several trained classifiers.

## Reroute elsewhere
- Single-annotator noisy-label workflows, model training, or predicted-probability generation: use [`../classification/SKILL.md`](../classification/SKILL.md).
- If you need the classifier that supplies `pred_probs`, stay in the classification route for the model-training side.
- Broader dataset auditing, issue managers, or custom Datalab workflows: use [`../datalab/SKILL.md`](../datalab/SKILL.md).
- Standalone outlier/OOD scoring: use [`../outlier/SKILL.md`](../outlier/SKILL.md).
- Multi-label/regression or structured-output label issues: use [`../tabular-label-issues/SKILL.md`](../tabular-label-issues/SKILL.md) or [`../structured-label-issues/SKILL.md`](../structured-label-issues/SKILL.md).
- Explicitly unstable helpers: use [`../experimental/SKILL.md`](../experimental/SKILL.md).

## What to expect
- `label_quality` includes consensus label, consensus quality score, annotator agreement, and annotation count.
- `consensus_method` can be a single method or a list; extra methods add suffixed columns such as `consensus_label_best_quality`.
- `detailed_label_quality` uses `quality_annotator_<annotator id>` columns.
- `annotator_stats` reports annotator quality, agreement with consensus, worst class, and labeled-example counts.
- `return_weights=True` only works with `quality_method="crowdlab"` for the single-model API.
- `get_majority_vote_label`, `get_label_quality_multiannotator`, and the active-learning helpers all accept DataFrame or ndarray inputs with `NaN` / `pd.NA` for missing labels.

## Read/run next
- Read [`references/api-reference.md`](references/api-reference.md) when you need exact function signatures, return keys, and output table columns.
- Read [`references/workflows.md`](references/workflows.md) when converting long annotation tables, computing consensus labels, or ranking relabeling candidates.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) when annotation matrices, missing values, consensus methods, weights, or active-learning scores fail.
- Run [`scripts/smoke_multiannotator.py`](scripts/smoke_multiannotator.py) to verify a tiny long-to-wide, consensus, annotator-stats, and active-learning path.
