---
name: three-d-box-fusion
description: "Fuse normalized 3D cuboid detections with weighted_boxes_fusion_3d."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# three-d-box-fusion

Use this sub-skill when you need to combine **normalized 3D axis-aligned cuboids** from multiple detectors with `weighted_boxes_fusion_3d`.

## Use for

- Fusing LiDAR, medical, or volumetric detector boxes that are already in a common normalized scene range.
- Choosing between `conf_type='avg'` and `conf_type='max'` for 3D fusion.
- Checking the returned `boxes`, `scores`, and `labels` arrays.
- Confirming coordinate order, weight handling, and threshold behavior for 3D WBF.

## Do not use for

- 2D box ensembling, NMS, Soft-NMS, or non-maximum weighted fusion.
- 1D interval or span fusion.
- Dataset-specific coordinate conversion or visualization workflows.
- Any 3D NMS/NMW helper: this package does not provide one.

## Expected inputs

- `boxes_list`: one list per model, each box in `[x1, y1, z1, x2, y2, z2]` order.
- `scores_list`: one confidence score list per model.
- `labels_list`: one numeric label list per model.
- Optional `weights`, `iou_thr`, `skip_box_thr`, `conf_type`, and `allows_overflow`.

## Output contract

- `boxes`: fused boxes as an `(N, 6)` NumPy array.
- `scores`: fused confidences as an `(N,)` NumPy array.
- `labels`: numeric labels as an `(N,)` NumPy array.
- Outputs are sorted by confidence descending.

## Routing hints

- If the task is 2D, route to the sibling 2D sub-skill.
- If the task is 1D, route to the sibling 1D sub-skill.
- If the task mentions metric LiDAR boxes, normalize them to a common `[0, 1]` scene range first, then fuse.
- If the task asks for unsupported 3D confidence names such as `absent_model_aware_avg`, fall back to `avg` and explain that 3D WBF accepts only `avg` and `max`.

## Bundled guidance

- [API reference](references/api-reference.md)
- [Workflows](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- [Smoke script](scripts/smoke_3d_fusion.py)
