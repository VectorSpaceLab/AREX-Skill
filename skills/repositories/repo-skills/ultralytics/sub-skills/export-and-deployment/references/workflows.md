# Export And Deployment Workflows

## Choose A Deployment Format

1. Identify the deployment hardware and runtime first: CPU server, Intel accelerator, NVIDIA GPU, Apple app, mobile/embedded TensorFlow, Triton service, or vendor NPU.
2. Pick the smallest compatible format and dependency group. Start with ONNX/OpenVINO when the target is uncertain; move to TensorRT/CoreML/TFLite only when the target runtime requires it.
3. Decide precision: FP32 for compatibility, `half=True` for FP16-capable targets, or `int8=True data=<dataset.yaml>` for calibrated size/speed trade-offs.
4. Export with a small representative command first, then run `predict` and `val` on the exported artifact before shipping.
5. Use `benchmark` on the same hardware class that will serve inference; benchmark results do not transfer reliably across CPUs, GPUs, drivers, and accelerators.

Cross-links: if the user has not prepared `data=<dataset.yaml>` for INT8 calibration, route to `data-and-configuration`; if they ask whether `yolo26n`, `yolo26n-seg`, `rtdetr-l`, or another family fits the target, route to `model-families-and-tasks`; if they need postprocessing output structures after export, route to `inference-and-results`.

## ONNX Export For Portable Deployment

Use ONNX for a balanced first export: CPU servers, GPU runtimes, web/edge toolchains, OpenCV DNN, and Triton all accept ONNX workflows.

```bash
pip install "ultralytics[export-base]"
yolo export model=yolo26n.pt format=onnx imgsz=640 dynamic=True simplify=True
yolo predict model=yolo26n.onnx source=image.jpg
```

For calibrated INT8 ONNX:

```bash
yolo export model=best.pt format=onnx imgsz=640 int8=True data=my_dataset.yaml fraction=0.5
```

Notes:

- ONNX supports `batch`, `data`, `dynamic`, `half`, `int8`, `opset`, `simplify`, `nms`, and `fraction`.
- Use `opset=<n>` only when a downstream parser requires a specific opset.
- Use `nms=True` only when the deployment runtime should receive post-NMS detections and the model/task supports it.
- C++ and Rust ONNX Runtime examples exist in the source repo, but this generated skill should reference them conceptually rather than copying full projects.

## OpenVINO For Intel Hardware

```bash
pip install "ultralytics[export-base]"
yolo export model=yolo26n.pt format=openvino imgsz=640 half=True
yolo predict model=yolo26n_openvino_model source=image.jpg device=intel:cpu
```

For Intel GPU or NPU inference:

```bash
yolo predict model=yolo26n_openvino_model source=image.jpg device=intel:gpu
yolo predict model=yolo26n_openvino_model source=image.jpg device=intel:npu
```

Notes:

- OpenVINO supports `dynamic`, `half`, `int8`, `nms`, `batch`, `data`, and `fraction`.
- INT8 export needs calibration data; pass the target dataset YAML rather than relying on task defaults.
- If Intel GPU/NPU is not detected, check OpenVINO device support and driver installation before changing model code.

## TensorRT For NVIDIA GPU

```bash
yolo export model=yolo26n.pt format=engine device=0 imgsz=640 half=True workspace=4
yolo predict model=yolo26n.engine source=image.jpg device=0
```

For TensorRT INT8:

```bash
yolo export model=best.pt format=engine device=0 imgsz=640 int8=True data=my_dataset.yaml batch=8 workspace=4
```

Notes:

- TensorRT export/inference requires NVIDIA GPU support; a CPU-only request should be rejected or routed to ONNX/OpenVINO.
- TensorRT supports `batch`, `data`, `dynamic`, `half`, `int8`, `simplify`, `nms`, `fraction`, `workspace`, and `device`.
- Calibrate INT8 on the same target device class when possible; TensorRT calibration can be hardware-specific.
- `workspace=None` lets TensorRT auto-allocate. If export crashes or reports unsupported state from memory limits, reduce `workspace`, `batch`, or `imgsz`.
- DLA is selected with `device=dla:0` or `device=dla:1` on supported Jetson stacks; TensorRT 11 removed DLA support, so use TensorRT 10.x for DLA.

## CoreML For Apple Apps

```bash
yolo export model=yolo26n.pt format=coreml int8=True
yolo predict model=yolo26n.mlpackage source=image.jpg
```

Notes:

- CoreML export produces `.mlpackage` and is not supported on Windows.
- Ultralytics CoreML prediction and validation are macOS-only.
- For YOLO26 end-to-end detection, `nms=True` is usually unnecessary; older model families may use it to embed NMS.
- Use `half=True` for conservative FP16 weight quantization or `int8=True` for smaller app-distributed models, then validate on target hardware.

## TensorFlow Lite And Edge TensorFlow

```bash
pip install "ultralytics[export-tensorflow]"
yolo export model=yolo26n.pt format=tflite imgsz=640
yolo predict model=yolo26n_float32.tflite source=image.jpg
```

For INT8 edge deployment:

```bash
yolo export model=best.pt format=tflite int8=True data=my_dataset.yaml fraction=0.5
```

Notes:

- TensorFlow formats include `saved_model`, `pb`, `tflite`, `edgetpu`, and `tfjs`.
- TensorFlow export stacks are sensitive to Python, protobuf, TensorFlow, and platform combinations. Prefer isolated environments for production export.
- Edge TPU requires non-aarch64 Linux and the Edge TPU compiler; batch is forced to 1.

## Triton Serving Route

Use Triton for scalable inference when the user can run Docker/Podman and wants server-side deployment.

1. Export ONNX with dynamic shapes:

```bash
yolo export model=yolo26n.pt format=onnx dynamic=True
```

2. Create a Triton model repository with `model.onnx` under `models/<name>/1/` and a `config.pbtxt` containing model metadata.
3. Start Triton with the model repository mounted.
4. Load the server URL with Ultralytics:

```python
from ultralytics import YOLO
model = YOLO("http://127.0.0.1:8000/yolo", task="detect")
results = model("image.jpg")
```

Triton setup can pull large containers and requires runtime-specific GPU flags; treat it as an explicit deployment action, not a hidden side effect of answering an export question.

## Benchmark Mode

Use `benchmark` when comparing export choices on the same hardware:

```bash
yolo benchmark model=yolo26n.pt data=coco8.yaml imgsz=640 format=onnx device=cpu
yolo benchmark model=yolo26n.pt data=coco8.yaml imgsz=640 device=0
```

Python:

```python
from ultralytics.utils.benchmarks import benchmark
benchmark(model="yolo26n.pt", data="coco8.yaml", imgsz=640, format="onnx", device="cpu")
```

Notes:

- A blank `format` attempts multiple formats and can install/download/export more than the user expects.
- Benchmark mode validates format support against the current device and platform, then exports, loads, runs validation, and records speed/metric columns.
- Avoid all-format benchmarking in constrained CI, CPU-only notebooks, or user environments with strict package policies.
