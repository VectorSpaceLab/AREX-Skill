# FastReID model zoo and recipe selection

## What this reference is for

Use this reference to choose a FastReID recipe/config pair before you train,
evaluate, or inspect a config merge.
It does not reproduce benchmark results. It explains how to select the right
config family and what each family implies.

## Recipe families

| Family | Base file | Distilled behavior | Typical config files |
| --- | --- | --- | --- |
| BoT / bagtricks | `Base-bagtricks.yml` | Standard baseline with ResNet backbones, BNNeck, triplet + cross-entropy, and common training augmentation. | `Market1501/bagtricks_R50.yml`, `DukeMTMC/bagtricks_R50.yml`, `MSMT17/bagtricks_R50-ibn.yml`, `VehicleID/bagtricks_R50-ibn.yml`, `VERIWild/bagtricks_R50-ibn.yml` |
| AGW | `Base-AGW.yml` | Adds the AGW family of settings, including non-local and GeM-style choices, with softer classification settings. | `Market1501/AGW_R50.yml`, `DukeMTMC/AGW_R101-ibn.yml`, `MSMT17/AGW_S50.yml` |
| SBS | `Base-SBS.yml` | Stronger baseline with CircleSoftmax, GeM-P pooling, AMP enabled, longer crops, and more aggressive augmentation. | `Market1501/sbs_R50.yml`, `DukeMTMC/sbs_R101-ibn.yml`, `MSMT17/sbs_R50-ibn.yml`, `VeRi/sbs_R50-ibn.yml` |
| MGN | `Base-MGN.yml` | Multi-granularity architecture with frozen branches and a smaller embedding head. | `DukeMTMC/mgn_R50-ibn.yml`, `MSMT17/mgn_R50-ibn.yml` |
| ViT variant | inline recipe | Vision Transformer backbone with custom normalization and explicit pretrained weight path. | `Market1501/bagtricks_vit.yml` |

## Dataset families and selection hints

The recipe directories group configs by benchmark family.
Choose the directory first, then the recipe family.

- `Market1501/` — general person re-identification baseline configs.
- `DukeMTMC/` — DukeMTMC-ReID recipe variants.
- `MSMT17/` — the larger MSMT17 benchmark family.
- `VeRi/` — vehicle re-identification recipe.
- `VehicleID/` — vehicle identity benchmark configs.
- `VERIWild/` — VERI-Wild vehicle benchmark configs.

## How to choose a config

1. Pick the benchmark family that matches your task.
2. Pick the recipe family that matches the behavior you want:
   - BoT/bagtricks for the common baseline
   - AGW for AGW-style settings
   - SBS for the stronger baseline
   - MGN for multi-branch modeling
   - ViT when you need the ViT backbone variant
3. Inspect the `_BASE_` chain to see which solver, input, head, and loss values
   are inherited.
4. Override only the final values that should differ for your run, such as
   `MODEL.DEVICE`, `MODEL.WEIGHTS`, `OUTPUT_DIR`, or a local pretrained path.
5. Use the config merge checker to confirm the merged result before you run a
   more expensive workflow.

## What to notice in the merged recipe

The recipe family usually changes several of these groups at once:

- `MODEL.BACKBONE.*`
- `MODEL.HEADS.*`
- `MODEL.LOSSES.*`
- `INPUT.*`
- `DATALOADER.*`
- `SOLVER.*`
- `TEST.*`

Examples:

- BoT recipes usually keep `GlobalAvgPool`, `BNNeck`, and a ResNet-style
  backbone.
- AGW recipes typically add non-local behavior and GeM-style pooling.
- SBS recipes often use `GeneralizedMeanPoolingP`, CircleSoftmax, AMP, and a
  larger crop size.
- MGN recipes change the meta-architecture itself, not just the head or solver.
- The ViT variant uses a different backbone and normalization scheme from the
  ResNet recipes.

## Model zoo notes

The benchmark tables that informed these recipes are reference points, not a
guarantee that a local run will reproduce the exact numbers.
They were reported on a different hardware/software stack and often assume
pretrained backbones or downloaded weights.

For offline or CPU-only setup checks, treat the recipe as a configuration
specification and keep any weight references local.

## Practical selection examples

- `configs/Market1501/bagtricks_R50.yml` — simplest person-reID baseline to
  inspect.
- `configs/DukeMTMC/AGW_R50-ibn.yml` — AGW family with IBN backbone.
- `configs/MSMT17/sbs_R101-ibn.yml` — stronger baseline on a larger benchmark.
- `configs/VeRi/sbs_R50-ibn.yml` — vehicle re-ID recipe.
- `configs/VehicleID/bagtricks_R50-ibn.yml` — vehicle identity family config.
- `configs/VERIWild/bagtricks_R50-ibn.yml` — VERI-Wild family config.

## Weight and pretrain selection

- If the recipe expects pretrained backbone behavior, check whether it relies on
  automatic downloads or a local pretrained path.
- If the machine is offline, place the needed files in a local cache or point
  the config at an explicit path.
- If you only need to validate the config structure, disable the weight-dependent
  behavior and inspect the merge result instead of launching a run.
