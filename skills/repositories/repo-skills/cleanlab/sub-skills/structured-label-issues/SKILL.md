---
name: structured-label-issues
description: "Route cleanlab token classification, object detection, and
  semantic segmentation label-issue workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
  root-skill: cleanlab
license: Apache 2.0
---

# Structured Label Issues

Use this sub-skill for cleanlab workflows where each dataset example has structured labels rather than one scalar label:

- **Token classification**: each sentence/document is a list of tokens with one class label and one probability vector per token.
- **Object detection**: each image has annotated bounding boxes/classes and detector predictions grouped by class.
- **Semantic segmentation**: each image has a pixel mask and per-pixel class probabilities.

Keep this file as a router. Read the bundled references for schemas, API calls, and troubleshooting before writing code.

## Route quickly

| User asks for | Route here? | First reference |
|---|---:|---|
| Named-entity recognition, POS tagging, or other per-token labels | Yes | [`references/token-classification.md`](references/token-classification.md) |
| Finding/ranking/displaying token label issues | Yes | [`references/token-classification.md`](references/token-classification.md) |
| Object-detection label issues, bounding-box ranking, or box visualization | Yes | [`references/object-detection.md`](references/object-detection.md) |
| Semantic-segmentation mask label issues or pixel/image ranking | Yes | [`references/segmentation.md`](references/segmentation.md) |
| Exact input schemas for all three families | Yes | [`references/data-formats.md`](references/data-formats.md) |
| Function signatures and return types | Yes | [`references/api-reference.md`](references/api-reference.md) |
| Shape/schema/backend failures | Yes | [`references/troubleshooting.md`](references/troubleshooting.md) |

## Route elsewhere

- If the user asks about **span classification** specifically, route to the sibling `experimental` sub-skill (`../experimental/`). Span classification is intentionally not owned here.
- If the user wants a **broad audit across one dataset** with many issue types or a single audit/report wrapper, route to the sibling `datalab` sub-skill (`../datalab/`). Use this sub-skill only when the user wants the direct task-specific token/object/segmentation APIs.
- For standard multiclass/binary classification, use [`../classification/SKILL.md`](../classification/SKILL.md).
- For multilabel classification or regression labels, use [`../tabular-label-issues/SKILL.md`](../tabular-label-issues/SKILL.md).
- For multi-annotator consensus/quality, use [`../multiannotator/SKILL.md`](../multiannotator/SKILL.md).
- For out-of-distribution or outlier scoring, use [`../outlier/SKILL.md`](../outlier/SKILL.md).

## Operating workflow

1. Identify the structured-output family: token classification, object detection, or semantic segmentation.
2. Validate data format first. Most failures are nested-list length mismatches, class-order mismatches, wrong bounding-box schema, or mask/probability shape errors.
3. Prefer out-of-sample model predictions/probabilities when available. Cleanlab scores are most meaningful when predictions were not obtained from a model fit on the same labels without cross-validation/holdout safeguards.
4. Use the family-specific `filter.find_label_issues` function when the user wants estimated issues; use `rank.get_label_quality_scores` plus `issues_from_scores` when the user wants ranking/thresholding control.
5. Use summary/visualization helpers only after confirming optional plotting dependencies are available or setting a non-interactive matplotlib backend for scripts and CI.
6. Interpret outputs at the right level: token tuples for token classification, image-level masks/indices plus per-box helper scores for object detection, and pixel masks plus image-level summaries for segmentation.

## Bundled helper

Run [`scripts/smoke_structured_label_issues.py`](scripts/smoke_structured_label_issues.py) to exercise deterministic tiny fixtures for all three families. It is distilled from the public tutorials and native tests rather than copied from a source script: tutorial notebooks require external downloads/interactive visualization, while native pytest files are test harnesses rather than safe reusable runtime helpers.
