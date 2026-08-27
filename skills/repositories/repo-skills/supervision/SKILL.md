---
name: supervision
description: "Route Supervision computer-vision package workflows for
  detections, annotators, datasets, tracking, metrics, and media utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Supervision

Use this repo skill when a task uses the `supervision` Python package as a
computer-vision utility layer: normalized detections, visual annotation, dataset
conversion, tracking/keypoints, evaluation metrics, image/video helpers, zones,
sinks, slicers, and optional OpenCV backend behavior.

## Install and minimal check

```bash
pip install supervision
python -c "import supervision as sv; print(sv.__version__)"
```

Add extras only for workflows that need them:

```bash
pip install "supervision[metrics]"   # pandas-backed metric tables and evaluation
pip install "supervision[geotiff]"   # rasterio/windowed GeoTIFF slicing
```

Native OpenCV is optional. Use Supervision's fallback backend by default; install
exactly one OpenCV wheel only when the application needs native OpenCV behavior,
GUI windows, webcam capture, or broader codec compatibility.

Run the bundled [check_supervision_install.py](scripts/check_supervision_install.py)
helper when the environment is unknown.

## Start here

- Read [overview](references/overview.md) for the package map, core concepts,
  optional extras, and deprecation summary.
- Read [troubleshooting](references/troubleshooting.md) for cross-cutting
  install/import/backend/deprecation failures.
- Read [repo provenance](references/repo-provenance.md) before deciding whether
  this skill matches a different checkout or package version.

## Route by task

| User intent or signals | Sub-skill |
| --- | --- |
| `Detections`, model adapters, VLM parsing, compact masks, filtering, NMS/NMM, zones, tiled inference, smoothing, CSV/JSON sinks | [detection-and-zones](sub-skills/detection-and-zones/SKILL.md) |
| Drawing boxes, masks, labels, traces, heatmaps, zones, comparison panels, and other high-level `scene` + detections/keypoints visualization | [annotators](sub-skills/annotators/SKILL.md) |
| YOLO/COCO/Pascal VOC/LabelMe/CreateML dataset loading/export, dataset splitting/merging, classification folder datasets | [datasets](sub-skills/datasets/SKILL.md) |
| `KeyPoints`, keypoint adapters/annotators, keypoint-to-detection conversion, tracker IDs, ByteTrack compatibility/migration, line crossing with identity | [tracking-keypoints](sub-skills/tracking-keypoints/SKILL.md) |
| mAP, mAR, precision, recall, F1, confusion matrices, `MetricTarget`, `AveragingMethod`, dataset-backed evaluation | [metrics](sub-skills/metrics/SKILL.md) |
| Image/video/file helpers, primitive drawing, colors, geometry, notebook display, assets, OpenCV fallback/native backend, GUI/windows, codecs | [media-utils](sub-skills/media-utils/SKILL.md) |

## Operating principles

1. Treat `sv.Detections` as the shared object between model adapters, filters,
   zones, trackers, annotators, datasets, sinks, slicers, and metrics.
2. Keep aligned arrays aligned. Filter the container object, not individual
   `xyxy`, `confidence`, `class_id`, `mask`, `tracker_id`, or `data` arrays.
3. Import metadata keys from `supervision.config` when writing reusable code:
   `CLASS_NAME_DATA_FIELD`, `ORIENTED_BOX_COORDINATES`, and `AREA_DATA_FIELD`.
4. Keep heavy optional model/framework imports lazy and model-specific.
   Supervision adapters convert already-produced results; they do not download
   models or install external frameworks.
5. Use `scene.copy()` before annotation when the original image or frame must be
   preserved. Annotators draw on the provided scene and return it.
6. Prefer current APIs: `supervision.key_points`/`sv.KeyPoints`,
   `keypoint_confidence`, `sv.VLM`, and `Detections.from_vlm`. Treat
   `supervision.keypoint`, `KeyPoints.confidence`, `sv.ByteTrack`, `sv.LMM`, and
   `from_lmm` as compatibility or migration topics.
7. Do not rely on original repository docs, examples, tests, notebooks, scripts,
   or local checkout files as runtime dependencies. The necessary operating
   guidance is distilled into this skill tree.

## Common route combinations

- **Annotate model output:** use `detection-and-zones` to normalize raw results
  into `Detections`, then `annotators` to draw on images or video frames.
- **Evaluate a dataset:** use `datasets` to load/convert annotations,
  `detection-and-zones` to normalize predictions, and `metrics` to compute and
  interpret scores.
- **Count objects in video zones:** use `media-utils` for video frames,
  `detection-and-zones` for `PolygonZone`/`LineZone`, `tracking-keypoints` when
  stable `tracker_id` is needed, and `annotators` for overlays.
- **Debug backend/image/video issues:** use `media-utils` first, then return to
  the workflow sub-skill that owns the higher-level operation.
