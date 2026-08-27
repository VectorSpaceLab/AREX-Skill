---
name: deployment-and-export
description: "Exports PaddleDetection models and plans Paddle Inference,
  Python/C++, Serving, Lite, ONNX, FastDeploy, TensorRT, and benchmark
  deployment workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Deployment and Export

Use this route to export a trained model, inspect exported artifacts, run Paddle Inference deployment, prepare Serving/Lite/ONNX/FastDeploy paths, or plan TensorRT/benchmark checks.

## Workflow

1. Start from a validated training config and weights file/URL. Confirm the model family supports the target backend.
2. Build an export command with [`scripts/build_export_deploy_command.py`](scripts/build_export_deploy_command.py). Export should produce `infer_cfg.yml`, `model.pdmodel`, `model.pdiparams`, and `model.pdiparams.info` in the model directory.
3. Inspect the exported directory with [`scripts/inspect_inference_model.py`](scripts/inspect_inference_model.py) before deploying.
4. For Python Paddle Inference, choose `--device=CPU/GPU/XPU`, `--run_mode=paddle/trt_fp32/trt_fp16/trt_int8`, input source, threshold, batch size, MKLDNN or TensorRT options.
5. For Serving, Lite, ONNX, FastDeploy, C++, or vendor backends, read the corresponding reference and verify the external runtime before running conversion/build commands.
6. Use [`scripts/convert_infer_cfg_to_json.py`](scripts/convert_infer_cfg_to_json.py) for the small Paddle Lite config conversion helper.

## References

- [`references/export-and-conversion.md`](references/export-and-conversion.md): export flags, ONNX conversion, benchmark, and quantization notes.
- [`references/python-inference.md`](references/python-inference.md): `deploy/python` runtime inputs and options.
- [`references/serving-and-edge.md`](references/serving-and-edge.md): Serving, Lite, C++, FastDeploy, and vendor backend boundaries.
- [`references/troubleshooting.md`](references/troubleshooting.md): exported artifact, runtime, and backend failures.
