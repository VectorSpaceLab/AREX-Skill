# Model Zoo and Config Families

## When to read

Read this before choosing a Swin-Transformer config, checkpoint, or sub-skill route. It distills the public model-hub/config layout into a task-oriented map.

## Config families

| Family | Config directory | `MODEL.TYPE` | Typical use | Route |
| --- | --- | --- | --- | --- |
| Swin V1 | `configs/swin/` | `swin` | ImageNet-1K training/evaluation, ImageNet-22K pretraining/fine-tuning, 224/384 resolution variants | `sub-skills/core-models/`, `sub-skills/training-eval-cli/` |
| Swin V2 | `configs/swinv2/` | `swinv2` | Scaled-capacity/resolution variants with continuous relative position bias and pretrained-window-size handling | `sub-skills/core-models/`, `sub-skills/training-eval-cli/` |
| Swin-MLP | `configs/swinmlp/` | `swin_mlp` | Attention-free shifted-window MLP variants | `sub-skills/core-models/`, `sub-skills/training-eval-cli/` |
| Swin-MoE | `configs/swinmoe/` | `swin_moe` | Tutel-based mixture-of-experts training/evaluation, usually ImageNet-22K and multi-node GPU | `sub-skills/moe-and-acceleration/` |
| SimMIM | `configs/simmim/` | `swin` or `swinv2` plus SimMIM scripts | Masked image modeling pretraining and fine-tuning/evaluation | `sub-skills/simmim-workflows/` |

## Common naming patterns

- `swin_tiny_patch4_window7_224.yaml`: Swin V1, patch size 4, window 7, image size 224.
- `*_22k.yaml`: ImageNet-22K pretraining configuration.
- `*_22kto1k_finetune.yaml` or `*_ft.yaml`: fine-tune an ImageNet-22K pretrained checkpoint on ImageNet-1K.
- `window12_384` or `window16_256`: larger resolution/window-size fine-tuning.
- `simmim_pretrain__...` versus `simmim_finetune__...`: use different entry scripts and data assumptions.
- `swin_moe_*_8expert_32gpu_22k.yaml`: MoE expert count and intended distributed scale appear in the filename.

## Selection heuristics

1. If the task names an exact checkpoint/model from a model hub table, select the config linked by that model name.
2. If it asks for baseline ImageNet-1K supervised training, start with Swin-T/S/B under `configs/swin/` or SwinV2-T/S/B under `configs/swinv2/`.
3. If it asks for high-resolution fine-tuning, use a config whose filename changes both window and image size, then pass `--pretrained <lower-resolution-checkpoint>`.
4. If it asks for SimMIM, do not use `main.py`; route to the SimMIM scripts and configs.
5. If it asks for MoE, confirm Tutel/GPU/multi-node expectations before composing a command.

## Validation

Use `scripts/inspect_swin_config.py` to summarize a config. Use `sub-skills/core-models/scripts/smoke_model_build.py` for CPU construction sanity, but remember that CPU construction does not verify full GPU training, MoE, or fused CUDA behavior.
