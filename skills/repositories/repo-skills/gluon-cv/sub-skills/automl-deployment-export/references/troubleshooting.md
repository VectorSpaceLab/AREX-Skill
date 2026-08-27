# AutoML and export troubleshooting

Use this guide when optional AutoGluon, export, ONNX, TVM, quantization, pretrained-weight, or deployment failures appear. Keep base GluonCV import problems separate from these optional workflows unless the stack trace proves the base import is the failing layer.

## Quick triage

| Symptom | Likely cause | First response |
| --- | --- | --- |
| `ModuleNotFoundError: autogluon` or `autogluon.core` | `gluoncv.auto` is optional and the base install does not include old AutoGluon | Explain that AutoML requires the legacy `autogluon.core==0.3.1`-era stack; do not treat it as a base GluonCV failure. |
| AutoGluon cannot resolve/install on modern Python | Old AutoGluon pin and legacy MXNet/Torch constraints | Use an older compatible Python environment for AutoML, or route to non-AutoML GluonCV training/scripts. |
| `ModuleNotFoundError: timm` | Torch/timm image-classification dispatch unavailable | Install a compatible `timm` only if the legacy AutoGluon/Torch stack supports it, or choose an MXNet GluonCV model name. |
| `Model not found ... Install torch and timm` | ImageClassification could not find the model in the installed backend registries | Validate whether the model name belongs to `timm` or MXNet GluonCV; install the missing backend only when compatible. |
| No GPU detected; task uses small config | AutoGluon resource helpers report zero GPUs or config requested zero usable GPUs | This is expected fallback to `LiteConfig`; reduce expectations, use tiny smoke data, or prepare a GPU-capable compatible stack. |
| ObjectDetection transfer model mismatch | `estimator` and `transfer` strings do not match | Pick transfer names matching the estimator family, such as `ssd_...` for `estimator='ssd'`. |
| `pycocotools` missing | COCO AutoML dataset parsing/evaluation optional dependency missing | Install compatible `pycocotools`/Cython for the platform, or use VOC-style data. |
| Export checker says invalid model | Name is not in the MXNet GluonCV model registry | Route to `../mxnet-model-zoo/` to find a valid MXNet name; Torch-only names cannot be exported with MXNet `export_block`. |
| Real export downloads unexpectedly | `get_model(name, pretrained=True)` needs pretrained weights not in cache | Confirm network/cache policy before export; use `pretrained=False` only for dry instantiation, not pretrained deployment. |
| `export_block` layout/preprocess assertion | Mismatch between `preprocess` and `layout` | Use HWC with default preprocess; use CHW/CTHW only when preprocess is disabled and external preprocessing is planned. |
| `RuntimeError` during export shape trial | Model needs explicit `data_shape` or is not generic-export friendly | Provide family-specific shapes or exclude difficult model families from generic export. |
| ONNX conversion operator failure | MXNet ONNX exporter lacks support for model operators | Try a different MXNet/ONNX stack or treat ONNX as unsupported for that model. |
| `ModuleNotFoundError: tvm` | TVM is optional and not part of base GluonCV | Install TVM only for explicit TVM export tasks; otherwise use MXNet JSON/params export. |
| Quantized model missing or accuracy poor | Unsupported model name, missing MKL/quantization support, or poor calibration data | Use known int8 candidates and representative calibration data; do not promise speed/accuracy without target benchmarking. |

## AutoML import and compatibility failures

### Missing AutoGluon

`gluoncv.auto.tasks` imports AutoGluon Core directly. If that import fails:

1. Do not reinstall base GluonCV first; base GluonCV and AutoML have different dependency requirements.
2. Explain that `gluoncv[auto]` historically pins `autogluon.core==0.3.1`.
3. Check the user's Python version and package constraints. Modern Python versions are often incompatible with this legacy pin.
4. If the user only needs model training scripts, route to `../training-evaluation-scripts/` instead of forcing AutoGluon.
5. If the user only needs model APIs, route to `../mxnet-model-zoo/` or `../torch-video-workflows/`.

### Deprecation warning

Importing `gluoncv.auto.tasks` warns that the Auto module was planned for deprecation in favor of AutoGluon Vision. This warning is informational. It does not mean a task failed, but it is a signal to avoid building new long-lived systems on this API unless the user explicitly needs legacy GluonCV behavior.

### Modern Python or resolver conflicts

Common legacy constraints:

- AutoGluon Core pin is old.
- MXNet accepted by GluonCV is `<2.0`.
- Legacy MXNet stacks can fail with newer NumPy versions that removed aliases such as `np.bool`.
- GluonCV's Torch side expects Torch 1.x-era packages and can be affected by newer Pillow/TorchVision changes.

Safe response pattern:

```text
This is an optional legacy AutoML stack issue, not proof that GluonCV itself is unusable. Use a separate compatible environment for AutoML, or switch to non-AutoML GluonCV model/training workflows.
```

Do not mutate an existing user environment with broad downgrades unless the user approves.

## AutoML task failures

### No GPU / `LiteConfig` fallback

Task constructors use resource discovery and choose conservative `LiteConfig` defaults when no GPU is available or requested GPUs are capped to zero. Expected effects:

- `ngpus_per_trial=0`.
- Smaller model/transfer search spaces.
- Fewer trials by default.
- Very slow training for non-tiny data.

Fixes:

- For CPU smoke tests, use tiny data, `num_trials=1`, `epochs=1`, small `batch_size`, and a short integer `time_limit`.
- For real training, prepare a compatible GPU AutoGluon/MXNet/Torch stack and validate GPU visibility from that environment.
- Do not claim CUDA behavior from a CPU-only environment.

### `fit` complains about validation data

If `train_data` is not a pandas/DataFrame-backed task dataset, `fit` cannot split it automatically and asserts that `val_data` is provided. Supply explicit `val_data` or convert data through the task dataset helpers.

### `time_limit` type error

Task-level `fit(..., time_limit=...)` expects an integer number of seconds or `None`. Convert floats/strings before passing them.

### Object-detection estimator/transfer mismatch

`ObjectDetection` filters `transfer` names by `estimator` when both are provided. Examples:

- `estimator='ssd'` needs transfer names containing `ssd`.
- `estimator='yolo3'` needs transfer names containing `yolo3`.
- `estimator='faster_rcnn'` needs transfer names containing `faster_rcnn`.
- `estimator='center_net'` needs transfer names containing `center_net`.

If no transfer names match, choose a family-consistent transfer value or remove the estimator constraint.

### Save/load context surprises

Auto estimators pickle their state. Loading calls context selection logic that can fall back to CPU if saved GPU context is unavailable. If a loaded estimator unexpectedly runs on CPU:

- Check whether the requested GPU backend is present in the current environment.
- Pass a load context when the estimator class supports it, such as `ctx='cpu'`, `ctx='gpu'`, or a GPU-id list.
- Avoid assuming that a checkpoint saved on one machine will reload with identical accelerators elsewhere.

## Export failures

### Invalid model name

Run the bundled checker:

```bash
python scripts/export_name_check.py --model MODEL_NAME
```

If invalid:

- The name may be Torch-only or from another library.
- The name may be a training-script shorthand rather than a model-zoo registry key.
- Use `../mxnet-model-zoo/` to discover valid names.

### MXNet missing or incompatible

MXNet export is not a Torch export path. It requires MXNet and `gluoncv.model_zoo`. If MXNet import fails:

- Use a GluonCV-compatible MXNet 1.x environment.
- Keep NumPy/Pillow compatibility in mind for legacy stacks.
- Do not try to export Torch DirectPose or Torch action models through MXNet `export_block`.

### Pretrained weights/cache/network

The export-pretrained pattern calls `get_model(name, pretrained=True)`. That may download weights. If network/cache is not allowed:

- Stop after model-name validation and explain prerequisites.
- Do not call `get_model(..., pretrained=True)`.
- A `pretrained=False` model can test construction but does not produce a meaningful pretrained deployment artifact unless initialized/trained weights are supplied.

### Layout and preprocess failures

Rules:

- Default preprocessing requires raw RGB HWC input and `layout='HWC'`.
- Disabling preprocessing requires caller-managed normalization and `layout='CHW'` for 2D or `layout='CTHW'` for 3D/video.
- ONNX and C++ consumers must match whatever preprocessing is embedded or externalized.

If a user gets shape/layout errors, ask for:

- Model name.
- Intended input shape.
- Whether exported graph should include preprocessing.
- Whether the downstream runtime expects HWC, CHW, or CTHW.

### Difficult model families

Some models need explicit data shapes or fail generic export because of operators, target generators, dynamic shape assumptions, or unsupported layers. Common caution areas:

- Semantic segmentation families often need fixed shapes.
- Video/action models need temporal layout and explicit CTHW shapes.
- Some GroupNorm/DCNv2, SiamRPN, DANet/FastSCNN, Monodepth, and other specialized models may fail generic export.
- Faster R-CNN/Mask R-CNN/CenterNet outputs can require model-family-specific downstream parsing.

If the model is difficult, provide a prerequisite plan and suggest a minimal export smoke only after dependencies, weights, output location, and runtime target are confirmed.

## ONNX failures

ONNX conversion is optional and fragile relative to plain MXNet JSON/params export.

Check:

1. Does symbol/params export succeed first?
2. Is `mxnet.contrib.onnx` available in the installed MXNet?
3. Are `onnx` and `onnxruntime` installed?
4. Does the model use operators unsupported by that MXNet ONNX exporter?
5. Does the input shape match the exported graph?

When conversion fails at unsupported operators, do not promise a simple code fix. Try another model, another compatible MXNet ONNX stack, or plain MXNet deployment artifacts.

## TVM failures

TVM is not bundled with base GluonCV. Install and use it only when the user explicitly needs TVM export.

Common issues:

- `ModuleNotFoundError: tvm`: install TVM or skip TVM export.
- Missing fixed shape: provide `data_shape` for MXNet `export_tvm` or representative input for TorchScript tracing.
- CUDA target failure: CPU TVM target `llvm` may work while `cuda` target needs GPU-enabled TVM and runtime support.
- DirectPose NMS conversion failure: ensure the custom `torchvision::nms` converter is registered in the TVM Relay PyTorch frontend call.
- Autotuning runs too long: avoid `use_autotvm=True` unless tuning time and benchmark conditions are explicitly approved.

## Quantized/int8 failures

Quantized/int8 workflows depend on model support, MXNet quantization/MKL support, calibration quality, and CPU hardware.

Safe responses:

- Validate that the model name has an int8/quantized candidate.
- Use script/API flags only for workflows that document `--quantized`, `--deploy`, `--model-prefix`, or calibration options.
- For custom quantization, require representative calibration data and specify `calib_mode` deliberately.
- Benchmark on the target machine before claiming speedups.
- If accuracy drops, improve calibration data, try `entropy` calibration, or fall back to FP32 deployment.

## When to ask for clarification

Ask before running or recommending side-effecting commands when any of these are missing:

- Permission to download pretrained weights or datasets.
- Permission to write exported artifacts.
- Target runtime format: MXNet JSON/params, ONNX, TVM, C++ demo, or quantized MXNet.
- Model name and expected input shape/layout.
- CPU versus GPU target and performance requirements.
- Whether the user must use legacy `gluoncv.auto` or can use newer AutoGluon/other training workflows.
