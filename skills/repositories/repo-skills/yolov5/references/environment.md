# Environment and Install Notes

## Clone-run model

YOLOv5 is normally used from a repository checkout. The public install path is:

```bash
pip install -r requirements.txt
python - <<'PY'
import torch
import models.common, models.yolo, utils.general
print(torch.__version__)
print('cuda', torch.cuda.is_available())
PY
```

Do not assume `import yolov5` or a `yolov5` console script exists. The repository exposes workflow entrypoints such as the detection, segmentation, classification, export, benchmark, and Flask scripts. Future agents should use this skill's planner/checker scripts before running those entrypoints.

## Python and base dependencies

- Python floor: `>=3.8`.
- Core runtime requirements: matplotlib, numpy, OpenCV, Pillow, PyYAML, requests, scipy, torch, torchvision, psutil, ultralytics-thop, pandas, seaborn, packaging, and the `ultralytics` package.
- The repository imports `ultralytics.utils.patches.torch_load` in Hub/model-loading paths, so the `ultralytics` dependency is not optional for current code.
- Use a disposable or project-specific environment. Avoid mutating Conda base or a shared research environment.

## PyTorch and CUDA

- CPU is enough for import checks, parser help, some tiny inference/export checks, and Flask dummy-service tests.
- CUDA is recommended for real training and large inference/validation. Install a PyTorch wheel that matches the host driver and Python version.
- A CUDA-capable PyTorch environment usually covers CPU checks too.
- Do not treat `torch.cuda.is_available() == False` as a harmless warning if the task requires TensorRT, CUDA export, half precision, or realistic training throughput.

Safe backend probe:

```bash
python - <<'PY'
import torch
print('torch', torch.__version__)
print('torch cuda runtime', torch.version.cuda)
print('cuda available', torch.cuda.is_available())
if torch.cuda.is_available():
    print('device count', torch.cuda.device_count())
    print('device 0', torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
    torch.empty((1,), device='cuda')
PY
```

## Optional dependency groups

Install optional dependencies only for the selected workflow:

| Need | Minimal direction | Notes |
| --- | --- | --- |
| ONNX export | `pip install onnx` | Default `export.py` includes TorchScript and ONNX. Add `onnxslim`/`onnxruntime` only for slimming or runtime validation. |
| OpenVINO export | `pip install openvino` | OpenVINO export goes through ONNX first. |
| TensorRT engine | NVIDIA GPU + TensorRT Python/runtime matching target runtime | Engine files are version/runtime sensitive; validate on the target deployment stack. |
| CoreML | `coremltools`; best on macOS for runtime validation | Package availability varies by platform. |
| TensorFlow/TFLite/TF.js | TensorFlow / tensorflowjs pins from metadata | Heavy install; keep separate if it conflicts with PyTorch or Keras. |
| Paddle export | PaddlePaddle packages | Optional; do not install for ordinary PyTorch workflows. |
| Edge TPU | Edge TPU compiler/runtime tooling | External system toolchain; shell-safety tests do not prove the compiler exists. |
| Flask REST API | `pip install Flask` | Only needed for `utils/flask_rest_api` style serving. |
| Tests | `pip install pytest` | Needed for selected native verification candidates, not for routine repo usage. |
| Logging integrations | Comet, ClearML, W&B, TensorBoard | External services/credentials; install only when logging is part of the task. |

## Editable/package install caveat

Current YOLOv5 metadata may fail editable installation in modern setuptools because the repository uses a flat layout with multiple top-level import packages and task directories. Treat that as a packaging limitation, not as a failed user workflow. The supported path is clone-run execution with dependencies installed and repository modules importable from the checkout.

If a task explicitly needs packaging work, route it as repository maintenance rather than normal YOLOv5 usage.

## Safe environment checker

Run this bundled helper from an environment where the YOLOv5 checkout modules are importable:

```bash
python scripts/check_yolov5_env.py --json
```

It checks imports, dependency versions, CUDA visibility, and optional export/service modules without downloads, model loading, training, export conversion, or server startup.
