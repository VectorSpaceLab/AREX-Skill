---
name: tabular-label-issues
description: "Route multi-label classification and regression label-issue
  workflows for cleanlab."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Tabular label issues

Use this sub-skill when the task is about nonstandard tabular labels: multi-label classification with labels as list-of-lists, or regression with numeric targets.

## Route here for
- Multi-label issue finding, per-class ranking, and dataset-health helpers.
- Regression `CleanLearning` workflows and regression label-quality scoring.
- Direct module APIs for these workflows.
- `Datalab(task="multilabel")` and `Datalab(task="regression")` only as cross-reference when the user wants the broader audit route.

## Route elsewhere
- Standard single-label binary/multiclass noisy-label cleanup -> [`../classification/SKILL.md`](../classification/SKILL.md).
- Full dataset audits, `lab.find_issues(...)`, or multiple issue families -> [`../datalab/SKILL.md`](../datalab/SKILL.md).
- Token, object-detection, or segmentation label issues -> [`../structured-label-issues/SKILL.md`](../structured-label-issues/SKILL.md).
- Multiannotator consensus or annotator-quality workflows -> [`../multiannotator/SKILL.md`](../multiannotator/SKILL.md).
- Standalone outlier scoring -> [`../outlier/SKILL.md`](../outlier/SKILL.md).
- Experimental helpers and span classification -> [`../experimental/SKILL.md`](../experimental/SKILL.md).

## Core contract
- Multilabel labels are `List[List[int]]` with zero-based class IDs.
- Multilabel `pred_probs` are `np.ndarray` with shape `(N, K)` and need not sum to 1 across rows.
- Use `find_label_issues` and `get_label_quality_scores` to flag and rank suspicious multilabel examples.
- Use `find_multilabel_issues_per_class` when you need per-class issue masks or ranked indices.
- Use `rank_classes_by_multilabel_quality`, `common_multilabel_issues`, `overall_multilabel_health_score`, and `multilabel_health_summary` for class-level and dataset-level summaries.
- Regression labels/targets are numeric 1D arrays.
- Use `cleanlab.regression.rank.get_label_quality_scores` for scored numeric predictions and `CleanLearning` when you want issue detection plus refitting.
- Regression `CleanLearning.find_label_issues(...)` returns a DataFrame with `is_label_issue`, `label_quality`, `given_label`, and `predicted_label`.
- Lower scores always mean more suspect labels.

## Datalab cross-reference
- `Datalab(..., task="multilabel")` and `Datalab(..., task="regression")` use the same tabular label semantics but expose the broader audit router.
- Use the direct module APIs when the only question is label quality.
- Use Datalab when you also need other issue types or a dataset-wide report.
- Datalab issue tables use `label_score`; direct regression `CleanLearning` uses `label_quality`.

## Read/run next
- Read [`references/api-reference.md`](references/api-reference.md) when you need exact multilabel/regression signatures, return values, and Datalab task parallels.
- Read [`references/data-formats.md`](references/data-formats.md) before constructing list-of-lists multilabel inputs or numeric regression targets.
- Read [`references/multilabel.md`](references/multilabel.md) when the task is multilabel issue finding, ranking, or dataset health.
- Read [`references/regression.md`](references/regression.md) when the task is numeric target-quality scoring or regression `CleanLearning` refitting.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) when shape, label-format, target, scoring, or task-route failures occur.
- Run [`scripts/smoke_tabular_label_issues.py`](scripts/smoke_tabular_label_issues.py) to verify tiny multilabel and regression paths.
