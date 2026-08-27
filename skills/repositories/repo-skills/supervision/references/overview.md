# Supervision overview

Supervision is a Python computer-vision utility package centered on normalized
prediction containers, visual annotation, dataset conversion, video/image
utilities, tracking/keypoint helpers, and detection metrics.

## Installation lanes

| Need | Command | Notes |
| --- | --- | --- |
| Base package | `pip install supervision` | Python >=3.10. Includes core containers, annotators, datasets, media helpers, fallback backend, and assets helpers. |
| Metrics | `pip install "supervision[metrics]"` | Adds pandas for metric result tables. Use this for mAP/MAR/precision/recall/F1/confusion-matrix workflows. |
| GeoTIFF slicing | `pip install "supervision[geotiff]"` | Adds `rasterio` for `InferenceSlicer` over windowed GeoTIFF datasets. Optional. |
| Native OpenCV | `pip install opencv-python-headless supervision` or `pip install opencv-python supervision` | Optional. Supervision's fallback backend works without OpenCV; install exactly one OpenCV wheel only when the application needs native behavior, GUI windows, or webcam capture. |
| External models | Package-specific | Supervision adapters normalize model outputs; they do not install Ultralytics, Inference, Transformers, MediaPipe, Detectron2, or model weights. |

Minimal import check:

```python
import supervision as sv
print(sv.__version__)
```

Backend diagnostic only:

```python
from supervision import _cv2
print(_cv2.BACKEND_NAME)
```

Do not use `_cv2` as application API; it is a backend diagnostic.

## Core concepts

### `Detections`

`sv.Detections` is the lingua franca for detection, segmentation, OBB, OCR, VLM,
tracking, annotator, slicer, sink, dataset, and metric workflows. It stores an
`xyxy` array plus optional aligned `mask`, `confidence`, `class_id`,
`tracker_id`, `data`, and `metadata`. Store per-detection metadata in
`detections.data` as arrays/lists aligned with `xyxy`.

Important constants from `supervision.config`:

- `CLASS_NAME_DATA_FIELD` -> `"class_name"`.
- `ORIENTED_BOX_COORDINATES` -> `"xyxyxyxy"` with shape `(N, 4, 2)`.
- `AREA_DATA_FIELD` -> `"area"` for COCO/metric area metadata.

### Annotators

High-level annotators accept `scene` plus `Detections` or `KeyPoints`, draw on
the supplied scene, and return it. Use `scene.copy()` when preserving the
original frame matters.

### Datasets

`DetectionDataset` loads and exports YOLO, COCO, Pascal VOC, LabelMe, and
CreateML detection datasets. `ClassificationDataset` handles folder-structure
classification datasets. Dataset conversion should preserve class ids and class
names deliberately.

### Tracking and keypoints

`KeyPoints` stores skeleton rows and per-anchor coordinates/visibility. Most
tracking, line-zone, trace, and tracker-label workflows operate on `Detections`
with stable `tracker_id`. Convert keypoints to detections when tracking pose.
`sv.ByteTrack` is deprecated; prefer the external `trackers` package when
available.

### Metrics

Use `supervision.metrics` classes for mAP, mAR, precision, recall, and F1.
Use `sv.ConfusionMatrix` or `supervision.metrics.detection.ConfusionMatrix` for
confusion matrices. Metrics are class-aware and usually require prediction
`confidence` and both-side `class_id`.

### Media utilities

Image, video, drawing, geometry, file, notebook, and assets helpers are support
workflows. They are separate from high-level annotators so a task can choose
between primitive drawing and detection-aware visualization.

## Sub-skill route map

| Sub-skill | Read when |
| --- | --- |
| [detection-and-zones](../sub-skills/detection-and-zones/SKILL.md) | `Detections`, model/VLM adapters, masks, compact masks, filters, NMS/NMM, zones, slicer, smoother, CSV/JSON sinks. |
| [annotators](../sub-skills/annotators/SKILL.md) | Drawing boxes, masks, labels, traces, heatmaps, zone overlays, comparison panels, or other high-level `scene` + detections visualizations. |
| [datasets](../sub-skills/datasets/SKILL.md) | Loading, splitting, merging, and converting YOLO/COCO/VOC/LabelMe/CreateML detection datasets or classification folder datasets. |
| [tracking-keypoints](../sub-skills/tracking-keypoints/SKILL.md) | `KeyPoints`, keypoint annotators, `tracker_id`, tracking, line-crossing identity, ByteTrack migration, and keypoint deprecations. |
| [metrics](../sub-skills/metrics/SKILL.md) | mAP, MAR, precision, recall, F1, confusion matrices, metric targets, and dataset-backed evaluation loops. |
| [media-utils](../sub-skills/media-utils/SKILL.md) | Image/video/file/draw/geometry/notebook/assets helpers, OpenCV fallback/native backend, codecs, and windows. |

## Deprecation reminders

- Use `supervision.key_points` or top-level `sv.KeyPoints`, not
  `supervision.keypoint`.
- Use `keypoint_confidence`, not `KeyPoints.confidence`, in new code.
- Prefer external `trackers.ByteTrackTracker` over deprecated `sv.ByteTrack`
  when the external package is available.
- Prefer `sv.VLM` and `Detections.from_vlm` over deprecated `sv.LMM` and
  `from_lmm`.
- Avoid deprecated `create_tiles` and validation shims in new code unless the
  task is compatibility repair.

## Maintainer/contributor hints

For code changes in this repository, follow the package's existing patterns:

- Source lives under `src/supervision/`; tests mirror source under `tests/`.
- Public exports are controlled by `src/supervision/__init__.py`.
- Heavy optional framework imports should stay lazy inside the function that
  needs them.
- Use vectorized NumPy operations in hot paths and constants from
  `supervision.config` for data-field keys.
- New/modified functions and tests should have docstrings and type hints.

These maintainer hints are included for context. Runtime package-usage tasks
should route through the sub-skills above rather than reopen the source tree.
