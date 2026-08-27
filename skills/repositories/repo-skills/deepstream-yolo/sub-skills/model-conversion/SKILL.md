---
name: model-conversion
description: "Routes DeepStream-Yolo exporter selection, ONNX conversion, and
  labels generation for supported model families."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model conversion

Use this sub-skill when the task is about turning a checkpoint into a DeepStream-ready ONNX file, picking the right exporter script, or generating the matching `labels.txt`.

## Trigger phrases

- convert weights to ONNX
- export YOLOv8 / YOLO11 / YOLOv10 / YOLOv12 / YOLOv13 / YOLO26
- generate `labels.txt`
- which export script should I use
- dynamic batch ONNX export
- use the DeepStream-Yolo exporter helper
- upstream repo setup for export

## Include here

- Ultralytics-family exporters that were verified in the inspection environment.
- Export flags such as `--size`, `--dynamic`, `--batch`, `--simplify`, and `--opset`.
- Label generation from exporter metadata.
- Guidance for matching the generated ONNX file back to the DeepStream config template.
- Reference-only notes for the other supported model families and their upstream stacks.

## Exclude or route elsewhere

- Building or running `deepstream-app`: use `deployment`.
- Multiple detector layouts: use `multi-gie`.
- INT8 calibration and benchmark tuning: use `int8-benchmarking`.
- Import/export or refresh of the skill library itself.

## How to use this route

1. Read `references/workflows.md` for the export flow.
2. Read `references/model-family-matrix.md` to pick the exporter and understand which families are bundled vs reference-only.
3. Read `references/upstream-dependencies.md` when the user wants an external repo setup checklist.
4. Use the bundled exporter script from `scripts/` that matches the chosen Ultralytics family.
5. Read `references/troubleshooting.md` if the export fails or labels are missing.

## What a future agent should be able to do here

- Choose the correct exporter from a checkpoint name and model family.
- Explain the common exporter flags and how they affect the ONNX artifact.
- Distinguish bundled Ultralytics-family support from reference-only upstream stacks.
- Tell the user which file to copy into the DeepStream deployment folder after export.

## Common failure signals

- Missing `onnx`, `onnxslim`, or `onnxruntime`
- The model file path is wrong
- The exporter runs but does not create `labels.txt`
- A legacy upstream repo is not installed
- The family matrix says the exporter is reference-only in this skill

## Linked helpers

- `scripts/export_yoloV8.py` — verified Ultralytics exporter copy.
- `scripts/export_yolo11.py` — verified Ultralytics exporter copy.
- `scripts/export_yoloV10.py` — verified Ultralytics exporter copy.
- `scripts/export_yolov12.py` — verified Ultralytics exporter copy.
- `scripts/export_yoloV13.py` — verified Ultralytics exporter copy.
- `scripts/export_yolo26.py` — verified Ultralytics exporter copy.
- `scripts/export_yolomaster.py` — verified Ultralytics exporter copy.
- `scripts/export_yoloV5u.py` — verified Ultralytics exporter copy.
- `scripts/export_rtdetr_ultralytics.py` — verified Ultralytics exporter copy.
- `references/workflows.md` — end-to-end export steps.
- `references/model-family-matrix.md` — exporter mapping and bundled/reference-only split.
- `references/upstream-dependencies.md` — external stack requirements by family.
- `references/troubleshooting.md` — export and label failure modes.
