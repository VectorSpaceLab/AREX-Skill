---
name: imagenet-training
description: "Routes Flag-DiT, Next-DiT, and Next-DiT-MoE ImageNet training and
  sampling tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ImageNet Training

Use this subskill for the benchmark branches that train or sample on ImageNet.
It covers the Flag-DiT, Next-DiT, and Next-DiT-MoE directories, including the single-node and Slurm launch scripts.

## Include here

- ImageNet folder-layout preparation.
- Flag-DiT, Next-DiT, and Next-DiT-MoE training launches.
- Sampling / evaluation routes in the Next-DiT benchmark branches.
- Stage script editing for the local ImageNet root.
- Distributed launcher selection (`torchrun`, `srun`, Slurm wrappers).

## Exclude or route elsewhere

- Lumina text-to-image training: use `image-training`.
- Inference or checkpoint conversion for the Lumina image models: use `image-generation`.
- Audio/music demos: use `audio-music`.
- Visual anagrams: use `visual-anagrams`.

## Read first

- `references/workflows.md` for the benchmark launch patterns.
- `references/data-layout.md` for the ImageNet directory shape and `train_data_root` editing.
- `references/troubleshooting.md` for GPU-count, FlashAttention, and checkpoint issues.
- `scripts/check_imagenet_layout.py` before a long run if the dataset layout is uncertain.

## Fast routing hints

- If the user says `ImageNet`, `FSDP`, `run_8gpus.sh`, `slurm`, or `class_labels`, use this subskill.
