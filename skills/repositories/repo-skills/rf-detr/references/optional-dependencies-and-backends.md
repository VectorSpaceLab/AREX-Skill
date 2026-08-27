# Optional Dependencies and Backends

## When to read

Read this before installing RF-DETR extras, choosing a backend-specific workflow, or diagnosing a missing optional dependency. Keep the environment minimal for the task: do not install every extra unless the user explicitly needs all affected workflows and accepts the resolver/backtracking cost.

## Baseline package

```bash
pip install rfdetr
```

Baseline dependencies include PyTorch, TorchVision, Transformers, Pydantic, Supervision, NumPy, Requests, tqdm, and deprecation helpers. This is sufficient to import model classes and run normal PyTorch prediction when pretrained weights/checkpoints are available.

## Extras by workflow

| Extra | Use when | Notes and backend limits |
| --- | --- | --- |
| `train` | `model.train`, `model.evaluate`, PyTorch Lightning modules, COCO metrics, Roboflow/RF100 helpers | Adds Lightning, PEFT, TorchMetrics detection, COCO evaluation, Roboflow/RF100 packages. Long training remains hardware/data-dependent. |
| `cli` | `rfdetr fit/validate/test/predict` Lightning CLI and YAML configs | Usually pair with `train`: `pip install "rfdetr[train,cli]"`. |
| `augment` | Custom Albumentations CPU transforms or Kornia GPU-side augmentation | Default training/validation/prediction/export preprocessing uses TorchVision. `augmentation_backend="auto"` can pick Kornia only when CUDA and Kornia are available. |
| `lora` | LoRA fine-tuning support | Training already includes PEFT, so use this for focused LoRA-only package installs. |
| `onnx` | ONNX export, ONNX Runtime checks, ONNX simplification/graph tooling | Stable baseline export route and often the best artifact for downstream runtimes. |
| `tensorrt` | Build RF-DETR TensorRT engines on NVIDIA GPU hosts | TensorRT engines are non-portable and tied to GPU architecture/TensorRT version. The extra does not include `pycuda` benchmarking dependencies. |
| `tensorrt-bench` | Async TensorRT benchmark helper that needs PyCUDA | Requires CUDA toolkit development headers; do not install for ordinary TensorRT conversion. |
| `tflite` | Experimental TFLite export via ONNX-to-TF path | Dependency markers target a narrow Python range in package metadata; isolate this backend from unrelated extras. |
| `executorch` | Experimental ExecuTorch `.pte` export, especially XNNPACK CPU delegate | Python/platform wheel availability and torch ABI constraints matter. QNN requires source-build/vendor SDK work beyond a simple pip wheel. |
| `coreml` | Native CoreML `.mlpackage` export on Apple platforms | Has torch/coremltools compatibility constraints and is macOS-centered. Linux import checks do not verify CoreML export. |
| `loggers` | TensorBoard, W&B, MLflow, ClearML experiment logging | Some services require credentials or local setup; missing credentials are not RF-DETR package failures. |
| `visual` | Plotting/analysis helpers | Useful for visualization docs/tests, not required for core training or prediction. |
| `plus` | Plus XLarge/2XLarge models | Installs `rfdetr_plus`; separate license/account boundary. |
| `xla` | XLA/TPU or CPU-PJRT validation paths | Torch and torch_xla minor versions must match; Linux wheel constraints apply. |

## Backend verification rules

- CPU import verifies only CPU/package usability.
- CUDA availability from `nvidia-smi` verifies host hardware visibility, not RF-DETR TensorRT or training correctness.
- A torch CUDA smoke check should allocate a tiny tensor before claiming CUDA framework readiness.
- TensorRT readiness requires TensorRT Python package/import and a compatible NVIDIA runtime. Building a `.trt` engine is target-specific.
- CoreML readiness requires a supported macOS/CoreML toolchain; Linux cannot prove native CoreML parity.
- ExecuTorch QNN readiness requires a target SoC and vendor/QNN build chain; do not imply the pip extra is enough.
- TFLite readiness depends on ONNX/TensorFlow/onnx2tf compatibility; isolate and test this path separately.
- Plus model import errors should mention `pip install "rfdetr[plus]"` and license/account prerequisites, not suggest reinstalling baseline RF-DETR.

## Minimal install recipes

```bash
# Inference / package inspection
pip install rfdetr

# Training with CLI and common custom augmentations
pip install "rfdetr[train,cli,augment]"

# Training with experiment trackers
pip install "rfdetr[train,cli,loggers]"

# Export only to ONNX
pip install "rfdetr[onnx]"

# TensorRT export on the build GPU host
pip install "rfdetr[onnx,tensorrt]"
```

Avoid `pip install "rfdetr[plus,tflite,executorch,coreml,xla,tensorrt,train,docs,tests]"` style installs unless a task explicitly needs all of those surfaces. Several extras have documented dependency conflicts or platform markers.

## Safe backend probes

Use the root environment script for quick probes:

```bash
python scripts/check_rfdetr_environment.py --extras train onnx augment --check-cuda
```

Use sub-skill-specific scripts before task-specific work:

```bash
python sub-skills/inference-and-models/scripts/inspect_rfdetr_models.py
python sub-skills/training-and-cli/scripts/inspect_training_config.py
python sub-skills/export-and-deployment/scripts/inspect_export_options.py --variant rfdetr-small --format onnx --shape 512 512
```

These scripts are read-only and do not train, export, instantiate pretrained models, or download weights.
