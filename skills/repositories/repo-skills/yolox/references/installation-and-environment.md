# YOLOX Installation And Environment

Use this reference before running YOLOX workflows in a new environment. It covers public install choices, required runtime dependencies, backend checks, and optional deployment packages.

## Package identity

- Distribution/import name: `yolox`
- Version captured for this generated skill: `0.3.0`
- Main public import check:

```bash
python -c "import yolox; print(yolox.__version__)"
```

YOLOX is a PyTorch package. The source distribution installs the `yolox` package plus packaged modules for `yolox.tools` and default experiment files.

## Public install pattern

A typical source install is:

```bash
python -m pip install -U pip wheel setuptools
python -m pip install -r requirements.txt
python -m pip install -v -e .
```

For reusable project environments, prefer an isolated Python environment. Choose a Python version supported by the required PyTorch, torchvision, OpenCV, pycocotools, ONNX, and optional deployment wheels. Older pinned export packages can be Python-version sensitive, so verify wheels before committing to a Python version.

## Base dependencies

The package requirements include:

- `numpy`
- `torch>=1.7`
- `torchvision`
- `opencv_python`
- `loguru`
- `tqdm`
- `thop`
- `ninja`
- `tabulate`
- `psutil`
- `tensorboard`
- `pycocotools>=2.0.2`
- `onnx>=1.13.0`
- `onnx-simplifier==0.4.10`

Practical import check:

```bash
python - <<'PY'
import yolox, torch, torchvision, cv2
print('yolox', yolox.__version__)
print('torch', torch.__version__, 'cuda', torch.version.cuda)
print('torchvision', torchvision.__version__)
print('opencv', cv2.__version__)
PY
```

## CPU versus CUDA

CPU is enough for import checks, CLI help, Exp inspection, dry-run export planning, and very small model-construction diagnostics. CUDA is normally needed for realistic YOLOX training, evaluation, FP16, large inference workloads, and TensorRT conversion.

CUDA check:

```bash
python - <<'PY'
import torch
print('cuda available:', torch.cuda.is_available())
print('device count:', torch.cuda.device_count())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
    torch.empty((1,), device='cuda')
    print('tiny allocation ok')
PY
```

Use a PyTorch/torchvision build compatible with the host driver and GPU. Do not treat a CPU-only torch import as proof that CUDA training, FP16, or TensorRT workflows are available.

## Package-level smoke helper

Run the root helper from the root skill directory:

```bash
python scripts/check_yolox_install.py --name yolox-nano --device auto --test-size 64
```

What it proves:

- YOLOX and core/support imports are available.
- A built-in or custom experiment can be resolved.
- A YOLOX model can be constructed.
- Optional CUDA allocation works when requested and available.
- Optional dummy forward can execute when enabled.

What it does not prove:

- Checkpoint compatibility or accuracy.
- Dataset availability.
- Full training/evaluation stability.
- Optional vendor deployment SDK availability.

## Build-extension notes

YOLOX includes a C++ fast COCO evaluation extension. Source installs may compile it using PyTorch's C++ extension machinery. If editable/source installation fails around C++ headers or `ninja`, check that compiler tools, PyTorch headers, Python headers, `ninja`, and pybind11 headers are available for the active environment. The generated skill does not require future agents to build from the same local setup; record only public dependency requirements and observed symptoms.

## Optional deployment packages

| Workflow | Extra packages/tooling | Notes |
|---|---|---|
| ONNX export | `onnx`, `onnx-simplifier` | Base requirements include these, but the pinned simplifier may have Python-version wheel constraints. |
| ONNXRuntime inference | `onnxruntime` | Required to execute ONNX models with the ONNXRuntime Python demo pattern. |
| TensorRT | NVIDIA GPU, TensorRT Python/C++ SDK, `torch2trt` | Optional and backend-specific; verify versions against PyTorch/CUDA. |
| OpenVINO | OpenVINO runtime/dev tools | Optional Intel deployment stack; opset and conversion details can matter. |
| ncnn | ncnn tools/SDK, C++ compiler or Android toolchain | Optional mobile/C++ stack; conversion may need graph edits. |
| MegEngine | MegEngine runtime/tools | Separate framework path, not PyTorch base install. |
| nebullvm | nebullvm stack and supported accelerators | Optional optimization stack with additional dependencies. |
| W&B logging | `wandb` plus credentials | Training-only logger path. |
| MLflow logging | `mlflow`, `python-dotenv`, tracking server/env vars | Training-only logger path. |

## Data and checkpoint resources

YOLOX installation does not include pretrained weights or datasets. Future agents should ask for or locate:

- A checkpoint that matches the selected default model name or custom `Exp`.
- COCO/VOC/custom dataset roots and annotation files for training/evaluation.
- Permission and budget for downloads, training, evaluation, or benchmark-scale runs.

If resources are missing, use dry-run and inspection helpers instead of launching a failing full workflow.
