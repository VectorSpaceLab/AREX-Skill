---
name: data-preparation
description: "Prepares and validates PaddleDetection COCO, VOC, WIDER, MOT,
  keypoint, custom, semi-supervised, and sliced-image datasets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data Preparation

Use this route for annotation conversion, dataset directory layout, label lists, custom readers, COCO/VOC/MOT/keypoint data, semi-supervised splits, or small-object slicing.

## Workflow

1. Decide the task and schema before touching files: detection/instance segmentation, keypoint, MOT, rotated detection, or industrial pipeline input.
2. Choose the matching dataset config under the target checkout's `configs/datasets/` and record its dataset root, image directory, annotation path, category/label source, metric, and `num_classes`.
3. Validate a tiny sample with [`scripts/validate_detection_dataset.py`](scripts/validate_detection_dataset.py) before downloading full data or starting workers.
4. For custom annotations, prefer COCO JSON or VOC XML. Use the documented converter command patterns in [`references/conversion-workflows.md`](references/conversion-workflows.md); keep the source data and generated annotations separate.
5. For MOT, verify `images/`, `labels_with_ids/`, sequence metadata, normalized boxes, class IDs, and identity IDs. For keypoints, verify the keypoint order and visibility convention.
6. For semi-supervised or sliced datasets, make the output directory explicit and preserve the random seed, percent, slice size, overlap, and merge method.

## Schema rules

- COCO detection boxes are `[x, y, width, height]`; image IDs and category IDs must be consistent.
- VOC XML boxes are corner coordinates `xmin, ymin, xmax, ymax`; label names must match the label list/config.
- MOT labels use `[class, identity, x_center, y_center, width, height]` normalized to image dimensions; `identity=-1` means unknown.
- COCO keypoints use triples `[x, y, visibility]` in the model's expected order; missing/unlabeled points use the documented zero convention.

Read [`references/data-formats.md`](references/data-formats.md), [`references/conversion-workflows.md`](references/conversion-workflows.md), and [`references/troubleshooting.md`](references/troubleshooting.md) before launching training. Download helpers are network/large-data operations and are not run by the bundled validator.
