---
name: box-ensembling
description: "Route 2D normalized box ensembling tasks with weighted boxes
  fusion, NMS, Soft-NMS, non-maximum weighted suppression, and the experimental
  vectorized WBF variant."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Box ensembling

Use this sub-skill for 2D object-detection prediction ensembling only. It works
with normalized `[x1, y1, x2, y2]` boxes, per-model scores and labels, model
weights, IoU thresholds, confidence modes, and sorted output arrays.

Use it when you need to:

- merge YOLO, Faster R-CNN, DetectoRS, or similar detector outputs from multiple models;
- choose between WBF, NMW, NMS, or Soft-NMS for a single 2D image batch;
- validate and normalize box arrays before fusion;
- explain repeated-box score inflation or confidence-mode selection.

Do not use this sub-skill for 1D spans or 3D cuboids.

## Start here

- [API reference](references/api-reference.md)
- [Workflow recipes](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- [Smoke script](scripts/smoke_2d_ensembling.py)

## Routing rules

- Prefer `weighted_boxes_fusion` for multi-model 2D fusion when you want fused
  coordinates.
- Use `weighted_boxes_fusion_experimental` only for trusted, already-sanitized
  inputs and speed-oriented experiments.
- Use `non_maximum_weighted` when you want a weighted representative box but
  not full WBF confidence behavior.
- Use `nms`, `soft_nms`, or `nms_method` when you want hard or soft suppression
  instead of coordinate averaging.
- Normalize raw pixel boxes before calling the library. The package can clip and
  swap corners, but it does not know image size.
- If repeated boxes from the same model make scores too high, prefer
  `box_and_model_avg` or `absent_model_aware_avg` and keep
  `allows_overflow=False`.

## Expected outputs

All supported functions return numpy arrays sorted by descending confidence:

- `boxes`: `(N, 4)` float array
- `scores`: `(N,)` float array
- `labels`: `(N,)` numeric labels; cast to integer if needed

Keep empty predictions as empty per-model lists so the outer model count stays
aligned.
