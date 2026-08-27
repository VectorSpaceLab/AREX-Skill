---
name: object-detection-workflows
description: "Still-image object detection workflows for COCO and custom ImageAI
  YOLO models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Object Detection Workflows

Use this sub-skill when the task is still-image object detection with ImageAI:

- COCO pretrained image detection with `ObjectDetection` and RetinaNet, YOLOv3, or TinyYOLOv3 weights.
- Custom image detection with `CustomObjectDetection`, YOLOv3 or TinyYOLOv3 weights, and the matching detection config JSON.
- Detection return contracts for saved files versus arrays.
- Object crop extraction as saved paths or in-memory arrays.
- COCO `CustomObjects` filters, custom-model label filters, confidence thresholds, NMS/objectness thresholds, and display flags.

Do not use this sub-skill for video files, cameras, live streams, callbacks, or training/data conversion. Route video and camera work to sibling sub-skill `video-detection-workflows`. Route custom model training, dataset validation, and Pascal VOC-to-YOLO conversion to sibling sub-skill `custom-training-and-data`.

## What to read

- Read [references/api-reference.md](references/api-reference.md) before writing code that calls ImageAI detection APIs. It records verified signatures, model-type mapping, parameter spelling, and return shapes.
- Read [references/workflows.md](references/workflows.md) for task recipes: COCO detection, custom detection, filters, file/array output choices, extraction, and helper-script examples.
- Read [references/coco-object-classes.md](references/coco-object-classes.md) before using `CustomObjects` so labels match the loaded COCO model family.
- Read [references/troubleshooting.md](references/troubleshooting.md) when a model file, JSON config, output path, extraction directory, object filter, or threshold behaves unexpectedly.

## Safe helper

The bundled helper [scripts/detect_image.py](scripts/detect_image.py) wraps the still-image detection APIs without downloading weights or assuming the current working directory. Use it when a caller wants a repeatable command-line entry point:

```bash
python scripts/detect_image.py --help
```

The helper supports `--mode coco|custom`, COCO/custom model-type validation, explicit model/config paths, file versus array outputs, extraction, threshold/display flags, COCO/custom object filters, CPU forcing, and JSON summaries.

## Operating reminders

- ImageAI 3.x expects PyTorch `.pt` or `.pth` weights. TensorFlow-era `.h5` weights are intentionally rejected.
- `output_type="file"` returns detections and writes an annotated image only when `output_image_path` is supplied. `output_type="array"` returns a rendered OpenCV/Numpy image array plus detections.
- Extraction with file output writes a sibling extraction directory based on the output image basename plus `-extracted`; pre-existing directories cause failure.
- Detection dictionaries contain `name`, `percentage_probability`, and `box_points` with `[x1, y1, x2, y2]` integer coordinates.
- For COCO filters, call `detector.CustomObjects(...)` with labels from the loaded class list and spaces converted to underscores, for example `traffic_light=True` or `cell_phone=True`.
- Current source uses `detectObjectsFromImage(custom_objects=...)`; older examples may mention `detectCustomObjectsFromImage`, but that method is not part of the verified current still-image API.
