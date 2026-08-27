---
name: datalab
description: "Route end-to-end dataset auditing with cleanlab.Datalab."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# datalab

Use this sub-skill when the user wants a unified dataset audit with `cleanlab.Datalab`.

## Use it for
- One-pass auditing across multiple issue families.
- `Datalab(...)`, `find_issues(...)`, `report(...)`, `get_issues(...)`, and `get_issue_summary(...)`.
- Classification, regression, and multilabel Datalab tasks.
- Optional image audits with `image_key` and CleanVision.
- Custom `IssueManager` workflows registered into Datalab.

## Route elsewhere
- Standard noisy-label, `CleanLearning`, `count`, `filter`, `rank`, or dataset-health workflows → [`../classification/SKILL.md`](../classification/SKILL.md).
- Standalone outlier scoring → [`../outlier/SKILL.md`](../outlier/SKILL.md).
- Multi-annotator consensus workflows → [`../multiannotator/SKILL.md`](../multiannotator/SKILL.md).
- Direct multilabel or regression label-issue workflows → [`../tabular-label-issues/SKILL.md`](../tabular-label-issues/SKILL.md).
- Token, object-detection, or segmentation label issues → [`../structured-label-issues/SKILL.md`](../structured-label-issues/SKILL.md).
- Experimental deep-learning helpers or span classification → [`../experimental/SKILL.md`](../experimental/SKILL.md).

## Core router facts
- `Datalab` accepts `task="classification"`, `task="regression"`, and `task="multilabel"`.
- `find_issues()` accepts `pred_probs`, `features`, `knn_graph`, and `issue_types`.
- `knn_graph` wins when both `knn_graph` and `features` are provided.
- `issue_types=None` means use the task default set; `issue_types={}` means do nothing.
- `report()` prints to stdout and does not return a report string.
- `get_issue_summary()` is the dataset-level view; `get_issues()` is the per-example view.
- `spurious_correlations` is image-only and lives in `get_info("spurious_correlations")`, not in `issue_summary`.

## Read/run next
- Read [`references/api-reference.md`](references/api-reference.md) when you need live-verified constructor/method signatures, task values, or output table meanings.
- Read [`references/issue-types.md`](references/issue-types.md) when deciding which issue families and inputs to request in `find_issues()`.
- Read [`references/workflows.md`](references/workflows.md) when you need complete classification, regression, multilabel, kNN-graph, image, serialization, or report recipes.
- Read [`references/custom-issue-manager.md`](references/custom-issue-manager.md) before registering a custom issue type.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) when dependencies, task names, `issue_types`, labels, images, or reports fail.
- Run [`scripts/smoke_datalab.py`](scripts/smoke_datalab.py) to verify a tiny Datalab audit and custom issue-manager path.
