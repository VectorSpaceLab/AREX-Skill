# Model and Demo Catalog

## Purpose

Use this catalog to decide which example family matches the user's task and which examples should stay reference-only.

## Classification and PointNet Families

| Example | Main workflow | Prerequisites | Notes |
|---|---|---|---|
| `examples/classification_modelnet40.py` | ModelNet40 classification | dataset download, sklearn, training data | Good reference for sparse classification heads and point-cloud voxelization. |
| `examples/pointnet.py` | PointNet / MinkowskiPointNet | dataset download, point-cloud loaders | Useful for comparing sparse and dense collate patterns. |
| `examples/resnet.py` | Residual sparse classification backbones | model/data setup | Good reference for deeper sparse classification blocks. |
| `examples/minkunet.py` and `examples/unet.py` | Sparse U-Net style classification/segmentation backbones | model/data setup | Reference-only by default because they are longer model definitions. |
| `examples/stack_unet.py` | Stacked sparse U-Net variant | model/data setup | Reference for stacked sparse blocks and reuse of layer families. |

## Segmentation and Indoor Demo

| Example | Main workflow | Prerequisites | Notes |
|---|---|---|---|
| `examples/indoor.py` | ScanNet-style semantic segmentation | Open3D, pretrained weights, visualization | Useful for TensorField + sparse slicing + colorized output patterns. |

## Reconstruction, Completion, and VAE

| Example | Main workflow | Prerequisites | Notes |
|---|---|---|---|
| `examples/reconstruction.py` | sparse reconstruction / pruning | dataset, pretrained weights, visualization | Reference pattern for conv-transpose + pruning loops. |
| `examples/completion.py` | completion network | dataset, heavy demo logic | Reference-only by default. |
| `examples/vae.py` | sparse VAE-style workflow | dataset, training and visualization | Reference-only by default. |

## Multi-GPU

| Example | Main workflow | Prerequisites | Notes |
|---|---|---|---|
| `examples/multigpu.py` | multi-GPU training | CUDA build, multiple GPUs | Reference-only unless the environment is explicitly CUDA-capable. |
| `examples/multigpu_ddp.py` | DistributedDataParallel | CUDA build, multiple GPUs | Good reference for pure DDP launch logic. |
| `examples/multigpu_lightning.py` | PyTorch Lightning multi-GPU training | CUDA build, Lightning, multiple GPUs | Good reference for Lightning data/module structure. |

## Data and Download Helpers

| Example | Main workflow | Prerequisites | Notes |
|---|---|---|---|
| `examples/training.py` | generic training loop | dataset construction | Best reference for the core loop and cache-clearing pattern. |
| `examples/download_modelnet40.sh` | ModelNet40 download | network access | Reference-only because it downloads external data. |
| `examples/common.py` | seeding, timers, sampler helpers | none | Safe to distill into reusable recipes. |

## What the Catalog Means

- Use the classification and segmentation examples as route anchors when the user asks for sparse-vision modeling tasks.
- Keep download, visualization, and long training workflows reference-only unless the user explicitly asks to run them.
- Use the synthetic smoke helper before touching a real dataset or pretrained checkpoint.
