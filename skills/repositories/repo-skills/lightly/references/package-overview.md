# LightlySSL Package Overview

## What LightlySSL provides

LightlySSL (`lightly`) is a PyTorch-based self-supervised learning package for computer vision. It provides:

- Low-level SSL building blocks: datasets, collate functions, augmentations, losses, projection/prediction heads, memory banks, and utility modules.
- Example-backed training patterns for many SSL methods, including SimCLR, MoCo, BYOL, DINO, DINOv2, SwaV, VICReg, Barlow Twins, MAE, iBOT, MSN, PMSN, FroSSL, AIM, CAPI, LeJEPA, Pixio, and related methods.
- CLI entry points for training, embedding, combined train+embed, cropping images by YOLO-style labels, and version checks.
- Embedding/evaluation helpers, including KNN/linear classifier utilities and PyTorch Lightning callbacks.
- Repository maintenance workflows for formatting, static checks, tests, docs, generated notebooks, and distributed test selection.

## Public modules and commands

| Surface | Main entry points | Route |
|---|---|---|
| Package import | `lightly`, `lightly.data`, `lightly.transforms`, `lightly.loss`, `lightly.models.modules` | `ssl-building-blocks` |
| CLI | `lightly-version`, `lightly-ssl-train`, `lightly-embed`, `lightly-magic`, `lightly-crop` | `cli-data-embedding` |
| Training recipes | PyTorch modules, Lightning modules, distributed variants | `training-workflows` |
| Evaluation | `BenchmarkModule`, `KNNClassifier`, `LinearClassifier`, `OnlineLinearClassifier`, `knn_predict` | `evaluation-maintenance` |
| Maintenance | `make format`, `make static-checks`, `make test-fast`, `make generate-example-notebooks` | `evaluation-maintenance` |

## Dependency boundaries

- Base package requires PyTorch, Torchvision, PyTorch Lightning, Hydra, NumPy, and tqdm.
- `lightly[timm]` is needed for TIMM-backed ViT/MAE/IJEPA/CAPI/Pixio-style modules.
- `lightly[video]` is needed for direct video-file datasets through PyAV.
- Dev, docs, notebook, and full test dependencies are separate from normal package use.
- Python 3.13 is not a good default for LightlySSL workflows because PyTorch compatibility can lag; prefer a Python version supported by the installed PyTorch wheel.

## Workflow boundaries

- Use API building blocks when writing or debugging custom models/losses/transforms.
- Use training workflows when adapting method examples to local data or Lightning/distributed execution.
- Use CLI/data guidance when constructing commands, validating folders, or dealing with embeddings/crops.
- Use evaluation/maintenance guidance when validating repository edits or running KNN/linear benchmark utilities.
