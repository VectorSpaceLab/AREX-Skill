---
name: transform-catalog
description: "Select and parameterize Albumentations 2D transform families,
  including pixel, crop, resize, geometric, dropout, mixing/domain adaptation,
  spectrogram, text, target support, interpolation, and fill behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Transform Catalog

Use this sub-skill when an agent needs to choose Albumentations 2D transforms, translate older parameter names to Albumentations 2.x, or decide whether a transform is safe for images, masks, segmentation, detection, keypoints, spectrograms, text rendering, or domain-adaptation workflows.

## Route by task

- Use `references/transform-reference.md` for transform families, representative APIs, target support, v2 parameter names, interpolation, `fill`/`fill_mask`, and metadata requirements.
- Use `references/recipes.md` for copy-adaptable pipelines: classification, segmentation-safe geometry, detection/keypoints routing, normalization, dropout, domain adaptation, spectrograms, and text overlays.
- Use `references/troubleshooting.md` when constructor validation fails, old v1 names appear, masks get corrupted, dtype/range assumptions break, metadata is missing, text rendering fails, or OpenCV interpolation/fill constraints are unclear.
- Use `scripts/transform_probe.py` to inspect an installed Albumentations transform signature, map common deprecated parameter names, or run a tiny image/mask smoke probe.

## Boundaries

- For `Compose`, `ReplayCompose`, probabilities across groups, strict validation, seeds, additional targets, and pipeline operator edits, route to `../pipeline-composition/`.
- For bbox/keypoint formats, label fields, coordinate normalization, 3D volumes, and target validation, route to `../targets-and-formats/`.
- For PyTorch tensor conversion, `ToTensorV2`, `ToTensor3D`, dataset placement, and channel order, route to `../framework-integration/`.
- For saving/loading pipelines, replay dictionaries, and non-serializable transforms, route to `../serialization-and-reproducibility/`.

## Quick defaults

- For segmentation masks, prefer geometry transforms that declare mask support and keep masks nearest-neighbor: `mask_interpolation=cv2.INTER_NEAREST` and class-safe `fill_mask` values.
- For pixel-only color/noise/weather transforms, apply only to images; do not expect masks, bboxes, or keypoints to change.
- In Albumentations 2.x, use `fill` and `fill_mask` instead of old `value` and `mask_value`, and use tuple range parameters such as `num_holes_range`, `hole_height_range`, and `hole_width_range` instead of old min/max dropout names.
- For domain adaptation and mixing transforms, pass required per-sample metadata arrays through the transform call, not source-repo paths or lazy file handles.
