---
name: model-api
description: "Use Pytorch-UNet model architecture and checkpoint APIs for binary
  or multiclass semantic segmentation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# model-api

Use this sub-skill when the task is about constructing, loading, checking, or adapting the Pytorch-UNet model API itself.

## Route here for

- Creating `UNet(n_channels, n_classes, bilinear=False)` for binary or multiclass semantic segmentation.
- Explaining the encoder/decoder blocks: `DoubleConv`, `Down`, `Up`, and `OutConv`.
- Choosing input channels, output classes, bilinear upsampling, or transposed-convolution upsampling.
- Loading raw checkpoint `state_dict` files, including checkpoints that carry a non-parameter `mask_values` entry.
- Using `torch.hub` `unet_carvana` weights with the supported pretrained scale choices and network-download caution.
- Running a safe CPU or optional CUDA forward-pass smoke check before training, prediction, or evaluation work.

## Do not use this sub-skill for

- Dataset directory layout, mask scanning, transforms, train/validation splitting, or the training CLI; route to `data-training`.
- Prediction image I/O, mask image conversion workflows, CLI output naming, or evaluation dataloaders and Dice reporting; route to `prediction-evaluation`.
- Downloading Kaggle/Carvana data or executing credentialed/network data scripts.

## Read next

- [references/api-reference.md](references/api-reference.md) for the distilled model API, architecture blocks, tensor contracts, and checkpoint conventions.
- [references/workflows.md](references/workflows.md) for common construction, checkpoint loading, torch.hub, and smoke-check workflows.
- [references/troubleshooting.md](references/troubleshooting.md) for channel/class mismatches, checkpoint loading failures, CUDA/AMP issues, and torch.hub download failures.

## Bundled safe check

Run the bundled script [scripts/model_smoke.py](scripts/model_smoke.py) from an environment where the Pytorch-UNet package or checkout is importable. It imports `UNet`, creates a tiny tensor, validates the output shape, and prints JSON. CPU is sufficient for functional checks; CUDA and AMP are optional accelerators.
