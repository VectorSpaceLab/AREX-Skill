# UNet++ stack overview

This repository contains two separate user-facing stacks.

| Stack | Directory | Main use | Typical environment |
| --- | --- | --- | --- |
| PyTorch nnU-Net | `pytorch/` | 3D medical image segmentation, training, inference, preprocessing, ensembling, pretrained-model management | Modern PyTorch + CUDA-capable environment |
| Keras segmentation_models | `keras/` | 2D segmentation model construction, backbone selection, and the BRATS2013 application workflow | Legacy TensorFlow 1.x + Keras 2.2.2 environment |

## Quick chooser

- Choose nnU-Net when the user talks about `nnUNet_train`, `nnUNet_predict`,
  `TaskXXX` datasets, preprocessing, inference folders, `RESULTS_FOLDER`, or
  pretrained nnU-Net model management.
- Choose Keras when the user talks about `Unet`, `Nestnet`, `Xnet`, `FPN`,
  `PSPNet`, `segmentation_models`, backbones, or BRATS2013.

## Why the split matters

The inspected snapshot showed that the two stacks need different runtimes:

- nnU-Net works with a modern PyTorch/CUDA environment.
- The Keras stack is pinned to a legacy TensorFlow 1.4.1 / Keras 2.2.2 world.

Future agents should treat those as separate operational routes rather than one
combined install target.

## What to read next

- [`../sub-skills/nnunet/SKILL.md`](../sub-skills/nnunet/SKILL.md) for the
  PyTorch route.
- [`../sub-skills/keras/SKILL.md`](../sub-skills/keras/SKILL.md) for the Keras
  route.
- [`troubleshooting.md`](troubleshooting.md) for cross-cutting problems.
