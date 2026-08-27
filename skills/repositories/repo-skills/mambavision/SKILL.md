---
name: "mambavision"
description: "Routes MambaVision users to classification, ImageNet training, and
  OpenMMLab backbone-adaptation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MambaVision repo skill

Use this skill when a request involves the MambaVision repository, the `mambavision` package, published ImageNet checkpoints, ImageNet training or fine-tuning, or the bundled MMDetection and MMSegmentation adapters.

MambaVision is a hybrid Mamba/Transformer vision backbone. This root skill routes you to the smallest sub-skill that matches the task and points you at the shared environment and provenance notes needed before you start.

## First checks

1. Read `references/repo-provenance.md` when you need to know whether this skill matches the current checkout.
2. Run `scripts/check_mambavision_env.py --help` to inspect the environment-check helper surface.
3. Use `scripts/check_mambavision_env.py --smoke` for a no-download import and forward check after installing the base package.
4. Read `references/installation.md` before asking for package installs, wheel selection, or rebuild steps.
5. Read `references/troubleshooting.md` when imports, checkpoint loading, registry wiring, or backend support fails.

## Install and verify

The verified package version for this generated skill is `mambavision==1.2.0`. The base package needs `torch`, `timm`, `transformers`, `mamba-ssm`, `einops`, `requests`, `Pillow`, and `tensorboardX`. Downstream object-detection and semantic-segmentation workflows additionally need the matching OpenMMLab stack. See `references/installation.md` for the exact package sets and smoke commands.

## Route map

### `classification`
Use this sub-skill for image classification, factory selection, no-download inference smoke tests, pretrained checkpoint handling, ImageNet validation planning, and safe throughput benchmarking.

Read:
- `sub-skills/classification/SKILL.md`
- `sub-skills/classification/references/api-reference.md`
- `sub-skills/classification/references/model-overview.md`
- `sub-skills/classification/references/validation-workflows.md`
- `sub-skills/classification/references/troubleshooting.md`

Typical tasks:
- choose a backbone factory or checkpoint family
- build an inference smoke command
- validate a local checkpoint against an ImageFolder tree
- compare safe throughput options

### `training`
Use this sub-skill for ImageNet training and fine-tuning, YAML preset selection, distributed launch planning, EMA/MESA flags, checkpoint resume, and data-layout checks.

Read:
- `sub-skills/training/SKILL.md`
- `sub-skills/training/references/training-workflows.md`
- `sub-skills/training/references/configuration.md`
- `sub-skills/training/references/data-formats.md`
- `sub-skills/training/references/troubleshooting.md`

Typical tasks:
- adapt `torchrun` or single-GPU launch templates
- choose the right preset and model family
- debug OOM, resume, and validation-loop behavior

### `object-detection`
Use this sub-skill for the published COCO Cascade Mask R-CNN workflows that attach MambaVision as an MMDetection backbone.

Read:
- `sub-skills/object-detection/SKILL.md`
- `sub-skills/object-detection/references/configuration.md`
- `sub-skills/object-detection/references/backbone-adapter.md`
- `sub-skills/object-detection/references/workflows.md`
- `sub-skills/object-detection/references/troubleshooting.md`

Typical tasks:
- adapt backbone and detector checkpoints
- print safe single-GPU train/test commands
- debug `MM_mamba_vision`, COCO layout, and metric selection

### `semantic-segmentation`
Use this sub-skill for the published ADE20K UPerNet workflows that attach MambaVision as an MMSegmentation backbone.

Read:
- `sub-skills/semantic-segmentation/SKILL.md`
- `sub-skills/semantic-segmentation/references/configuration.md`
- `sub-skills/semantic-segmentation/references/backbone-adapter.md`
- `sub-skills/semantic-segmentation/references/workflows.md`
- `sub-skills/semantic-segmentation/references/troubleshooting.md`

Typical tasks:
- choose the tiny, small, base, or L3 recipe
- print safe train/test command templates
- debug `MM_mamba_vision`, ADE20K layout, crop size, and AMP behavior

## Shared helpers

- `scripts/check_mambavision_env.py` checks import readiness, optional OpenMMLab imports, and an opt-in no-download forward smoke.
- `references/repo-routing-metadata.json` is the structured scenario map used by the router.
- `references/repo-provenance.md` captures the repo snapshot and construction baseline.

## Operating boundaries

- Do not start long training jobs, dataset conversions, or checkpoint downloads unless the user explicitly asks for execution and accepts the cost.
- Treat the bundled command helpers as templates; they do not launch anything.
- Keep runtime links inside this skill tree. If a task needs a deeper workflow, route to the matching sub-skill instead of reopening the source checkout.
