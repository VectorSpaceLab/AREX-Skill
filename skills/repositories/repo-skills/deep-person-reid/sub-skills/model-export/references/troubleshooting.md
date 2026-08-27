# Troubleshooting

## Quick recovery table

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No core model key found` or `model-name is required` | The checkpoint filename does not contain a safe architecture token | Pass `--model-name` explicitly. Do not rely on the source `get_model_name()` helper for generic checkpoint names. |
| `Unsupported include value` | A value outside `onnx`, `openvino`, or `tflite` was passed | Re-run with one of the supported include tokens only. |
| `ModuleNotFoundError: onnx` | ONNX export was requested but the package is absent | Install the ONNX extra, or limit the run to `--dry-run` until the dependency is available. |
| `ModuleNotFoundError: openvino...` | OpenVINO conversion was requested without OpenVINO tooling | Export ONNX first, then install `openvino-dev` or the equivalent Model Optimizer package. |
| `ModuleNotFoundError: openvino2tensorflow` or TensorFlow import failure | The TFLite chain was requested without its converter/runtime packages | Install `openvino2tensorflow`, `tensorflow`, and the related TensorFlow extras before retrying. |
| Checkpoint load fails or loads zero matched layers | Wrong checkpoint, wrong architecture, or corrupted file | Verify the file path, confirm the model family, and make sure the checkpoint really belongs to that model key. |
| `--half-precision` plus CPU or `--dynamic` looks wrong | Half precision is not trustworthy for the CPU-safe ONNX path | Keep ONNX in float32; reserve FP16 for the optional OpenVINO stage when the converter supports it. |
| Dynamic axes do not survive downstream conversion | The converter stage flattened or constrained the ONNX shape | Treat dynamic batch support as an ONNX-stage feature and verify downstream converter behavior separately. |
| OpenVINO fails when ONNX was skipped | The converter expects ONNX as its input | Re-run with ONNX in the chain; OpenVINO is not a direct raw-checkpoint exporter here. |
| TFLite fails when OpenVINO was skipped | The TFLite chain expects the OpenVINO artifact first | Export ONNX, then OpenVINO, then the TFLite-style outputs. |
| The run claims success but no artifact was produced | The export was not actually executed, or the environment lacked an optional dependency | Record the run as unverified until the file or directory really exists in the working tree. |

## Source-script quirks to remember

- The source `tools/export.py` reuses detection-style messages, so its failure text is not always Torchreid-specific.
- The source `get_model_name()` only recognizes a small subset of model names and can miss valid Torchreid checkpoints.
- The source script imports pandas for its format table; the bundled helper should not do that on the help path.
- `--include` order should be normalized by the helper so users can request `openvino` or `tflite` without manually adding the upstream steps.

## Safe response pattern

1. Keep the ONNX stage as the first real export step.
2. Refuse to guess the model family when the filename is ambiguous.
3. Stop with a precise optional-dependency error instead of trying to run a missing backend.
4. Avoid claiming success until the file system confirms the output artifact exists.
