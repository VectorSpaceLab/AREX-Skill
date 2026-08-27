# MMYOLO Installation and Environment Notes

Use this reference before running MMYOLO APIs, MIM commands, training/evaluation, inference, or deployment workflows.

## Package and dependency constraints

MMYOLO v0.6.0 imports and version-checks these OpenMMLab packages:

| Package | Required range |
| --- | --- |
| `mmcv` | `>=2.0.0rc4,<2.1.0` |
| `mmengine` | `>=0.7.1,<1.0.0` |
| `mmdet` | `>=3.0.0,<4.0.0` |

Base runtime requirements also include `numpy` and `prettytable`. PyTorch and TorchVision are required by the OpenMMLab stack even when the task is CPU-only.

## Preferred install choices

For a fresh environment, prefer a Python version supported by the OpenMMLab package set used for this MMYOLO release; Python 3.8 is a conservative choice for v0.6.0-era wheels.

Typical OpenMMLab install path:

```shell
pip install -U openmim
mim install "mmengine>=0.7.1,<1.0.0"
mim install "mmcv>=2.0.0rc4,<2.1.0"
mim install "mmdet>=3.0.0,<4.0.0"
mim install mmyolo
```

When working from a local source checkout for development, install the same core dependencies first, then install the package in editable mode. Keep this as a development choice, not as a dependency of the generated skill itself.

## Optional dependency groups

Install optional packages only when the requested workflow needs them:

| Workflow | Optional packages |
| --- | --- |
| Albumentations transforms | `albumentations` using MMYOLO's documented no-binary recommendation when OpenCV conflicts matter. |
| Large-image/SAHI inference | `sahi>=0.11.4`. |
| Pose/rotated/downstream workflows | `mmpose`, `mmrotate`, or `mmrazor` as required by the config/project. |
| Feature-map or CAM visualization | plotting stack; BoxAM/Grad-CAM needs a Grad-CAM package. |
| ONNX/ONNXRuntime deployment | `onnx`, optional `onnxsim`, and `onnxruntime`. |
| MMDeploy deployment | `mmdeploy` and matching backend runtime packages. |
| TensorRT/RKNN/DeepStream | vendor toolchains, hardware, and matching Python bindings. |

Do not install all optional groups just to inspect configs or build ordinary train/test commands.

## Minimal import check

Run the root helper when diagnosing an environment:

```shell
python scripts/check_mmyolo_environment.py --json
```

For a config parse check:

```shell
python scripts/check_mmyolo_environment.py --config CONFIG.py
```

A healthy CPU inspection environment should import `torch`, `mmcv`, `mmengine`, `mmdet`, `mmyolo`, and `prettytable`, and should parse simple MMYOLO configs. CUDA/TensorRT/RKNN readiness needs separate backend checks and hardware.

## CPU vs GPU expectations

- CPU is enough for import checks, config parsing, command construction, many unit-style inspections, and some small inference/evaluation attempts.
- Real training and performance evaluation are normally GPU-oriented and may be impractically slow on CPU.
- TensorRT, RKNN, and DeepStream cannot be verified by CPU import checks; they need vendor packages and hardware.
- A GPU-visible host does not automatically mean the Python environment has GPU-capable PyTorch/MMCV/TensorRT wheels.

## OpenMIM command discovery

Use package-command discovery before relying on MIM launch commands:

```shell
mim train mmyolo --help
mim test mmyolo --help
mim run mmyolo --help
```

If commands are missing, repair the package installation or choose a package version that includes MIM metadata.
