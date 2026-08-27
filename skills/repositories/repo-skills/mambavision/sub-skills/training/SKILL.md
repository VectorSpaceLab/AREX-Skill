---
name: training
description: "Route MambaVision ImageNet training and fine-tuning workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Training

Use this sub-skill for MambaVision ImageNet training and fine-tuning command planning.

It covers:
- choosing among the bundled YAML presets for `mamba_vision_T`, `mamba_vision_T2`, `mamba_vision_S`, `mamba_vision_B`, `mamba_vision_L`, and `mamba_vision_L2`
- adapting the published `torchrun` launch pattern into safe command recipes with user-supplied paths
- `train.py` flags for data roots, split names, model choice, input size, batch size, AMP, EMA, MESA, checkpoints, logging, and output locations
- ImageFolder and LMDB-style data layouts
- distributed vs single-GPU debugging and failure triage
- validation that runs inside the training loop

Use this sub-skill only for training and fine-tuning. Route other tasks elsewhere:
- classification API, inference, feature extraction, or standalone validation -> `../classification/SKILL.md`
- OpenMMLab detection training -> `../object-detection/SKILL.md`
- OpenMMLab segmentation training -> `../semantic-segmentation/SKILL.md`

Start with the bundled references and helper:
- `references/training-workflows.md` for launch recipes and flag choices.
- `references/configuration.md` for YAML preset differences.
- `references/data-formats.md` for ImageNet/ImageFolder/LMDB layout checks.
- `references/troubleshooting.md` for OOM, DDP, data, checkpoint, and numerical failures.
- `scripts/print_training_command.py` to print a safe command template without launching training.

This skill is a router and reference hub. It does not bundle or launch the full training entry point because full ImageNet training is long-running and target-project specific.
