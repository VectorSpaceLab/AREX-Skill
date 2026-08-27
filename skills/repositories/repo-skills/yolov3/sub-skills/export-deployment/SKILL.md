---
name: export-deployment
description: "Export YOLOv3 weights and choose deployment formats across
  TorchScript, ONNX, OpenVINO, TensorRT, CoreML, and Paddle."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Export and Deployment Sub-skill

Read this for `export.py`, deployment formats, `DetectMultiBackend` suffixes, backend-specific dependencies, ONNX/OpenVINO/TensorRT/CoreML/Paddle choices, and export troubleshooting.

## Use

- Read `references/export-formats.md` for supported format matrix and backend constraints.
- Use `scripts/yolov3_export_format_matrix.py` to print or validate format names without exporting weights.
- Read `references/troubleshooting.md` for optional dependency, CPU/GPU, and unsupported TensorFlow export issues.

## Important facts

- Public export command pattern: `python export.py --weights yolov3-tiny.pt --img 64 --include torchscript`.
- CPU-friendly export formats include TorchScript, ONNX, OpenVINO, CoreML, and Paddle when dependencies exist.
- TensorRT `.engine` export is CUDA/GPU-only.
- TensorFlow rows are retained in `export_formats()` for suffix detection, but TensorFlow export is not implemented by this repo.
