# Export API Reference

## CLI And Python Entry Points

- CLI: `yolo export model=<weights.pt> format=<target> arg=value` and `yolo benchmark model=<weights.pt> data=<dataset.yaml> imgsz=<square-size> format=<target>`.
- Python export: `YOLO("weights.pt").export(format="onnx", **kwargs)` returns the exported artifact path.
- Python benchmark: `from ultralytics.utils.benchmarks import benchmark`; call `benchmark(model="yolo26n.pt", data="coco8.yaml", imgsz=640, format="onnx")`.
- Exported models can usually be loaded back through `YOLO(exported_path)` for `predict` and `val`, subject to backend/platform constraints.

## Common Format Matrix

| Format | `format=` | Output | CPU | GPU | Dependency environment | Main arguments |
| --- | --- | --- | --- | --- | --- | --- |
| TorchScript | `torchscript` | `.torchscript` | yes | yes | base | `batch`, `optimize`, `half`, `nms`, `dynamic` |
| ONNX | `onnx` | `.onnx` or `_int8.onnx` | yes | yes | `export-base` | `batch`, `data`, `dynamic`, `half`, `int8`, `opset`, `simplify`, `nms`, `fraction` |
| OpenVINO | `openvino` | `_openvino_model/` | yes | no for export table | `export-base` | `batch`, `data`, `dynamic`, `half`, `int8`, `nms`, `fraction` |
| TensorRT | `engine` | `.engine` | no | yes | TensorRT/CUDA plus base export deps | `batch`, `data`, `dynamic`, `half`, `int8`, `simplify`, `nms`, `fraction`, `workspace`, `device` |
| CoreML | `coreml` | `.mlpackage` | yes | no for export table | `export-base`, `export-coreml` | `batch`, `dynamic`, `half`, `int8`, `nms` |
| TensorFlow SavedModel | `saved_model` | `_saved_model/` | yes | yes | `export-base`, `export-tensorflow` | `batch`, `data`, `fraction`, `int8`, `keras`, `nms` |
| TensorFlow GraphDef | `pb` | `.pb` | yes | yes | `export-base`, `export-tensorflow` | `batch` |
| TensorFlow Lite | `tflite` | `.tflite` | yes | no for export table | `export-base`, `export-tensorflow` | `batch`, `data`, `half`, `int8`, `nms`, `fraction` |
| Edge TPU | `edgetpu` | `_edgetpu.tflite` | yes | no | TensorFlow env plus Edge TPU compiler | `data`, `fraction`, `int8` |
| TensorFlow.js | `tfjs` | `_web_model/` | yes | no | `export-base`, `export-tensorflow` | `batch`, `data`, `fraction`, `half`, `int8`, `nms` |
| MNN | `mnn` | `.mnn` | yes | yes | `export-base` plus MNN packages | `batch`, `half`, `int8` |
| NCNN | `ncnn` | `_ncnn_model/` | yes | yes | `export-base` plus NCNN/PNNX | `batch`, `half` |
| IMX | `imx` | `_imx_model/` | yes | yes | isolated IMX env | `data`, `int8`, `fraction`, `nms` |
| RKNN | `rknn` | `_rknn_model/` | no | no | isolated RKNN env | `batch`, `name`, `half`, `int8`, `data`, `fraction` |
| ExecuTorch | `executorch` | `_executorch_model/` | yes | no | `export-base`, `export-executorch` | `batch` |
| Axelera AI | `axelera` | `_axelera_model/` | no | no | isolated Axelera env | `batch`, `int8`, `fraction`, `data` |
| DEEPX | `deepx` | `_deepx_model/` | no | no | isolated DEEPX env | `data`, `int8`, `optimize` |
| Qualcomm QNN | `qnn` | `_qnn.onnx` | no | no | base export deps plus QNN runtime availability | `batch`, `name`, `int8`, `fraction`, `data` |

## Optional Dependency Groups

Install the smallest extra that fits the target instead of defaulting to the broad `export` extra:

- `ultralytics[export-base]`: ONNX, ONNX Runtime, ONNX graph slimming, OpenVINO, and common export helpers. This is usually enough for ONNX/OpenVINO planning.
- `ultralytics[export-tensorflow]`: TensorFlow, TensorFlow.js, ONNX-to-TF helpers, LiteRT, and protobuf-sensitive packages for SavedModel, GraphDef, TFLite, Edge TPU, and TF.js.
- `ultralytics[export-coreml]`: CoreML conversion tooling and scikit-learn for CoreML quantization on supported non-Windows platforms.
- `ultralytics[export]`: broad convenience extra combining export-base, export-tensorflow, and export-coreml; useful for exploration, but heavier and more conflict-prone than a target-specific install.
- Specialized formats such as IMX, RKNN, Axelera, DeepX, MNN, NCNN, and ExecuTorch may need isolated Python/Torch/package combinations rather than the broad extra.

## Argument Compatibility Rules

- Do not pass arbitrary config keys to export: the exporter validates changed values for `half`, `int8`, `dynamic`, `keras`, `nms`, `batch`, `fraction`, and `data` against each format.
- `half=True` and `int8=True` are mutually exclusive; the exporter will force `half=False` when both are set.
- `int8=True` without `data` falls back to a task default calibration dataset; for production, pass a representative dataset YAML.
- `nms=True` is invalid for classification, forced off for semantic segmentation, and can be forced off for end-to-end models and RT-DETR-like heads.
- `dynamic=True` with `nms=True`, `format=engine`, or `format=coreml` should usually include `batch=<max-batch>` greater than 1.
- Benchmark mode requires square `imgsz`; use a single integer or square size.

## Backend Notes

- **ONNX:** works across CPU and GPU runtimes. INT8 ONNX uses calibration data and produces an `_int8.onnx` artifact.
- **OpenVINO:** export produces a directory with XML/BIN/mapping files. Run with `device=intel:cpu`, `device=intel:gpu`, or `device=intel:npu` when supported by installed drivers and hardware.
- **TensorRT:** `format=engine` requires NVIDIA GPU/CUDA/TensorRT. If `device` is omitted, the exporter assigns GPU device `0`. DLA uses `device=dla:0` or `device=dla:1` on supported Jetson/TensorRT combinations.
- **CoreML:** output is `.mlpackage`. Export is not supported on Windows; Ultralytics CoreML inference is macOS-only.
- **TFLite/TF:** TensorFlow exports are more prone to Python, protobuf, and platform conflicts; prefer an isolated environment if export-base and TensorFlow extras collide.
- **Triton:** export ONNX with `dynamic=True`, arrange a Triton model repository, and optionally enable TensorRT acceleration in `config.pbtxt` for NVIDIA GPU serving.
