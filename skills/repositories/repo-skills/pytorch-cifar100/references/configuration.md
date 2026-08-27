# Configuration and Runtime Facts

## Purpose

Read this for shared pytorch-cifar100 setup, dependencies, paths, constants, and backend expectations used by the model, training, and evaluation sub-skills.

## Repository style

The project is a script-based PyTorch checkout. It has no package metadata or console entry points. Commands normally run from the checkout root so `utils.py`, `conf/`, and `models/` are importable.

## Core dependencies

| Dependency | Required for | Notes |
| --- | --- | --- |
| Python | all workflows | README describes Python 3.6-era experiments; modern Python can be used if PyTorch/TorchVision support it. |
| PyTorch | all model/training/evaluation workflows | README used `pytorch1.6.0+cu101`; verify compatibility in the active environment rather than assuming that exact historical wheel. |
| TorchVision | CIFAR-100 dataloaders and transforms | `train.py` and `test.py` use `torchvision.datasets.CIFAR100(..., download=True)`. |
| NumPy | utilities and dataset support | Used in helper functions and legacy data code. |
| TensorBoard | `train.py` import and training logs | `train.py` imports `torch.utils.tensorboard.SummaryWriter`; missing TensorBoard can break even parser/help import in some environments. |
| Matplotlib | `test.py` and `lr_finder.py` imports | `test.py` imports pyplot though it does not plot during ordinary evaluation. |
| OpenCV (`cv2`) | optional LR finder | Only needed for `lr_finder.py`; not needed for primary training/evaluation commands. |
| scikit-image | optional legacy dataset import | `dataset.py` imports `skimage.io`; current train/test paths use TorchVision instead. |

## Backend policy

- CPU is sufficient for selected smoke, parser, command-builder, and representative model checks.
- CUDA is optional for `-gpu` training/evaluation and is recommended for full 200-epoch experiments.
- Do not treat a CPU check as proof of CUDA runtime behavior when the task explicitly requires GPU memory, CUDA kernels, or full-speed training.
- Before using `-gpu`, confirm `torch.cuda.is_available()` and a compatible PyTorch CUDA build.

## Shared paths and constants

| Setting | Value | Used by |
| --- | --- | --- |
| CIFAR-100 data root | `./data` | Training and evaluation dataloaders. |
| Checkpoint root | `checkpoint` | `train.py` saves and resumes under `checkpoint/<net>/<timestamp>/`. |
| TensorBoard root | `runs` | `train.py` writes under `runs/<net>/<TIME_NOW>/`. |
| Epochs | `200` | Full training loop. |
| LR milestones | `[60, 120, 160]` | `MultiStepLR` schedule. |
| LR decay gamma | `0.2` | `train.py` scheduler argument. |
| Regular save interval | `10` | Regular checkpoints every ten epochs. |
| Timestamp format | `%A_%d_%B_%Y_%Hh_%Mm_%Ss` | Run/checkpoint/log folder names. |
| CIFAR-100 mean | `(0.5070751592371323, 0.48654887331495095, 0.4409178433670343)` | Train and test normalization. |
| CIFAR-100 std | `(0.2673342858792401, 0.2564384629170883, 0.27615047132568404)` | Train and test normalization. |

## Safe environment check

Use the bundled root helper when you need a non-destructive probe:

```bash
python scripts/check_environment.py --repo-root <checkout> --net resnet18
```

The helper checks imports, optional CUDA availability, and a random 32x32 forward pass. It does not download CIFAR-100, train, evaluate, or write checkpoints.
