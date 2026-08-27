---
name: deployment-and-inference
description: "Export trained anomalib models and run runtime inference with
  Engine.predict, export helpers, TorchInferencer, and OpenVINOInferencer."
metadata:
  disco-role: operating
license: Apache 2.0
disable-model-invocation: true
---

# Deployment and Inference

Use this skill when a trained anomalib model must be turned into a runtime artifact or run at inference time. It covers the path from checkpoint or trained model to export, runtime loading, and prediction.

## What this skill covers

- `Engine.predict(...)` for dataset, datamodule, `data_path`, or explicit dataloaders.
- `Engine.export(...)` and the underlying `ExportMixin` helpers.
- `TorchInferencer` for trusted Torch checkpoints.
- `OpenVINOInferencer` for OpenVINO IR or ONNX artifacts.
- Export and runtime troubleshooting for optional dependencies and trust gates.

## What this skill excludes

- Training loop internals, fit/test/validate logic, and callback design.
- Benchmark or pipeline orchestration.
- Studio application files and UI implementation details.

## Quick chooser

| Need | Use | Notes |
| --- | --- | --- |
| Predict from a trained model inside Lightning | `Engine.predict(...)` | Best default when you already have an `AnomalibModule`. |
| Export to Torch / ONNX / OpenVINO | `Engine.export(...)` or `ExportMixin` | `INT8_PTQ` and `INT8_ACQ` need a datamodule. |
| Load a trusted Torch checkpoint directly | `TorchInferencer` | Legacy, pickle-based, and gated by `TRUST_REMOTE_CODE`. |
| Load an OpenVINO or ONNX deployment artifact | `OpenVINOInferencer` | Default device is `AUTO`; `config` is optional. |

## Primary workflow

1. Start from a trained `AnomalibModule` or a trusted exported checkpoint.
2. Decide whether you need:
   - Lightning-managed prediction (`Engine.predict`)
   - an export artifact (`Engine.export` / `ExportMixin`)
   - direct runtime inference (`TorchInferencer` or `OpenVINOInferencer`)
3. Pick the export format:
   - `torch` for a pickled model object
   - `onnx` for interchange or downstream conversion
   - `openvino` for optimized deployment
4. For ONNX dynamo export, `onnxscript` must be installed. For OpenVINO INT8 export, `nncf` must be installed.
5. For OpenVINO quantization:
   - use `FP16` or `INT8` when you do not have a datamodule
   - use `INT8_PTQ` or `INT8_ACQ` only with a datamodule
   - use `INT8_ACQ` with a metric when you need custom quality control
6. Treat Torch checkpoints as trusted code only. If the source is not trusted, do not bypass the gate; prefer ONNX or OpenVINO instead.
7. Use the bundled scripts for tiny deterministic smoke runs.

## Bundled references

- [Deployment guide](references/deployment-and-inference.md)
- [API reference](references/api-reference.md)
- [Troubleshooting](references/troubleshooting.md)

## Bundled scripts

- `scripts/basic-inference-api.py` — minimal Python `Engine.predict` example.
- `scripts/basic-openvino-inference.py` — minimal OpenVINO API recipe.
- `scripts/lightning-inference.py` — CLI-style `Engine.predict` helper.
- `scripts/openvino-inference.py` — OpenVINO image inference helper.
- `scripts/torch-inference.py` — legacy Torch inference helper with trust warning.

## Notes for future agents

- Prefer `Engine.predict` over `TorchInferencer` for new work.
- `TorchInferencer` loads pickled checkpoints and requires `TRUST_REMOTE_CODE=1`.
- `OpenVINOInferencer` accepts `.xml`, `.bin`, or `.onnx` paths and may create `openvino_cache/` in the current working directory.
- The repo's `basic_torch_inference.py` example is only a header stub in this checkout; do not depend on it.
- `tools/inference/gradio_inference.py` is reference-only because it launches a server and depends on optional UI packages.

## Minimal success checks

- Exported Torch artifact ends in `weights/torch/model.pt`.
- Exported ONNX artifact ends in `weights/onnx/model.onnx`.
- Exported OpenVINO artifact ends in `weights/openvino/model.xml` with a sibling `.bin`.
- `Engine.predict` can be driven by `dataset`, `datamodule`, or `data_path`.
- OpenVINO INT8 export is rejected until a datamodule is provided.
- Torch checkpoint loading is rejected until the trust gate is explicitly opened for a trusted file.
