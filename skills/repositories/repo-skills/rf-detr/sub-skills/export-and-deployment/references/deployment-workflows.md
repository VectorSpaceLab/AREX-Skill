# RF-DETR deployment workflows

Use this reference to choose an export/deployment route. The examples are intentionally concise and avoid heavy notebook flows. Substitute the model class and checkpoint path for the actual detection, segmentation, or keypoint task.

## Choose the artifact

| Target consumer | Recommended path | Avoid |
| --- | --- | --- |
| General external inference runtime, ONNX Runtime, OpenVINO, inference-models handoff | `format="onnx"` | Starting with TensorRT unless the consumer specifically loads raw `.trt` |
| Raw TensorRT service you control on NVIDIA GPU | `format="tensorrt"` on the deployment GPU family | Building on a different GPU/TensorRT version and copying the engine blindly |
| Roboflow inference-models with automatic backend selection | Give inference-models a model id, checkpoint, or ONNX-compatible source; let it manage TRT | Exporting `format="tensorrt"` and expecting inference-models to consume that `.trt` |
| TensorFlow Lite mobile/edge | `format="tflite"` in a backend-isolated Python 3.12 environment | Static/full-integer INT8; unpinned TensorFlow/onnx2tf upgrades without validation |
| Portable PyTorch on-device CPU runtime | `format="executorch", backend="xnnpack"` | `dynamic_batch=True` |
| Apple on-device ExecuTorch delegate | `format="executorch", backend="coreml"` | Confusing it with native `format="coreml"` |
| Qualcomm Snapdragon HTP/NPU | `format="executorch", backend="qnn", soc="SM8650"` or the actual target SoC | Assuming the pip `executorch` wheel contains QNN |
| Native Xcode/Core ML bundle | `format="coreml"` | Passing `backend="coreml"` and expecting ExecuTorch output |
| Roboflow hosted/edge deployment | `deploy_to_roboflow(...)` or network-free `export_for_roboflow(...)` | Deploying after `inference(inplace=True)` |

## Preflight every export

1. Pick model family: detection (`RFDETRSmall`), segmentation (`RFDETRSegSmall`), or keypoint preview (`RFDETRKeypointPreview`).
2. Confirm checkpoint compatibility and trust boundary. For untrusted checkpoints, prefer safe loading paths such as `RFDETR.from_checkpoint(path, trust_checkpoint=False, **kwargs)`.
3. Choose `shape` divisible by `patch_size * num_windows`; start from the model's default resolution unless the deployment runtime requires a different size.
4. Run the bundled read-only preflight:

```bash
python scripts/inspect_export_options.py --variant rfdetr-small --format onnx --shape 512 512
```

5. Install only the target extra, ideally in a fresh environment for TFLite/CoreML/ExecuTorch.
6. Export with `verbose=True` for first attempts, then validate the artifact on representative images before production use.

## ONNX baseline workflow

Install and export:

```bash
pip install "rfdetr[onnx]"
```

```python
from rfdetr import RFDETRSmall

model = RFDETRSmall(pretrain_weights="checkpoint.pth")
path = model.export(
    output_dir="exports/onnx",
    format="onnx",
    shape=(512, 512),
    dynamic_batch=False,
    notes={"dataset": "my-dataset", "classes": ["part", "defect"]},
)
print(path)
```

Deployment notes:

- Decode raw `dets` and `labels` outside the graph. Apply sigmoid to logits after dropping the no-object column; convert normalized `cxcywh` boxes to pixel `xyxy` for your image size.
- For segmentation, also consume `masks`; for keypoints, consume `keypoints`.
- Match outputs by name, not shape.
- Use ONNX as the handoff format when another deployment system, including inference-models, handles acceleration.

## TensorRT workflow

Install and export on the build/deploy GPU family:

```bash
pip install "rfdetr[tensorrt]"
```

```python
from rfdetr import RFDETRSmall

model = RFDETRSmall(pretrain_weights="checkpoint.pth")
engine = model.export(
    output_dir="exports/trt",
    format="tensorrt",
    shape=(512, 512),
    fp16=True,
)
print(engine)
```

Rules:

- Build the engine on the same GPU architecture and TensorRT runtime family that will run it.
- Treat the `.trt` file as a compiled binary, not as a portable model interchange file.
- Set `fp16=False` when the TensorRT build cannot expose FP16 builder support or when you need FP32 parity testing.
- The in-process builder uses Polygraphy/TensorRT Python APIs; no `trtexec` binary is needed.

When using inference-models:

```bash
pip install inference-models
pip install "inference-models[trt10]"  # only when NVIDIA TensorRT support is needed
```

```python
from inference_models import AutoModel, BackendType

model = AutoModel.from_pretrained("rfdetr-small", backend=BackendType.TRT)
```

Do not pass the RF-DETR-exported `.trt` file to inference-models. Use ONNX/checkpoint/model id style inputs and let inference-models build/cache the engine it needs.

## TFLite workflow

Install in a Python 3.12 environment because the RF-DETR TFLite extra is version-marker gated:

```bash
pip install "rfdetr[tflite]"
```

FP32/FP16 export:

```python
from rfdetr import RFDETRSmall

model = RFDETRSmall(pretrain_weights="checkpoint.pth")
path = model.export(
    output_dir="exports/tflite",
    format="tflite",
    shape=(512, 512),
)
print(path)  # primary FP32 path; FP16 is also written
```

Dynamic-range INT8 export:

```python
from rfdetr import RFDETRSmall

model = RFDETRSmall(pretrain_weights="checkpoint.pth")
path = model.export(
    output_dir="exports/tflite-int8",
    format="tflite",
    quantization="int8",
    calibration_data="calibration_images",
    max_images=100,
)
print(path)
```

Calibration/validation data:

- Directory input: JPEG, PNG, BMP, and WebP images are loaded, resized, and converted automatically.
- `.npy`/array input: shape `(N, H, W, 3)`, dtype `float32`, values in `[0, 1]`, NHWC, no ImageNet normalization.
- Use 20-100 representative images from the train/validation domain for meaningful validation. Random data is acceptable only for a mechanical smoke.

Runtime preprocessing:

- TFLite models expect NHWC float32 input after ImageNet mean/std normalization unless you implement runtime-specific quantized input handling.
- For segmentation, expect an additional masks output.

Isolation guidance:

- Run TFLite conversion in a fresh process if your application imports ONNX. TensorFlow should load before ONNX to avoid a known Abseil symbol/load-order hang.
- Pin TensorFlow/onnx2tf/ai_edge_litert versions for production and rerun parity checks after upgrades.

## ExecuTorch workflows

Install:

```bash
pip install "rfdetr[executorch]"
```

Portable XNNPACK CPU:

```python
from rfdetr import RFDETRSmall

model = RFDETRSmall(pretrain_weights="checkpoint.pth")
pte = model.export(
    output_dir="exports/executorch-xnnpack",
    format="executorch",
    backend="xnnpack",
    shape=(512, 512),
    batch_size=1,
)
print(pte)
```

Apple ExecuTorch CoreML delegate:

```bash
pip install coremltools
```

```python
pte = model.export(
    output_dir="exports/executorch-coreml",
    format="executorch",
    backend="coreml",
    shape=(512, 512),
)
```

Qualcomm QNN:

```python
pte = model.export(
    output_dir="exports/executorch-qnn",
    format="executorch",
    backend="qnn",
    soc="SM8650",
    shape=(512, 512),
)
```

QNN requires a source build of ExecuTorch against the Qualcomm QAIRT/QNN SDK; the pip wheel is insufficient. Validate on the actual Snapdragon device.

Runtime notes:

- Inputs must be contiguous NCHW tensors. After a transpose or permute, call `.contiguous()` or `np.ascontiguousarray(...)` before runtime execution.
- If `executorch.runtime` fails to import due to a torch ABI mismatch, export may still work; only local `.pte` loading/running is broken. Use a torch version compatible with the installed ExecuTorch wheel.

## Native CoreML workflow

Install on an Apple-capable environment when you need to run the model locally:

```bash
pip install "rfdetr[coreml]"
```

Export:

```python
from rfdetr import RFDETRSmall

model = RFDETRSmall(pretrain_weights="checkpoint.pth")
mlpackage = model.export(
    output_dir="exports/coreml",
    format="coreml",
    shape=(512, 512),
    coreml_precision="float32",  # or "float16" for a smaller ANE-oriented bundle
)
print(mlpackage)
```

Rules:

- Native CoreML is a `.mlpackage` for Xcode/Core ML and is not an ExecuTorch `.pte`.
- Fixed shapes only; export one artifact per batch/shape.
- FP32 is the conservative parity mode. FP16 is expected to drift numerically but may be better for ANE deployment.
- Keypoint native CoreML export is not verified in the evidence; prefer detection/segmentation for this route unless new validation exists.

## Roboflow deployment workflow

For a local, network-free bundle:

```python
from rfdetr import RFDETRSmall

model = RFDETRSmall(pretrain_weights="checkpoint.pth")
model.export_for_roboflow("roboflow_bundle")
```

This writes:

- `weights.pt`
- `class_names.txt`

For upload:

```python
model.deploy_to_roboflow(
    workspace="workspace-id",
    project_id="project-id",
    version=1,
    api_key="ROBOFLOW_API_KEY_VALUE",
)
```

Use environment variable `ROBOFLOW_API_KEY` instead of passing `api_key` when appropriate. Do not put API keys in committed files or generated artifacts.

## Latency benchmarking route

The benchmark notebook compares:

- plain PyTorch `predict()` FP32 baseline,
- `model.inference(dtype=torch.float16)` JIT/optimized runtime,
- ONNX Runtime GPU.

Use the benchmark pattern only for deployment evaluation. It is not an export correctness gate and may need CUDA-specific ONNX Runtime wheels for accurate GPU measurement.
