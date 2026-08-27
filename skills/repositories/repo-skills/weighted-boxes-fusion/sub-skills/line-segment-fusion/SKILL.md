---
name: line-segment-fusion
description: "Use weighted_boxes_fusion_1d for normalized 1D spans, token-span
  ensembling, and NLP/NER postprocessing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Line Segment Fusion

Use this sub-skill when the task is to ensemble normalized 1D intervals with `weighted_boxes_fusion_1d`.

## Use this for
- Merging token spans or `predictionstring` intervals from several NLP models.
- Converting string class labels to numeric labels before fusion, then mapping fused labels back.
- Tuning `iou_thr`, `skip_box_thr`, model `weights`, `conf_type`, and `allows_overflow` for 1D span ensembling.
- Working with normalized `[x1, x2]` spans where `x1 <= x2` and the coordinates live in `[0, 1]`.

## Do not use this for
- 2D box ensembling.
- 3D cuboid fusion.
- Full benchmark reproduction as the default path.

## Start here
- [API reference](references/api-reference.md)
- [Workflow recipes](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- [Smoke script](scripts/smoke_1d_fusion.py)
