---
name: targets-and-formats
description: "Apply Albumentations pipelines safely to images, masks, bboxes,
  keypoints, multiple images, volumes, 3D masks, and labels without corrupting
  geometry or data formats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Targets and Formats

Use this sub-skill when a task involves Albumentations input/output keys, bbox or keypoint formats, label fields, additional targets, or 3D volume/mask targets. The central rule is: declare every geometric annotation contract in `A.Compose(...)` before calling the pipeline, then keep the data arrays and label arrays length-aligned after filtering.

## Route First

- Use `references/data-formats.md` to choose `BboxParams`, `KeypointParams`, bbox/keypoint formats, label fields, shape rules, and 3D target keys.
- Use `references/target-recipes.md` for copy-adaptable recipes covering detection, keypoints, segmentation, additional targets, multi-image inputs, and volumes.
- Use `references/troubleshooting.md` when a pipeline drops boxes/keypoints, rejects shapes, misreads YOLO boxes, or loses labels.
- Use `scripts/validate_targets.py` for a small local preflight of bbox/keypoint JSON fixtures and optional volume/mask3d shapes before debugging a full training dataset.

## Required Composition Contracts

- Bboxes require `bbox_params=A.BboxParams(...)` whenever the call includes `bboxes`; keypoints require `keypoint_params=A.KeypointParams(...)` whenever the call includes `keypoints`.
- `BboxParams(format=...)` accepts `"coco"`, `"pascal_voc"`, `"albumentations"`, or `"yolo"`; Albumentations internally transforms bboxes as normalized `[x_min, y_min, x_max, y_max]`.
- `KeypointParams(format=...)` accepts `"xy"`, `"yx"`, `"xya"`, `"xys"`, `"xyas"`, `"xysa"`, or `"xyz"`; Albumentations internally transforms keypoints as `[x, y, z, angle, scale]`.
- Labels that must be filtered with bboxes/keypoints belong in `label_fields`, for example `label_fields=["class_labels"]` or `label_fields=["keypoint_labels"]`.
- 3D volumes use `volume` or `volumes`; 3D masks use `mask3d` or `masks3d`; shape checking expects `D,H,W[,C]` for single volumes and `N,D,H,W[,C]` for batches.

## Safe Defaults

- Use `strict=True` while developing to catch unknown input keys and invalid transform arguments early; route general Compose behavior to `../pipeline-composition/`.
- Keep `is_check_shapes=True` unless a dataset intentionally supplies nonmatching spatial targets and the code handles that explicitly.
- For detection data with messy boxes, prefer `clip=True, filter_invalid_bboxes=True` and a conservative `min_visibility` or `min_area` rather than silently trusting source annotations.
- For keypoints near crop borders, set `remove_invisible=False` only if downstream code can handle off-image coordinates; otherwise preserve label alignment via `label_fields` and accept filtering.
- For tensor conversion and channel-order decisions, route to `../framework-integration/`; for transform family selection, route to `../transform-catalog/`; for save/load/replay, route to `../serialization-and-reproducibility/`.
