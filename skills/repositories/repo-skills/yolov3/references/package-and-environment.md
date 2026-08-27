# Package and Environment Reference

## Install contract

Operate YOLOv3 from a repository checkout and install dependencies with:

```bash
python -m pip install -r requirements.txt
```

The package metadata names the project `YOLOv3`, requires Python `>=3.8`, and lists runtime dependencies including PyTorch, torchvision, OpenCV, Ultralytics, ultralytics-thop, NumPy, Pillow, PyYAML, Requests, SciPy, pandas, seaborn, packaging, and psutil. Optional groups are `dev`, `export`, `logging`, and `extra`.

Do not rely on editable installation for normal usage. This repo is script-oriented and may fail editable install in some toolchains when project metadata lacks a version field. That is a maintenance topic, not a normal user setup path.

## Backend matrix

| Backend or extra | Status | Use |
| --- | --- | --- |
| CPU PyTorch | Required baseline | Builds models and runs deterministic smokes. |
| CUDA PyTorch | Optional | Faster inference/training, multi-GPU, DDP, and FP16. Verify torch CUDA and device allocation before use. |
| ONNX / ONNX Runtime | Optional | ONNX export and runtime; OpenCV DNN can read some ONNX models through `--dnn`. |
| OpenVINO | Optional CPU deployment | Export requires OpenVINO packages. |
| TensorRT | Optional GPU-only | `.engine` export/inference requires CUDA. |
| CoreML | Optional Apple deployment | Export uses `coremltools`; macOS is the natural runtime target. |
| PaddlePaddle | Optional | Paddle export/runtime. |
| pycocotools | Optional metrics | COCO JSON evaluation summaries. |
| W&B, ClearML, Comet, TensorBoard | Optional logging | Missing loggers should not block core training. |

## Minimal readiness probe

```bash
python - <<'PY'
import torch
from models.yolo import Model
model = Model('models/yolov3-tiny.yaml').eval()
out = model(torch.zeros(1, 3, 64, 64))[0]
print('ok', tuple(out.shape))
PY
```

Expected output shape is `(1, 60, 85)` for the default 80-class tiny model at image size 64.
