---
name: deployment
description: "Export DAMO-YOLO models to ONNX or TensorRT, plan partial INT8
  quantization, and diagnose deployment backend dependencies."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# DAMO-YOLO deployment

Use this sub-skill when the task involves DAMO-YOLO ONNX export, TensorRT engine export or evaluation, partial INT8 quantization, OpenVINO/TensorRT benchmark preparation, or deployment dependency troubleshooting.

Route training, fine-tuning, and COCO dataset setup to the training sub-skill. Route image/video/camera inference with an already-created engine to the inference sub-skill.

## First actions

1. Identify the target artifact: raw ONNX, end-to-end ONNX with NMS, TensorRT FP32/FP16/INT8 engine, TensorRT evaluation, OpenVINO conversion, or partial quantization.
2. Read [Deployment workflows](references/workflows.md) for supported paths and when to stop at ONNX.
3. Read [Deployment CLI reference](references/cli-reference.md) for flag meanings and source-equivalent commands.
4. Run `scripts/check_deploy_env.py` before installing or debugging optional backends.
5. Use `scripts/export_onnx_safe.py` when you need a generated-skill-owned ONNX exporter that imports the installed `damo` package and does not call repo-local converter scripts.
6. If anything fails, use [Deployment troubleshooting](references/troubleshooting.md).

## Bundled helper scripts

- `scripts/check_deploy_env.py`: reports availability of `damo`, PyTorch/CUDA, ONNX, ONNX Runtime, ONNX simplifier, TensorRT, CUDA Python/PyCUDA, and `pytorch_quantization`.
- `scripts/export_onnx_safe.py`: self-contained ONNX export helper adapted from the source converter flow. It requires a config, checkpoint, and output path; it supports raw or end-to-end ONNX export but does not build `.trt` engines. The helper calls `torch.onnx.export(..., dynamo=False)` so it does not require `onnxscript` on PyTorch builds whose default exporter uses it.

## Operating rules

- Keep model config, checkpoint, image size, batch size, and class count aligned. Most deployment failures are shape or class-count mismatches.
- Use raw ONNX (`--benchmark` or no `--end2end`) when measuring backbone/neck/head latency without NMS.
- Use `--end2end --ort` for ONNX Runtime NMS export; use `--end2end` without `--ort` only when the downstream TensorRT parser/runtime supports the selected NMS plugin family.
- TensorRT engine build/eval requires a TensorRT runtime stack; the construction environment verified CUDA but did not install TensorRT, PyCUDA, or `pytorch_quantization`.
- Partial INT8 quantization is an advanced TensorRT workflow. It needs calibration images, `pytorch_quantization`, model-type-specific sensitivity lists (`tiny`, `small`, `medium`), and enough GPU memory.
