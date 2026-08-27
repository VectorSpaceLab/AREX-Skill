# Install and backend guidance

Read this before using GluonCV APIs or constructing script commands. GluonCV 0.11.0 is a legacy dual-backend package; most failures come from framework, Python, NumPy, Pillow, optional dependency, or GPU-version mismatches.

## Backend guard

`import gluoncv` succeeds only when at least one backend family imports and passes version checks:

- MXNet: `>=1.4.0,<2.0.0`
- PyTorch: `>=1.4.0,<2.0.0`

When neither backend is present, import raises an error saying both `mxnet` and `torch` are missing. When both are present, GluonCV may warn about increased GPU memory footprint.

## Practical environment choices

For a new user environment, choose the smallest stack that matches the task:

| Task | Suggested base |
| --- | --- |
| MXNet model zoo, datasets, transforms, classic scripts | Python compatible with MXNet 1.x, `mxnet` or the documented MXNet CUDA wheel, `numpy<1.24`, `gluoncv` |
| PyTorch action-recognition/video or DirectPose | Python compatible with Torch 1.x, `torch<2`, matching `torchvision`, `Pillow<10`, `gluoncv` |
| CPU registry/API inspection | One CPU backend is enough; install MXNet CPU and/or Torch CPU according to the APIs being inspected. |
| CUDA training/inference | Install the backend-specific CUDA wheel that matches the driver/toolkit; verify with a tiny device allocation before running GluonCV scripts. |
| AutoGluon wrappers | Treat as optional legacy stack; `gluoncv[auto]` pins `autogluon.core==0.3.1`. |
| Export/ONNX/TVM/quantized workflows | Add only the export backend required by the selected workflow. |

Avoid installing broad extras (`full`, old AutoGluon, DALI, Horovod, TVM, ONNX, `decord`, `pycocotools`) unless the user selected the corresponding workflow.

## Public install patterns

MXNet CPU-oriented example:

```bash
python -m pip install 'numpy<1.24'
python -m pip install 'mxnet>=1.4,<2.0'
python -m pip install gluoncv
```

Torch CPU-oriented legacy example:

```bash
python -m pip install 'torch>=1.4,<2' 'torchvision<0.15'
python -m pip install 'Pillow<10'
python -m pip install gluoncv
```

Development checkout example:

```bash
python -m pip install -e .
```

Use backend-specific official install commands for CUDA. Do not treat a CPU-only framework import as proof that CUDA training, benchmarks, or DDP work.

## Minimal import and registry checks

```python
import gluoncv
print(gluoncv.__version__)
print('mxnet?', getattr(gluoncv, '_found_mxnet', None))
print('torch?', getattr(gluoncv, '_found_pytorch', None))
```

MXNet model-zoo check:

```python
from gluoncv import model_zoo
print(len(list(model_zoo.get_model_list())))
net = model_zoo.get_model('cifar_resnet20_v1', pretrained=False)
```

Torch model-zoo check:

```python
from gluoncv.torch.engine.config import get_cfg_defaults
from gluoncv.torch.model_zoo import get_model, get_model_list
cfg = get_cfg_defaults()
cfg.CONFIG.MODEL.NAME = 'resnet18_v1b_kinetics400'
cfg.CONFIG.MODEL.PRETRAINED = False
cfg.CONFIG.DATA.NUM_CLASSES = 400
print(len(list(get_model_list())))
net = get_model(cfg)
```

## Optional dependencies by workflow

| Optional package/tool | Needed for |
| --- | --- |
| `torchvision` | Torch data/model imports and video workflows. |
| `decord` | Efficient video decoding in action-recognition workflows. |
| `pycocotools` | COCO detection/instance/keypoint metrics and some dataset paths. |
| `tensorboardx` | Training logging in selected scripts. |
| `autogluon.core` | `gluoncv.auto` image classification/object detection tasks. |
| `timm` | Torch model dispatch in some AutoGluon classification paths. |
| Cython build | Optional MXNet bbox/RPN extension modules from source. |
| DALI | ImageNet data pipeline variants. |
| Horovod | Distributed ImageNet training variant. |
| ONNX/ONNXRuntime | ONNX export/inference workflows. |
| TVM | DirectPose/compiled deployment workflows. |

## Backend verification checklist

Before real jobs:

1. `python scripts/check_gluoncv_environment.py` passes for the selected backend.
2. A tiny MXNet or Torch CPU/API smoke passes, or a CUDA smoke proves device access when CUDA is required.
3. Dataset roots and annotations are validated.
4. Pretrained download/cache policy is approved if using `pretrained=True` or export from pretrained weights.
5. Optional dependencies are installed only for the workflow being run.
6. GPU IDs, batch size, clip length, image shape, output directory, and overwrite policy are explicit.
