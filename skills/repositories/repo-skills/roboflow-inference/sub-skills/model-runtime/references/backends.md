# Backends and installation

This reference maps the runtime backend values to their installation extras and the situations where each backend is the right first choice.

## Backend values

| BackendType value | Typical use | Notes |
| --- | --- | --- |
| `trt` | NVIDIA GPU production | Fastest when the TensorRT engine matches the runtime environment. |
| `onnx` | CPU, cross-platform, Roboflow-exported models | Needs ONNX Runtime and compatible execution providers. |
| `torch` | Development, CPU, flexible model support | Good default when you want the widest debug surface. |
| `hugging-face` | Vision-language and transformer-style models | Included in the base install; availability still depends on the model. |
| `torch-script` | TorchScript-exported packages | Used by some exported families, especially YOLO variants. |
| `ultralytics` | Ultralytics-backed packages | Only when the model registry exposes it. |
| `custom` | Provider-defined or local custom packages | Usually paired with a custom code package. |

## Current ranking stance

When packages are otherwise comparable, the current code path ranks them in this order:

`trt` > `onnx` > `torch` > `hugging-face` > `torch-script` > `ultralytics` > `custom`

That ranking only happens after the package has already passed model-implementation, trust, batch-size, quantization, runtime, and feature filters.

## Installation extras

### Torch extras

- `torch-cpu`
- `torch-cu118`
- `torch-cu124`
- `torch-cu126`
- `torch-cu128`
- `torch-cu130`
- `torch-jp6-cu126`

### ONNX extras

- `onnx-cpu`
- `onnx-cu118`
- `onnx-cu12`
- `onnx-jp6-cu126`

### TensorRT

- `trt10`

## Installation patterns

### Base install

```bash
pip install inference-models
```

Use this when you want the default CPU Torch + transformer stack and plan to let `AutoModel` negotiate the package automatically.

### CPU-only

```bash
pip install "inference-models[onnx-cpu]"
```

Use this when you want a simple CPU install and you know the model family has ONNX packages.

### NVIDIA GPU

```bash
pip install --index-url https://download.pytorch.org/whl/cu128 torch torchvision
pip install "tensorrt==10.12.0.36"
pip install "inference-models[torch-cu128,onnx-cu12,trt10]"
```

This is the broadest modern GPU setup for CUDA 12.x environments.

### Jetson

```bash
pip install --index-url https://pypi.jetson-ai-lab.io/jp6/cu126/+simple torch torchvision onnxruntime-gpu
pip install "inference-models[torch-jp6-cu126,onnx-jp6-cu126]"
```

Do not add `trt10` on Jetson; use the TensorRT stack shipped with JetPack.

## Practical backend choice

### Choose `trt` when

- you are on NVIDIA GPU hardware
- the model family exposes a TensorRT package
- runtime and engine versions match
- you want production latency and throughput

### Choose `onnx` when

- you need cross-platform compatibility
- the model family is Roboflow-exported or ONNX-native
- you want a stable CPU path on machines without TensorRT

### Choose `torch` when

- you are debugging model behavior
- you need the broadest developer ergonomics
- you are on CPU and the model family provides a Torch package

### Choose `hugging-face` when

- the catalog page shows a Hugging Face package
- the model is transformer-like or vision-language oriented
- you want the packaged transformer stack rather than a lower-level export

## What to check before forcing a backend

1. Run `AutoModel.describe_compute_environment()`.
2. Run `AutoModel.describe_model(model_id)`.
3. If needed, run `AutoModel.describe_model_package(model_id, package_id)`.
4. Match the backend to the catalog entry instead of forcing a backend that the model does not publish.
5. If the package is ONNX, make sure `ONNXRUNTIME_EXECUTION_PROVIDERS` or `onnx_execution_providers` is valid.

## PyPI caveat

When installing from PyPI, backend-specific wheels sometimes need explicit package indexes.
The `inference-models` extras express the dependency intent, but the exact wheel location for `torch`, `onnxruntime`, and `tensorrt` still depends on your platform.

If you are unsure, install the backend wheel first, then install `inference-models` with the matching extra.

## Model-family heuristic

- RF-DETR and many YOLO variants usually offer `onnx`, `trt`, or `torch-script` packages.
- SAM / SAM2 / depth / OCR / vision-language families often lean on `torch` or `hugging-face` packages.
- Roboflow-exported models frequently require `onnx`.
- Always confirm with the model catalog before making assumptions.
