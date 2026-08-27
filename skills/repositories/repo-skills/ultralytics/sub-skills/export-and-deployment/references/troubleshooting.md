# Export Troubleshooting

## CLI Argument Shape Problems

Symptoms:

- The command prints the Ultralytics syntax help.
- Arguments are ignored or interpreted as positional text.
- User writes `--format onnx`, `format onnx`, or mixed argparse-style flags.

Fix:

- Use `yolo TASK MODE arg=value` syntax, for example `yolo export model=yolo26n.pt format=onnx imgsz=640`.
- Do not use argparse-style `--format`; all configuration overrides are `key=value`.
- `TASK` is optional for export/benchmark when the model path implies the task, but valid tasks are `classify`, `detect`, `obb`, `pose`, `segment`, and `semantic`.

## Unsupported Export Argument

Symptoms:

- Error such as `argument 'dynamic' is not supported for format='pb'`.
- Export starts after adding a key that works for another backend but not this one.

Fix:

- Check the format matrix in `api-reference.md`.
- Remove unsupported keys instead of trying to force them through config.
- Common mismatch examples: `dynamic=True` on TFLite, `keras=True` outside SavedModel, `nms=True` on classification or semantic models, and `optimize=True` outside supported mobile/CPU routes.

## Optional Dependency Failures

Symptoms:

- Import errors for `onnx`, `onnxruntime`, `openvino`, `coremltools`, `tensorflow`, `onnx2tf`, `tensorrt`, `MNN`, `ncnn`, or vendor SDK packages.
- Resolver conflicts involving TensorFlow, protobuf, NumPy, setuptools, or Torch.

Fix:

- For ONNX/OpenVINO, start with `pip install "ultralytics[export-base]"`.
- For TFLite/SavedModel/TF.js/Edge TPU, use `ultralytics[export-tensorflow]` in a fresh environment when possible.
- For CoreML, use `ultralytics[export-coreml]` on supported non-Windows platforms.
- Avoid `ultralytics[export]` when the user only needs ONNX; the broad extra includes TensorFlow and CoreML stacks that can create unrelated conflicts.
- Specialized vendor formats may require isolated Python/Torch versions; do not repair them by blindly upgrading every package.

## TensorRT On CPU-Only Environment

Symptoms:

- User requests `format=engine device=cpu`.
- Export says TensorRT requires GPU or auto-assigns `device=0` and then CUDA/TensorRT fails.
- Inference says engine execution is not supported on CPU.

Fix:

- Explain that TensorRT is NVIDIA GPU/DLA-oriented and not a CPU deployment format.
- If the target is CPU, route to `format=onnx` or `format=openvino` depending on hardware.
- If the target is NVIDIA GPU, check CUDA driver/runtime, TensorRT install, visible GPU, and matching deployment hardware before export.
- For Jetson DLA, use `device=dla:0` or `device=dla:1` only on a supported stack; TensorRT 11 does not support DLA.

## INT8 Calibration Issues

Symptoms:

- Export warns that `data` is missing and uses a default dataset.
- Accuracy drops after INT8 export.
- TensorRT calibration cache is stale or tied to old data/batch settings.

Fix:

- Pass `data=<dataset.yaml>` from the deployment domain; route dataset creation/repair to `data-and-configuration`.
- Use a representative validation set and an appropriate `fraction` rather than the smallest demo dataset for production.
- For TensorRT INT8, calibrate on the same target GPU class whenever possible.
- Remove stale calibration cache files if data distribution, batch size, or target device changes significantly.

## Bad Data Or Config Paths

Symptoms:

- INT8 export fails while loading calibration data.
- Benchmark or validation after export cannot find images, labels, or dataset YAML.

Fix:

- Confirm the YAML path is reachable from the current process and contains valid task-specific dataset fields.
- Use built-in `coco8.yaml` only for smoke tests, not production calibration claims.
- Route deeper dataset YAML repair to `data-and-configuration`.

## Backend And Platform Constraints

- **OpenVINO:** Intel GPU/NPU inference requires supported hardware and drivers. If `device=intel:gpu` or `device=intel:npu` is not detected, fix OpenVINO device setup rather than changing the exported model.
- **CoreML:** export is unsupported on Windows and aarch64 Linux; Ultralytics CoreML predict/val runs on macOS only. macOS Python 3.13 can conflict with OpenVINO/CoreML OpenMP behavior in shared benchmark processes.
- **TFLite/TensorFlow:** TensorFlow exports can fail from Python/protobuf/NumPy/setuptools conflicts. Use a fresh environment and the target-specific extra.
- **Edge TPU:** requires non-aarch64 Linux and the Edge TPU compiler, and forces batch 1.
- **Paddle/MNN:** protobuf conflicts can appear in shared processes after TensorFlow imports; isolate the export if needed.
- **RKNN/QNN/vendor NPU:** require target architecture names and vendor packages; many tests verify artifact creation but skip real on-device inference.

## Download, Network, And Side Effects

- Official model names such as `yolo26n.pt` may trigger weight downloads if not cached.
- Export writes model artifacts next to the source weights or current working directory.
- Benchmark mode may export multiple formats and validate on data, which can be slow and disk-heavy.
- Triton examples can pull large containers and start services.
- Ask before running commands that download weights, pull containers, benchmark all formats, or write large export artifacts.

## When To Re-route

- The user needs a dataset YAML, class names, calibration splits, or path fixes: `data-and-configuration`.
- The user needs training, fine-tuning, validation of PyTorch weights, or metric interpretation before export: `training-and-validation`.
- The user needs result object parsing, postprocessing, custom output tensor decoding, or media inference loops: `inference-and-results`.
- The user is choosing between YOLO, RT-DETR, SAM, YOLOWorld, task suffixes, or model sizes: `model-families-and-tasks`.
