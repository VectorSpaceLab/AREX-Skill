---
name: simmim-workflows
description: "Use this repo skill for Swin-Transformer SimMIM masked image
  modeling pretraining, fine-tuning, evaluation, mask generation, checkpoint
  remapping, and safe synthetic smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# simmim-workflows

Use this sub-skill when a task involves SimMIM in the Swin-Transformer repository: masked image modeling pretraining, fine-tuning a SimMIM-pretrained checkpoint, evaluating a SimMIM fine-tuned model, mask generation, or checkpoint remapping.

## Covers

- `main_simmim_pt.py` pretraining command shape.
- `main_simmim_ft.py` fine-tuning/evaluation command shape.
- `MaskGenerator`, `SimMIMTransform`, `SimMIM`, and `build_simmim` behavior.
- SimMIM config pairs under `configs/simmim/`.
- Safe mask/loss CPU smoke checks.

## Routes elsewhere

- Baseline supervised `main.py` commands: `training-eval-cli`.
- Generic ImageNet layouts: `data-and-checkpoints`.
- Swin V1/V2 constructor details: `core-models`.
- MoE/Tutel/fused CUDA: `moe-and-acceleration`.

## Workflow

1. Decide if the task is pretraining, fine-tuning, or evaluation.
2. Read `references/simmim-workflows.md` for command shape and config pairing.
3. Read `references/api-reference.md` for mask/loss behavior.
4. Validate the proposed command with `scripts/validate_simmim_command.py`.
5. Run `scripts/smoke_simmim_loss.py` only for a tiny CPU synthetic check; it is not a training substitute.

## Linked files

- `references/simmim-workflows.md` - task recipes and config pair guidance.
- `references/api-reference.md` - mask and SimMIM model APIs.
- `references/troubleshooting.md` - common mask, checkpoint, and command mistakes.
- `scripts/validate_simmim_command.py` - safe command validator.
- `scripts/smoke_simmim_loss.py` - tiny synthetic CPU loss smoke.
