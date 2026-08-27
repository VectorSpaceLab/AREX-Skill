---
name: export
description: "Guides YOLOP ONNX export, ONNXRuntime inference validation,
  TensorRT .wts preparation, and TensorRT/ZED deployment constraints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# YOLOP Export and Deployment Preparation

Use this sub-skill when the task asks to export a YOLOP checkpoint to ONNX, run ONNXRuntime inference, inspect exported output names/shapes, produce TensorRT `.wts` weights, or understand the repo's C++ TensorRT/ZED deployment path.

Do not use this sub-skill for PyTorch demo inference (use `inference`), BDD100K data preparation (use `data-preparation`), or full training/evaluation (use `training`).

## Read first

- [references/workflows.md](references/workflows.md) covers ONNX export, ONNXRuntime inference, output naming, and bundled helper usage.
- [references/tensorrt-deployment.md](references/tensorrt-deployment.md) distills the TensorRT/ZED deployment path and explains why it is not a CPU/Python smoke.
- [references/troubleshooting.md](references/troubleshooting.md) covers export output mismatches, missing ONNX packages, checkpoint format issues, and TensorRT build blockers.
- [scripts/export_onnx_model.py](scripts/export_onnx_model.py) is the safe ONNX exporter with explicit output path.
- [scripts/run_onnx_inference.py](scripts/run_onnx_inference.py) runs ONNXRuntime inference with explicit image/model/output paths.
- [scripts/export_wts.py](scripts/export_wts.py) converts a PyTorch checkpoint to TensorRT `.wts` text format with explicit output or dry-run mode.

## Quick route

```bash
# Export to a controlled location, using the export-specific MCnet wrapper
python sub-skills/export/scripts/export_onnx_model.py \
  --repo-root /path/to/YOLOP \
  --checkpoint /path/to/YOLOP/weights/End-to-end.pth \
  --output /tmp/yolop-640-640.onnx \
  --height 640 --width 640 --simplify --check

# Validate an ONNX model on a single image with ONNXRuntime CPU
python sub-skills/export/scripts/run_onnx_inference.py \
  --repo-root /path/to/YOLOP \
  --onnx /tmp/yolop-640-640.onnx \
  --image /path/to/YOLOP/test.jpg \
  --output-dir /tmp/yolop-onnx-output

# Inspect or write TensorRT .wts weights
python sub-skills/export/scripts/export_wts.py \
  --repo-root /path/to/YOLOP \
  --checkpoint /path/to/YOLOP/weights/End-to-end.pth \
  --dry-run
```

## Key gotcha

Do not export `lib.models.get_net(cfg)` directly unless you inspect the resulting ONNX outputs. The active source model's eval detection head returns a nested tuple, and some PyTorch exporters flatten it into extra outputs. The source `export_onnx.py` defines an export-specific `MCnet` wrapper that returns exactly `det_out`, `drive_area_seg`, and `lane_line_seg`; the bundled exporter uses that wrapper.

## Backend boundary

ONNX export and ONNXRuntime CPU inference can be validated in a CPU Python environment. TensorRT engine build and ZED-camera deployment require CUDA/TensorRT/ZED/OpenCV C++ prerequisites and are reference-only unless the user provides that environment.
