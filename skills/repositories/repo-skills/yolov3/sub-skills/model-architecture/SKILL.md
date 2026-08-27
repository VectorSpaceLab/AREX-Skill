---
name: model-architecture
description: "Inspect and modify YOLOv3 model YAMLs, anchors, Detect heads,
  parse_model behavior, strides, and tensor shapes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Model Architecture Sub-skill

Read this for `models/yolo.py`, `models/common.py`, model YAMLs, anchors, class counts, `Detect`, `Model`, `DetectionModel`, `parse_model`, stride/grid behavior, and output-shape debugging.

## Use

- Read `references/architecture.md` for YAML structure, supported model files, and parser/head behavior.
- Use `scripts/yolov3_model_yaml_probe.py` to instantiate a YAML and report prediction shapes on a zero tensor.
- Read `references/troubleshooting.md` for class/anchor/channel mismatch issues.

## Important facts

- Built-in detection YAMLs are `models/yolov3.yaml`, `models/yolov3-spp.yaml`, and `models/yolov3-tiny.yaml`.
- This repo does not contain segmentation, classification, pose, or newer YOLO task heads.
- Default Detect output has `no = nc + 5`; for COCO, `85` channels per anchor prediction.
- At `64x64`, default YOLOv3-tiny produces `(1, 60, 85)` predictions.
