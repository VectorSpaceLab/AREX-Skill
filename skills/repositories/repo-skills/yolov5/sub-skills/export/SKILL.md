---
name: export
description: "Use this YOLOv5 sub-skill for model export, deployment formats,
  backend prerequisites, benchmarks, TensorRT/ONNX/CoreML/TFLite/OpenVINO/Paddle
  issues, and export safety."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# YOLOv5 Export and Benchmarks

Use this route for `export.py`, `benchmarks.py`, deployment-format conversion, export prerequisite checks, TensorRT/ONNX/CoreML/OpenVINO/TensorFlow/TFLite/TF.js/Paddle/Edge TPU issues, or benchmark planning.

## Choose the workflow

- **Export a checkpoint**: read `references/formats.md` to choose `--include` formats, dependencies, device, image size, dynamic/NMS options, and validation strategy.
- **Check optional dependencies**: run `scripts/check_export_prereqs.py --formats onnx torchscript` or another format list before installing heavy packages or converting models.
- **Benchmark formats**: read `references/benchmarks.md` before running `benchmarks.py`; benchmark commands can export models, download weights/data, and run validation.
- **Backend errors**: read `references/troubleshooting.md` for TensorRT version mismatch, ONNX dependency, Edge TPU compiler, TensorFlow/Keras, CoreML, OpenVINO, and path-safety failures.

## Common decisions

- Export only after selecting a task-compatible checkpoint from detection, segmentation, or classification.
- ONNX is the smallest common non-PyTorch export dependency; TorchScript does not need ONNX.
- TensorRT engines should be built and validated on the target runtime stack.
- `--half` and `--device 0` imply CUDA-capable execution; do not force them on CPU.
- Keep output directories/files explicit and isolated.
- Do not run broad `--include` lists just to see what happens; install/check only selected formats.

## Handoffs

- Route model training/selection to `../detection/SKILL.md`, `../segmentation/SKILL.md`, or `../classification/SKILL.md` first.
- Route Flask HTTP serving to `../serving/SKILL.md` if the user wants the repository's Flask example instead of an exported artifact.
- Read root `references/environment.md` for optional dependency grouping and backend setup.
