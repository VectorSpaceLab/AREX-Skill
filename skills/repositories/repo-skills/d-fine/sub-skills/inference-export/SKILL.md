---
name: inference-export
description: "Run D-FINE inference, export, deployment, benchmark,
  visualization, and EMA checkpoint workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# D-FINE Inference and Export Router

Use this sub-skill when the user needs D-FINE deployment or inference commands, backend prerequisites, generated result filenames, benchmark commands, or EMA-only checkpoint extraction.

## Route by task

- **PyTorch image/video inference**: collect a D-FINE config, checkpoint, input image/video, and device; then use [references/inference-and-export.md](references/inference-and-export.md) or `scripts/dfine_inference_command.py --backend torch`.
- **ONNX export or ONNX Runtime inference**: collect config, checkpoint, ONNX model path, input image/video, and optional check/simplify requirements; then use [references/inference-and-export.md](references/inference-and-export.md) and `scripts/dfine_export_command.py` or `scripts/dfine_inference_command.py --backend onnx`.
- **TensorRT engine build, inference, or latency**: collect ONNX model, engine output/input, CUDA device, image directory for latency, and TensorRT toolchain availability; then use [references/deployment-and-benchmarks.md](references/deployment-and-benchmarks.md), `scripts/dfine_export_command.py --build-trt`, `scripts/dfine_inference_command.py --backend trt`, or `scripts/dfine_benchmark_command.py --benchmark trt`.
- **OpenVINO inference**: collect an OpenVINO IR/XML model and image path; then use [references/inference-and-export.md](references/inference-and-export.md) or `scripts/dfine_inference_command.py --backend openvino`.
- **FLOPs/MACs/params or FiftyOne visualization**: use [references/deployment-and-benchmarks.md](references/deployment-and-benchmarks.md) and `scripts/dfine_benchmark_command.py --benchmark flops` for static model info.
- **EMA checkpoint extraction**: use `scripts/extract_ema_checkpoint.py` when a checkpoint has `ema.module` and the user needs a `{model: ...}` checkpoint for simpler loading/export.

## Required inputs to ask for

- Config file for config-bound workflows, for example a COCO, Objects365, CrowdHuman, or custom D-FINE YAML.
- Checkpoint for PyTorch inference, ONNX export, FiftyOne, or EMA extraction.
- ONNX model for ONNX Runtime inference or TensorRT engine creation.
- TensorRT engine for TensorRT inference/latency; OpenVINO IR/XML model for OpenVINO inference.
- Image/video path for visualization inference; image directory for TensorRT latency benchmark.
- Device string where the native script accepts one, such as `cpu`, `cuda:0`, or TensorRT CUDA device.
- Expected output filename: PyTorch uses `torch_results.jpg` or `torch_results.mp4`; ONNX Runtime uses `onnx_result.jpg` or `onnx_result.mp4`; TensorRT uses `trt_result.jpg` or `trt_result.mp4`; OpenVINO writes `openvino_result.jpg`.

## Boundaries

- This sub-skill covers inference, export, deployment conversion, benchmark commands, optional backend prerequisites, output files, and deployment-oriented checkpoint conversion.
- Route training, resume, tuning, evaluation, checkpoint creation, and long experiment launch decisions to the training/evaluation sub-skill.
- Route dataset layout and data config editing to the data/config sub-skill.
- Route architecture internals to the architecture/API sub-skill, except for deploy-mode facts needed for export and inference.

## Failure handling

Start with [references/troubleshooting.md](references/troubleshooting.md) for missing checkpoint keys, `HGNetv2.pretrained`, ONNX opset/check/simplify, TensorRT/trtexec, OpenVINO IR/device, preprocessing, shifted boxes, and output filename mismatches.
