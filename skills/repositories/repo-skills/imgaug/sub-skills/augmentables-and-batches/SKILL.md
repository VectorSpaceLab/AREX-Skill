---
name: augmentables-and-batches
description: "Use when applying imgaug transforms to keypoints, boxes, polygons,
  line strings, heatmaps, segmentation maps, or mixed batches."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Augmentables and Batches

Use this sub-skill when the task involves applying imgaug transforms to images **and aligned non-image data**: keypoints, bounding boxes, polygons, line strings, heatmaps, segmentation maps, or `Batch`/`UnnormalizedBatch` containers.

## What this sub-skill covers

- Construction and validation of `KeypointsOnImage`, `BoundingBoxesOnImage`, `PolygonsOnImage`, `LineStringsOnImage`, `HeatmapsOnImage`, and `SegmentationMapsOnImage`.
- Passing aligned augmentables in the same augmenter call as images.
- Image shape metadata, coordinate projection, `on(...)`, drawing, clipping, and out-of-image handling.
- Dense heatmap versus segmentation-map semantics.
- `Batch` and `UnnormalizedBatch` workflows for mixed data and background augmentation.

## What it does not cover

- Choosing image augmenter families belongs to [`../augmentation-pipelines/SKILL.md`](../augmentation-pipelines/SKILL.md).
- Stochastic parameters, RNG, dtype helper internals, and sample data belong to [`../parameters-random-and-utilities/SKILL.md`](../parameters-random-and-utilities/SKILL.md).
- Background pool execution belongs to [`../multicore-and-diagnostics/SKILL.md`](../multicore-and-diagnostics/SKILL.md).

## Typical triggers

- “Apply affine augmentation to images and bounding boxes.”
- “How do I augment lower-resolution heatmaps or segmentation maps with images?”
- “Why are my keypoints out of image bounds after augmentation?”
- “How should I package images, boxes, and metadata into batches?”

## Fast path

1. Read [`references/augmentables-data-formats.md`](references/augmentables-data-formats.md) to choose object types and data layouts.
2. Read [`references/batch-workflows.md`](references/batch-workflows.md) when the task uses `Batch`, `UnnormalizedBatch`, or background augmentation.
3. Run [`scripts/smoke_aligned_augmentables.py`](scripts/smoke_aligned_augmentables.py) for a tiny alignment smoke.
4. Read [`references/troubleshooting.md`](references/troubleshooting.md) for shape/count mismatches, invalid polygons, dense-map interpolation, or out-of-image coordinate issues.

## Core aligned-call pattern

```python
import numpy as np
import imgaug as ia
import imgaug.augmenters as iaa

images = np.zeros((2, 64, 64, 3), dtype=np.uint8)
keypoints = [[ia.Keypoint(x=10.5, y=20.5)], [ia.Keypoint(x=30.5, y=40.5)]]
boxes = [[ia.BoundingBox(x1=5, y1=5, x2=20, y2=20)], [ia.BoundingBox(x1=8, y1=8, x2=24, y2=24)]]

seq = iaa.Sequential([iaa.Fliplr(1.0), iaa.Affine(translate_px={"x": 2})])
images_aug, keypoints_aug, boxes_aug = seq(
    images=images,
    keypoints=keypoints,
    bounding_boxes=boxes,
)
```

Use one call for all aligned data whenever possible. This ensures the same sampled geometric transform is applied to every augmentable group.

## Dense-map rules of thumb

- Heatmaps are continuous arrays; they are usually float-like and may be lower resolution than images.
- Segmentation maps are categorical; nearest-neighbor semantics are expected during resizing or spatial transforms.
- Always provide the original image `shape` to dense augmentable objects so imgaug can project coordinates correctly.

## Batch guidance

Use `UnnormalizedBatch` when a loader naturally returns flexible Python lists or arrays and you want imgaug to normalize and restore output forms. Use `Batch` when inputs are already normalized imgaug augmentable objects. For multiprocessing, combine this sub-skill with the multicore sub-skill.

## Validation mindset

A safe aligned-data smoke should assert:

1. The number of image items and annotation groups is preserved.
2. Output shapes match expectations for both images and dense maps.
3. Coordinate objects remain instances of the expected imgaug classes.
4. Out-of-image objects are explicitly clipped, removed, or allowed according to task requirements.
