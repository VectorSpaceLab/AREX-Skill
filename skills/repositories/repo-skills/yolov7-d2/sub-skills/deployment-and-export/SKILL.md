---
name: deployment-and-export
description: "Export YOLOv7-d2 models to ONNX or TorchScript, inspect
  ONNXRuntime inputs, convert DETR checkpoints, and reason about TensorRT or
  quantization deployment."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# Deployment and Export

Use this sub-skill when the user asks about YOLOv7-d2 ONNX/TorchScript export, ONNXRuntime inference, model IO inspection, DETR/AnchorDETR/SMCA checkpoint conversion, TensorRT, or quantization.

## Start here

1. Confirm the user has a trained checkpoint, matching config, and sample input image before export. Read [references/export-onnx.md](references/export-onnx.md).
2. Build an export command with [scripts/build_export_command.py](scripts/build_export_command.py).
3. Inspect exported ONNX files with [scripts/inspect_onnx_model.py](scripts/inspect_onnx_model.py), then read [references/onnxruntime-inference.md](references/onnxruntime-inference.md).
4. For reference DETR checkpoints, use [scripts/convert_detr_checkpoint.py](scripts/convert_detr_checkpoint.py) and read [references/checkpoint-conversion.md](references/checkpoint-conversion.md).
5. For TensorRT or quantization, read [references/quantization-and-tensorrt.md](references/quantization-and-tensorrt.md) before installing toolchains.
6. Use [references/troubleshooting.md](references/troubleshooting.md) for export/import/operator/runtime errors.

## Important distinctions

- Export is a PyTorch/Detectron2 model operation that needs the original model code, config, weights, and sample input shape.
- ONNXRuntime inference needs a completed ONNX file and postprocessing assumptions matching the exported model family.
- TensorRT and quantization are optional hardware/toolchain workflows, not automatically verified by a successful ONNX export.

## Boundaries

- For training configs and checkpoints before export, read [../training-and-configuration/SKILL.md](../training-and-configuration/SKILL.md).
- For ordinary PyTorch checkpoint demo/evaluation, read [../inference-and-evaluation/SKILL.md](../inference-and-evaluation/SKILL.md).
