# ResNeSt Model Overview

Use this reference before choosing a backend-specific sub-skill. It summarizes model names, published crop sizes, pretrained behavior, and downstream integration boundaries.

## What ResNeSt adds

ResNeSt is a split-attention ResNet variant. The canonical PyTorch and Gluon builders use a deep stem, average-down projection, average downsampling in bottlenecks, and split-attention (`radix=2`) by default. The Detectron2 integration reuses the same design ideas in an FPN backbone for COCO detection, instance segmentation, and panoptic segmentation recipes.

## Core classification models

| Model | PyTorch factory | Gluon factory | Published crop size | Published top-1: PyTorch / Gluon | Notes |
|---|---|---|---:|---|---|
| ResNeSt-50 | `resnest50` | `resnest50` | 224 | 81.03 / 81.04 | Default entry point for smoke tests and transfer learning. |
| ResNeSt-101 | `resnest101` | `resnest101` | 256 | 82.83 / 82.81 | Larger depth with stem width 64. |
| ResNeSt-200 | `resnest200` | `resnest200` | 320 | 83.84 / 83.88 | Heavyweight model; Gluon builder uses final dropout. |
| ResNeSt-269 | `resnest269` | `resnest269` | 416 | 84.54 / 84.53 | Largest canonical classifier; expensive for real validation. |

For tiny smoke tests, smaller random inputs such as 64x64 can validate tensor flow, but real pretrained accuracy checks should use the published crop sizes and ImageNet preprocessing.

## Fast ablation variants

| Factory name | Setting | PyTorch top-1 | Gluon top-1 | Notes |
|---|---|---:|---:|---|
| `resnest50_fast_1s1x64d` | radix 1, groups 1, width 64 | 80.33 | 80.35 | No split-attention branch; fast ablation. |
| `resnest50_fast_2s1x64d` | radix 2, groups 1, width 64 | 80.53 | 80.65 | Split-attention, one group. |
| `resnest50_fast_4s1x64d` | radix 4, groups 1, width 64 | 80.76 | 80.90 | More radix splits. |
| `resnest50_fast_1s2x40d` | radix 1, groups 2, width 40 | 80.59 | 80.72 | Cardinality ablation. |
| `resnest50_fast_2s2x40d` | radix 2, groups 2, width 40 | 80.61 | 80.84 | Split-attention plus two groups. |
| `resnest50_fast_4s2x40d` | radix 4, groups 2, width 40 | 81.14 | 81.17 | Best reported fast ablation in the table. |
| `resnest50_fast_1s4x24d` | radix 1, groups 4, width 24 | 80.99 | 80.97 | Higher cardinality without radix split. |

Fast variants are direct PyTorch/Gluon exports. In the PyTorch training registry, the fast ablation factories are not config registry names, so call them directly unless you add your own registry entry.

## Backend selection

| Need | Best route | Notes |
|---|---|---|
| Ordinary Python package inference, Torch Hub, model modification, Split-Attention inspection | `pytorch-models` | Required/verified core path; start with `pretrained=False`. |
| Legacy Gluon model zoo, `.params` files, Gluon RecordIO throughput comparison | `gluon-models` | Optional; requires MXNet and possibly GluonCV/Horovod. |
| COCO detection, instance segmentation, panoptic segmentation with ResNeSt/FPN | `detectron2-backbones` | Optional; requires Detectron2 and realistic data/hardware for train/eval. |
| Published ImageNet or COCO metric reproduction | Backend-specific workflow references | Needs pretrained weights, correct crop/input format, full dataset, and sufficient compute; tiny smoke checks do not reproduce metrics. |

## Pretrained weight behavior

- PyTorch factories with `pretrained=True` use `torch.hub.load_state_dict_from_url(..., check_hash=True)` and the PyTorch Hub cache.
- Gluon factories with `pretrained=True` use a `.params` cache root and SHA-1 verification.
- Detectron2 configs use external `MODEL.WEIGHTS` URLs for backbone initialization or full task checkpoints.
- Keep the classifier/task shape aligned with the checkpoint. ImageNet classifiers use 1000 output classes; COCO checkpoints require the matching Detectron2 recipe family.
- If network access or cache state is uncertain, first run no-pretrained smoke checks.

## Transfer-learning notes

- For PyTorch classification transfer, construct a model with `pretrained=False` for offline work or with `pretrained=True` only when ImageNet-1000 weights are acceptable, then replace or fine-tune the classifier head as appropriate.
- For Gluon transfer, initialize manually when `pretrained=False`; do not call `initialize()` after loading pretrained parameters unless you intentionally reinitialize.
- For Detectron2 transfer, begin with the config/backbone fields and weights matching the target task. Changing SyncBN, DCN, input format, pixel statistics, batch size, or dataset registration changes behavior relative to released metrics.
