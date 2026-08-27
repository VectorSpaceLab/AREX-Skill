---
name: minivit
description: "Routes MiniViT Mini-DeiT and Mini-Swin compression, distillation,
  command-construction, dataset-layout, and optional RPE/custom-op workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MiniViT

Use this sub-skill when the user asks about **MiniViT** workflows for Mini-DeiT or Mini-Swin: model/variant selection, ImageNet layout validation, MiniViT weight multiplexing, distillation command construction, evaluation command construction, 224-to-384 Mini-Swin finetuning, or optional RPE/custom-op status.

## Route first

| User task | Read/run |
| --- | --- |
| Build a Mini-DeiT or Mini-Swin command template | [`scripts/build_minivit_command.py`](scripts/build_minivit_command.py), then [`references/command-reference.md`](references/command-reference.md) |
| Choose a model variant, YAML config, or checkpoint family | [`references/api-reference.md`](references/api-reference.md) and [`references/command-reference.md`](references/command-reference.md) |
| Validate ImageNet folders or tar archives | [`references/workflows.md`](references/workflows.md) and root [`scripts/check_dataset_layout.py`](../../scripts/check_dataset_layout.py) |
| Diagnose teacher checkpoints, `rpe_ops`, Mini-Swin configs, Apex, or layer-list mismatches | [`references/troubleshooting.md`](references/troubleshooting.md) |

## Safe operating pattern

1. Confirm whether the user means **Mini-DeiT** or **Mini-Swin**. Generic iRPE integration belongs to the `irpe` sub-skill; TinyViT and EfficientViT belong to their own sub-skills.
2. Validate the ImageNet root before constructing expensive launchers:

   ```bash
   python ../../scripts/check_dataset_layout.py --root /path/to/ImageNet --kind imagenet1k
   ```

3. Generate, review, and edit a command template instead of improvising distributed flags:

   ```bash
   python scripts/build_minivit_command.py --workflow mini-swin-train --variant tiny --data-path /path/to/ImageNet --output /path/to/output --teacher /path/to/teacher.pth --amp-opt-level O0
   ```

4. Treat printed commands as templates. The helper never starts distributed training, downloads data, or writes checkpoints; commands printed by the helper may do those things if the user later runs them.

## Native safe checks

- Mini-DeiT parser help is safe in an environment with `timm` installed.
- `mini_deit_tiny_patch16_224` CPU instantiation is safe and was verified in the inspection environment.
- Mini-Swin config parsing with an explicit `--cfg` is safe; full Mini-Swin training/evaluation requires CUDA, DistributedDataParallel, and NCCL setup.

## Boundaries

- Covered here: Mini-DeiT and Mini-Swin compression/distillation/evaluation command construction and troubleshooting.
- Not covered here: generic iRPE API integration, TinyViT sparse-logit workflows, EfficientViT classification/downstream workflows, or Cream/AutoFormer NAS search.
- Keep runtime guidance self-contained: use bundled references/helpers rather than source-repo documentation links.
