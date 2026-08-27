---
name: datasets
description: "Use supervision DetectionDataset and ClassificationDataset for
  loading, splitting, merging, converting, and exporting datasets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Datasets

Use this sub-skill when a task centers on `supervision` dataset containers or
format conversion. It covers `DetectionDataset` and `ClassificationDataset` in
`supervision` 0.31.0.dev0 on Python >=3.10.

## Trigger here

- Load detection datasets with `DetectionDataset.from_yolo`, `from_coco`,
  `from_pascal_voc`, `from_labelme`, or `from_createml`.
- Export detection datasets with `as_yolo`, `as_coco`, `as_pascal_voc`,
  `as_labelme`, or `as_createml`.
- Split, merge, iterate, visualize, augment, or convert detection datasets.
- Load or export classification folder-structure datasets with
  `ClassificationDataset.from_folder_structure` or `as_folder_structure`.
- Diagnose dataset path safety, duplicate image collisions, class-id/name
  remapping, `CLASS_NAME_DATA_FIELD`, `ORIENTED_BOX_COORDINATES`, mask
  polygon/RLE behavior, or progress flags.

## Route away

- Evaluation metrics after predictions: use [metrics](../metrics/SKILL.md).
- Primitive image/video/file helpers, OpenCV backend selection, or plotting grids:
  use [media-utils](../media-utils/SKILL.md).
- `Detections` construction, framework adapters, filtering, zones, slicers, sinks,
  or low-level detection internals: use
  [detection-and-zones](../detection-and-zones/SKILL.md).
- Styling annotated images beyond quick dataset inspection: use
  [annotators](../annotators/SKILL.md).

## Start with these references

- [Data formats](references/data-formats.md) for exact layouts, loader/exporter
  methods, class-id conventions, masks, OBBs, and classification folders.
- [Workflows](references/workflows.md) for load/split/merge/convert/export and
  common dataset-processing recipes.
- [Troubleshooting](references/troubleshooting.md) for unsafe paths, COCO category
  indexing, class remapping, duplicate images, masks/RLE, shape constraints,
  progress flags, and dataset API version pinning.

## Operating rules

1. Prefer public APIs exported from `supervision` as `sv.DetectionDataset`,
   `sv.ClassificationDataset`, `sv.Detections`, and `sv.Classifications`.
2. Treat dataset image storage as path-first. Passing a dict of in-memory images
   still works but is deprecated; use list-of-paths unless a user already owns
   arrays and accepts the deprecation.
3. Assume detection dataset annotations are `Detections` keyed by the same image
   paths as the dataset image list. Constructor validation rejects key mismatches,
   non-integer `class_id`, and class ids outside `dataset.classes`.
4. After constructing or merging a `DetectionDataset`, rely on
   `detections.data["class_name"]` only as metadata derived from `classes` and
   `class_id`; do not hand-edit it without also keeping `class_id` aligned.
5. For conversion work, name source and target formats, required directories or
   JSON/YAML/XML files, whether masks are required, whether YOLO OBB mode is
   required, and whether progress bars are acceptable.
