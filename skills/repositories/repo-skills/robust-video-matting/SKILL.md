---
name: robust-video-matting
description: "Use for RobustVideoMatting human video matting workflows:
  MattingNetwork APIs, inference conversion, training data setup, and RVM
  evaluation metrics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# RobustVideoMatting Repo Skill

Use this skill when a task involves Robust Video Matting (RVM), the repository
for robust human video matting with temporal guidance. RVM predicts foreground
RGB and alpha mattes from ordinary human videos, recycles recurrent states over
time, and provides source-checkout/TorchHub workflows for PyTorch inference,
training, and evaluation.

## First route the task

- Use [sub-skills/model-api](sub-skills/model-api/SKILL.md) for
  `MattingNetwork`, `mobilenetv3` vs `resnet50`, refiners, tensor shapes,
  recurrent states, `segmentation_pass`, or safe synthetic forward checks.
- Use [sub-skills/inference-workflows](sub-skills/inference-workflows/SKILL.md)
  for loading checkpoints or TorchHub models, calling `convert_video`, running
  image/video conversion, choosing output alpha/foreground/composition, or
  using TorchScript, ONNX, TensorFlow, TensorFlow.js, and CoreML artifacts.
- Use [sub-skills/training-data](sub-skills/training-data/SKILL.md) for
  VideoMatte240K, ImageMatte, background, COCO, SPD, or YouTubeVIS layouts;
  `DATA_PATHS`; augmentations/losses; and the official four-stage training
  commands.
- Use [sub-skills/evaluation-tools](sub-skills/evaluation-tools/SKILL.md) for
  LR/HR matting metrics, prediction/ground-truth directory structures,
  synthetic evaluation composite scripts, and speed benchmark caveats.

## Install and import orientation

This repository snapshot is not a normal pip-installable distribution. It has
no `setup.py` or `pyproject.toml`; local source workflows import modules such as
`model`, `inference`, `dataset`, and `evaluation` from a checkout root. TorchHub
is also supported for model and converter loading when network/cache behavior is
acceptable.

For source-checkout workflows, make the checkout importable and install the
needed dependencies for the chosen route:

```bash
# Historical repo requirement files exist for inference and training, but may
# need Python/PyTorch-version adjustment on modern systems.
pip install torch torchvision tqdm pillow
pip install av pims          # video file IO / converter video workflows
pip install opencv-python-headless xlsxwriter kornia  # evaluation workflows
pip install easing_functions tensorboard              # training workflows
```

Minimal source import and model smoke check:

```bash
python scripts/check_rvm_environment.py --repo-root /path/to/RobustVideoMatting --device cpu
```

The helper validates imports, signatures, and a tiny synthetic forward pass. It
is not a quality test, paper reproduction, GPU speed benchmark, or full
training check.

## Shared references and helpers

- Read [references/model-catalog.md](references/model-catalog.md) for model
  variants, artifact families, backend support, and speed caveats shared across
  workflows.
- Read [references/troubleshooting.md](references/troubleshooting.md) for
  source-layout, dependency, network, CUDA, and media IO failures before diving
  into a sub-skill-specific troubleshooting page.
- Read [references/repo-provenance.md](references/repo-provenance.md) before
  deciding whether this skill is current for a checkout or whether it needs a
  refresh.
- `references/repo-routing-metadata.json` contains structured router metadata
  for managed repo-skill import.
- Run [scripts/check_rvm_environment.py](scripts/check_rvm_environment.py) to
  check importability and a tiny model forward from arbitrary working
  directories.

## Key operating constraints

- Do not hide network downloads. TorchHub default pretrained models,
  `pretrained_backbone=True`, official weights, and datasets may download
  external artifacts.
- Do not use CPU smoke checks as evidence for CUDA speed, HR evaluation, or
  full training. CUDA is required for those claims.
- Do not run full training as a quick validation. `train.py` uses GPU count,
  multiprocessing, NCCL, DDP, SyncBatchNorm, AMP, and large datasets.
- Prefer PNG sequence conversion while debugging media/model behavior; video
  conversion adds PyAV/PIMS/codec issues.
- Preserve recurrent states for video matting. Independent per-frame calls are
  valid for image-like tests but discard RVM's temporal memory.

## Quick task patterns

- "Convert my frames to alpha PNGs": route to
  [inference-workflows](sub-skills/inference-workflows/SKILL.md) and use its
  bundled `rvm_convert_image_sequence.py` wrapper with a local checkpoint.
- "Why does my tensor call fail?": route to
  [model-api](sub-skills/model-api/SKILL.md), verify `[B,3,H,W]` or
  `[B,T,3,H,W]`, and run `rvm_model_smoke.py`.
- "Prepare custom data for training": route to
  [training-data](sub-skills/training-data/SKILL.md), validate `fgr`/`pha` and
  background roots, then adapt the stage commands.
- "Evaluate predicted alpha against ground truth": route to
  [evaluation-tools](sub-skills/evaluation-tools/SKILL.md), check exact
  dataset/clip/frame matching, then choose LR/tiny or HR/CUDA metrics.
