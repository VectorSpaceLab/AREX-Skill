---
name: resnest
description: "Use ResNeSt split-attention CNN models across PyTorch, optional
  MXNet Gluon, and optional Detectron2 backbones with safe install checks, model
  routing, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ResNeSt Repo Skill

Use this skill when a task names ResNeSt or asks for split-attention ResNet-style CNNs, PyTorch classification factories, Torch Hub loading, optional MXNet Gluon models, or optional Detectron2 ResNeSt/FPN backbones.

ResNeSt is a Python package centered on ImageNet classification backbones and downstream detection/segmentation integration. The safest verified core path is PyTorch model construction with `pretrained=False`; pretrained weights, ImageNet/COCO metrics, MXNet Gluon, Horovod, and Detectron2 are optional/heavyweight surfaces that need the user's environment and data.

## Start with an install/import check

For ordinary package use:

```bash
pip install resnest --pre
python - <<'PY'
from resnest.torch import resnest50
model = resnest50(pretrained=False)
print(model.__class__.__name__)
PY
```

For a fuller offline-first package probe, run the bundled root helper:

```bash
python scripts/check_resnest_install.py --model resnest50 --image-size 64
```

The helper does not download weights or train models by default. It reports optional Gluon and Detectron2 availability without making those backends required.

## Route by workflow

| User intent | Read next | Why |
|---|---|---|
| Load ResNeSt in PyTorch, use Torch Hub, run a no-pretrained inference smoke, inspect `SplAtConv2d`, or interpret PyTorch ImageNet training configs | [sub-skills/pytorch-models/SKILL.md](sub-skills/pytorch-models/SKILL.md) | This is the verified core surface and owns PyTorch APIs, model names, training config notes, and PyTorch troubleshooting. |
| Use MXNet Gluon builders, `get_model`, Gluon pretrained `.params` cache behavior, raw/RecordIO ImageNet validation, or Horovod Gluon training notes | [sub-skills/gluon-models/SKILL.md](sub-skills/gluon-models/SKILL.md) | Gluon is optional and needs a compatible MXNet stack; the sub-skill keeps optional-backend guidance separate from PyTorch. |
| Register ResNeSt inside Detectron2, choose COCO Faster/Mask/Cascade/Panoptic configs, validate `build_resnest_fpn_backbone`, or debug SyncBN/DCN/COCO issues | [sub-skills/detectron2-backbones/SKILL.md](sub-skills/detectron2-backbones/SKILL.md) | Detectron2 is optional and heavy; this sub-skill owns config extension, backbone builders, COCO recipe catalog, and safe config probes. |
| Decide which model/depth/backend is appropriate before entering a backend-specific route | [references/model-overview.md](references/model-overview.md) | Shared catalog of core and fast model variants, published crop sizes, and backend/pretrained notes. |
| Fix import, optional dependency, pretrained download/cache, dataset, or backend setup failures | [references/troubleshooting.md](references/troubleshooting.md) | Cross-cutting failure map before using a backend-specific troubleshooting reference. |
| Check whether this skill matches the current repository revision | [references/repo-provenance.md](references/repo-provenance.md) | Source commit, package version, evidence paths, and refresh guidance. |

## Core model names

Core classification factories: `resnest50`, `resnest101`, `resnest200`, `resnest269`.

Fast ablation factories: `resnest50_fast_1s1x64d`, `resnest50_fast_2s1x64d`, `resnest50_fast_4s1x64d`, `resnest50_fast_1s2x40d`, `resnest50_fast_2s2x40d`, `resnest50_fast_4s2x40d`, `resnest50_fast_1s4x24d`.

All public PyTorch and Gluon factories accept the pattern `pretrained=False` plus backend-specific `root`/`ctx` and `**kwargs`. Keep `pretrained=False` for offline or smoke-test work. Use `pretrained=True` only when network/cache behavior and ImageNet-1000 classifier shape are acceptable.

## Backend boundaries

- PyTorch classification is the required core path. CPU fully validates package import, factory construction, and tiny tensor forwards.
- CUDA is useful for real training and throughput, but it is not required for the core package smoke unless the user explicitly asks for GPU behavior.
- Gluon/MXNet is optional. Do not install or claim Gluon runtime support until a compatible MXNet wheel imports in the user's environment.
- Detectron2 is optional. Config probing is lightweight; real train/eval needs a Detectron2 build compatible with PyTorch/CUDA, COCO data, and often SyncBN/DCN operators.
- ImageNet and COCO preparation are large-data workflows. Do not run dataset download/extraction or full validation/training as a default check.

## Safe operating pattern

1. Run the root helper or PyTorch tiny inference helper with `pretrained=False`.
2. Use the model overview to choose depth, crop size, and backend.
3. Enter the backend-specific sub-skill for concrete APIs, commands, config fields, and troubleshooting.
4. Escalate to pretrained downloads, ImageNet/COCO validation, CUDA, Horovod, or Detectron2 training only after the user confirms data, hardware, runtime, and time budget.

## What this skill deliberately avoids

- It does not bundle full ImageNet or COCO download/extraction launchers.
- It does not make optional Gluon or Detectron2 dependencies part of the minimum install path.
- It does not claim reproduced paper or benchmark metrics from tiny smoke checks.
- It does not require the original ResNeSt repository checkout at runtime; references and scripts here are distilled or adapted for the skill tree.
