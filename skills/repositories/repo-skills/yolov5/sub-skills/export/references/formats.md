# Export Formats

## Shared export entrypoint

`export.py` is the shared export surface for YOLOv5 checkpoints. The inspected parser includes options such as `--data`, `--weights`, `--imgsz`, `--batch-size`, `--device`, `--half`, `--inplace`, `--keras`, `--optimize`, `--int8`, `--per-tensor`, `--dynamic`, `--cache`, `--simplify`, `--mlmodel`, `--opset`, `--verbose`, `--workspace`, `--nms`, `--agnostic-nms`, `--topk-per-class`, `--topk-all`, `--iou-thres`, `--conf-thres`, and `--include`.

## Format overview

| Format | Typical flag | Key prerequisite | Notes |
| --- | --- | --- | --- |
| TorchScript | `torchscript` | PyTorch | Lightest native export path. |
| ONNX | `onnx` | `onnx` package | Common bridge to many runtimes. |
| OpenVINO | `openvino` | `openvino` plus ONNX | Converts from ONNX. |
| TensorRT | `engine` | CUDA-capable GPU + TensorRT | Runtime/version/GPU sensitive. |
| CoreML | `coreml` | `coremltools` | Best on macOS for validation. |
| SavedModel | `saved_model` | TensorFlow | Heavy and version-sensitive. |
| GraphDef | `pb` | TensorFlow | Legacy TensorFlow graph export. |
| TFLite | `tflite` | TensorFlow / TFLite tooling | Often follows TensorFlow export paths. |
| Edge TPU | `edgetpu` | Edge TPU tooling | Device/compiler dependent. |
| TF.js | `tfjs` | tensorflowjs and TensorFlow | Heavy dependency stack. |
| Paddle | `paddle` | PaddlePaddle packages | Optional and separate from PyTorch. |

## Default path behavior

The source shows `export.py` can export multiple formats from the same checkpoint and often requires a PyTorch source model plus an intermediate ONNX or TensorFlow artifact for some formats. File names are typically derived from the input checkpoint, such as `.onnx`, `.engine`, `.mlpackage`, or `_saved_model` suffixes.

## Format selection guidance

- Use TorchScript for the most direct PyTorch-adjacent deployment path.
- Use ONNX when you need broad interoperability or a gateway to OpenVINO/TensorRT-like runtimes.
- Use TensorRT only when the target deployment environment matches the engine build.
- Use CoreML for Apple deployment planning.
- Use TensorFlow/TFLite/TF.js only if the target runtime stack justifies the heavy dependency set.
- Use Paddle only when the downstream consumer specifically requires it.

## Validation strategy

1. Confirm the source checkpoint family matches the task.
2. Confirm the output directory and filenames.
3. Confirm the minimum prerequisite package set for the chosen format list.
4. Prefer a tiny image size and a non-destructive workspace when the task only needs a smoke check.
5. Use the benchmark sub-skill only when you want multi-format timing/comparison behavior.
