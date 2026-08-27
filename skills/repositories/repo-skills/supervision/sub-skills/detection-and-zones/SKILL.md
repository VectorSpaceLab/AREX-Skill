---
name: detection-and-zones
description: "Use supervision Detections, model adapters, compact masks,
  filtering, zones, slicing, smoothing, and CSV/JSON sinks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Detection And Zones

Use this sub-skill when the task centers on detection data, model-result normalization, segmentation mask containers, filtering, overlap suppression/merging, zones, tiled inference, smoothing, or saving detections.

## Natural triggers

Route here for prompts mentioning:

- `sv.Detections`, `Detections.empty`, indexing/filtering, `data`, `metadata`, `tracker_id`, `class_name`.
- `from_ultralytics`, `from_inference`, `from_transformers`, `from_vlm`, `from_lmm`, `from_sam`, `from_sam3`, `from_tensorflow`, `from_mmdetection`, `from_detectron2`, `from_yolov5`, `from_yolo_nas`, `from_easyocr`, `from_ncnn`, or other `Detections.from_*` adapters.
- `CompactMask`, `compact_masks=True`, dense vs compact masks, mask/box/OBB geometry, `ORIENTED_BOX_COORDINATES`.
- `with_nms`, `with_soft_nms`, `with_nmm`, `OverlapFilter`, `OverlapMetric`, IoU/IoS, duplicate detections.
- `PolygonZone`, `LineZone`, count in zone, line crossing, zone trigger masks, `Position` anchors.
- `InferenceSlicer`, small object detection, tiled inference, overlap windows, GeoTIFF/windowed raster slicing.
- `DetectionsSmoother`, `CSVSink`, `JSONSink`, save detections, custom detection data serialization.

## First response routing

1. Identify the raw input type: already a `Detections`, a framework result object, a VLM response, manual NumPy arrays, or persisted rows.
2. Open [API reference](references/api-reference.md) for exact container fields, adapter signatures, constants, and tool parameters.
3. Open [workflows](references/workflows.md) for common recipes: normalization, filtering, zones, slicing, compact masks, smoothing, and CSV/JSON export.
4. Open [troubleshooting](references/troubleshooting.md) before changing code when shapes, optional dependencies, missing metadata, tracker IDs, masks, zones, or slicer behavior are unclear.

## Boundaries

Handle:

- Detection containers and aligned per-detection arrays.
- Adapter normalization from model/framework/VLM outputs into `sv.Detections`.
- Detection utility functions that transform boxes, masks, polygons, overlaps, or VLM label matching.
- Zone trigger logic and counts, including tracker-dependent line crossing.
- Slicer, smoother, CSV sink, and JSON sink behaviors.

Route elsewhere:

- Pure drawing, color styling, label layout, and annotator composition belong to the annotators sub-skill.
- Tracking identity persistence, tracker configuration, keypoint containers, and keypoint deprecations belong to the tracking-keypoints sub-skill; return here once `tracker_id` is present for `LineZone` or smoothing.
- Image/video I/O, OpenCV backend selection, media helpers, assets, and low-level geometry primitives belong to the media-utils sub-skill unless they directly affect detection boxes/masks/zones.
- Dataset format conversion and dataset splitting/merging belong to the datasets sub-skill.
- mAP/MAR/precision/recall/F1/confusion-matrix evaluation belongs to the metrics sub-skill.

## Operating defaults

- Target package facts: `supervision` 0.31.0.dev0, Python >=3.10, base install via `pip install supervision`.
- Optional model frameworks are caller-managed; Supervision adapters normalize results but do not install or download model packages.
- Optional GeoTIFF/windowed raster support needs the geotiff extra or `rasterio`.
- OpenCV native wheels are optional for the package; do not assume native OpenCV is installed when writing detection-only code.
- Prefer constants from `supervision.config` (`CLASS_NAME_DATA_FIELD`, `ORIENTED_BOX_COORDINATES`) over string literals in code that writes `detections.data`.
- Treat all detection-level fields as aligned length-`N` data; filtering must preserve alignment by indexing the `Detections` object, not by slicing only one array.
