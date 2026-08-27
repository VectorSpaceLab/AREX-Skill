---
name: ops-and-detection
description: "Use torchvision.ops for boxes, NMS, ROI pooling/alignment,
  detection helper concepts, and extension-dependent troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# TorchVision Ops And Detection

Use this sub-skill when the task needs low-level `torchvision.ops` APIs, detection box utilities, ROI/NMS behavior, detection postprocessing concepts, or diagnosis of missing custom C++ operators.

## Route first

- Use this skill for `torchvision.ops.nms`, `batched_nms`, box IoU/conversion/clipping/filtering, `masks_to_boxes`, `roi_align`, `roi_pool`, `MultiScaleRoIAlign`, FPN helpers, losses, and operator availability errors.
- Use `../models-and-weights/` for choosing or constructing high-level detection models and pretrained weights.
- Use `../training-references/` for official detection training/evaluation command patterns.
- Use `../transforms-and-tv-tensors/` for annotation-aware transform pipelines, TVTensor metadata, and bounding-box transform migration.

## Fast workflow

1. Confirm coordinate convention and tensor shapes before calling ops. Most detection model internals use `xyxy` boxes with shape `[N, 4]` and coordinates ordered `x1 <= x2`, `y1 <= y2`.
2. Normalize formats explicitly with `torchvision.ops.box_convert` before IoU/NMS; do not mix `xyxy`, `xywh`, and center formats in the same tensor.
3. Keep `boxes`, `scores`, `labels`, feature maps, and ROI tensors on compatible devices and dtypes; device mismatches are common when CUDA tensors meet CPU boxes.
4. Treat NMS output order as score-sorted indices, but avoid relying on deterministic tie-breaking when multiple boxes have identical scores and IoUs.
5. For ROI ops, validate feature map rank `[N, C, H, W]`, box format, batch indices, `output_size`, `spatial_scale`, and `featmap_names` before debugging model heads.
6. If an op raises `operator torchvision::nms does not exist` or a custom-ops loading error, diagnose install/build compatibility before rewriting model code.

## References

- `references/box-and-roi-ops.md`: box formats, IoU variants, NMS, masks, ROI Align/Pool, FPN, and layers/losses.
- `references/detection-helpers.md`: detection model helper concepts, postprocessing knobs, output structures, and boundaries.
- `references/troubleshooting.md`: extension, version, device, coordinate, nondeterminism, and ROI-shape failures.

## Bundled check

Run the tiny CPU smoke script to verify that import, boxes, IoU, NMS, and ROI Align work without downloads or large tensors:

```bash
python sub-skills/ops-and-detection/scripts/smoke_ops.py
```

If the script reports missing compiled ops, follow `references/troubleshooting.md` rather than treating it as a model-definition issue.
