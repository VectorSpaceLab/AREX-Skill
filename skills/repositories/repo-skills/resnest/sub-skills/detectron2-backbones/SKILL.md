---
name: detectron2-backbones
description: "Use optional Detectron2 ResNeSt/FPN backbones, config extension,
  COCO recipes, and safe train/eval command construction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Detectron2 ResNeSt Backbones

Use this sub-skill when a task involves ResNeSt inside Detectron2: optional backbone registration, FPN construction, COCO detection/instance/panoptic recipe selection, config merging, train/eval command construction, or Detectron2-specific failures.

Detectron2 is an optional dependency for ResNeSt. It was not installed in the minimum inspection environment used to build this skill, so runtime checks are conditional: first prove Detectron2 and its compiled operators are available in the user's environment, then merge configs or construct models.

## Route here for

- `resnest.d2.add_resnest_config(cfg)` and Detectron2 config extension.
- `build_resnest_backbone` or `build_resnest_fpn_backbone` in `MODEL.BACKBONE.NAME`.
- ResNeSt/FPN COCO recipes for Faster R-CNN, Cascade R-CNN, Mask R-CNN, Cascade Mask R-CNN, and Panoptic FPN.
- ResNeSt Detectron2 split-attention layers, including DCN variants.
- Safe construction of Detectron2 train/eval commands without running training.

## Route elsewhere

- Plain PyTorch classification models, Torch Hub loading, ImageNet inference, and PyTorch `SplAtConv2d` outside Detectron2 belong to `pytorch-models`.
- MXNet Gluon model zoo usage belongs to `gluon-models`.
- Generic Detectron2 tutorials that do not involve ResNeSt-specific registration, config fields, or ResNeSt COCO recipes are out of scope.

## First steps

1. Confirm optional Detectron2 availability with the bundled probe before training or evaluation:

   ```bash
   python scripts/detectron2_config_probe.py
   ```

   The probe is safe by default: it does not train, download weights, read source checkout configs, or require a config file.

2. If you have a self-contained Detectron2 config file, merge it without training:

   ```bash
   python scripts/detectron2_config_probe.py --config-file path/to/config.yaml --opts MODEL.BACKBONE.NAME build_resnest_fpn_backbone
   ```

3. In a training/evaluation launcher, import the ResNeSt Detectron2 package before model construction and call `add_resnest_config(cfg)` before merging config files or `KEY VALUE` overrides.

## References and bundled script

- Read [references/api-reference.md](references/api-reference.md) when wiring imports, backbone registry names, ResNeSt config fields, or the Detectron2 split-attention/DCN layers.
- Read [references/config-reference.md](references/config-reference.md) when choosing a COCO recipe, depth, SyncBN/DCN option, schedule, pixel format, or released external weight URL.
- Read [references/workflows.md](references/workflows.md) when constructing config-merge, training, eval-only, TTA, or COCO dataset setup commands.
- Read [references/troubleshooting.md](references/troubleshooting.md) when Detectron2 is missing, a backbone is unregistered, config fields fail to merge, SyncBN/DCN operators fail, COCO data are not registered, or released weights do not load.
- Run [scripts/detectron2_config_probe.py](scripts/detectron2_config_probe.py) to check optional Detectron2 availability and print the merged ResNeSt-related config fields without building a trainer or model.
