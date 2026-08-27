---
name: pytorch-unet
description: "Use Pytorch-UNet for semantic segmentation model APIs, data
  preparation, training, prediction, evaluation, checkpoints, CUDA/AMP, and
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# pytorch-unet

Use this repo skill for Pytorch-UNet, a PyTorch U-Net implementation for semantic segmentation workflows such as Carvana-style binary masks, custom image/mask datasets, training, prediction, and Dice evaluation.

## Quick install/import orientation

Pytorch-UNet is commonly used from a source checkout rather than an installed distribution. A typical environment needs PyTorch plus the repo's runtime dependencies:

```bash
pip install torch torchvision matplotlib==3.6.2 numpy==1.23.5 Pillow==9.3.0 tqdm==4.64.1 wandb==0.13.5
python -c "from unet import UNet; print(UNet(3, 2))"
```

Use a CUDA-capable PyTorch build when the user needs practical GPU training or AMP. CPU is enough for import checks, dataset validation, model-shape checks, and tiny synthetic prediction smoke tests.

## Route by task

| User task | Read |
| --- | --- |
| Construct a `UNet`, choose `n_channels`/`n_classes`/`bilinear`, load state dicts, use torch.hub `unet_carvana`, debug architecture checkpoint mismatches, or run a forward smoke check | [sub-skills/model-api/SKILL.md](sub-skills/model-api/SKILL.md) |
| Prepare `data/imgs` and `data/masks`, validate mask naming and dimensions, build training argument lists, handle W&B/checkpoints/CUDA/AMP, or debug data loader/training failures | [sub-skills/data-training/SKILL.md](sub-skills/data-training/SKILL.md) |
| Run prediction via bundled wrappers, convert class IDs to mask images, set prediction outputs, evaluate Dice, handle visualization/no-save, or debug prediction/evaluation failures | [sub-skills/prediction-evaluation/SKILL.md](sub-skills/prediction-evaluation/SKILL.md) |

## Shared references and checks

- [references/package-overview.md](references/package-overview.md) summarizes the repo's public surfaces, dependencies, backend assumptions, and safe route map.
- [references/troubleshooting.md](references/troubleshooting.md) covers cross-cutting import, dependency, CUDA, W&B, credentials, network, and route-choice failures.
- [references/repo-provenance.md](references/repo-provenance.md) records the source snapshot and evidence paths. Read it before deciding whether this skill is stale for a different checkout.
- [scripts/check_environment.py](scripts/check_environment.py) verifies imports and optional CUDA visibility. Use `--repo-root` when checking an unpackaged source checkout.

## Safe default workflow

1. Identify the user's goal and route to the relevant sub-skill.
2. Run only safe checks first: CLI `-h`, `scripts/check_environment.py`, the model smoke script, dataset validator, or prediction smoke script.
3. Do not run Kaggle data download, torch.hub pretrained downloads, Docker build/push, full Carvana training, W&B online logging, or large checkpoint inference unless the user explicitly approves the network, credentials, disk, and runtime cost.
4. Keep model shape, data labels, training flags, and prediction flags aligned: `n_channels`, `n_classes`/`--classes`, `bilinear`/`--bilinear`, `mask_values`, and scale all interact across workflows.

## Backend policy

- CPU verifies functional model/data/prediction behavior for small fixtures.
- CUDA is optional acceleration for training and AMP unless the user's task explicitly requires GPU performance evidence.
- If CUDA is required, verify a matching PyTorch CUDA build and a small CUDA tensor allocation before launching training or large prediction jobs.

## Non-goals

This skill does not provide Kaggle credentials, ship pretrained weights, replace the original U-Net paper, or certify a full Carvana benchmark run. It gives future agents self-contained operating guidance and bundled safe helpers for using the Pytorch-UNet codebase correctly.
