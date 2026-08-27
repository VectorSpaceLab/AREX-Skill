---
name: vision-workflows
description: "Routes AXLearn vision model configs, ImageNet inputs, and
  ResNet/CLIP-style recipes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# vision-workflows

Use this sub-skill for AXLearn's image-centric workflows.

Typical triggers:

- ImageNet, ResNet, ImageClassificationModel, or `ImagenetInput`.
- CLIP, CoCa, CyCLIP, or other vision-language model helpers.
- Image preprocessing, fake image datasets, crop/augment/whiten helpers, or vision trainer configs.

If the task is only about shared trainer plumbing, use `../training-core/` first.
If the task is about `axlearn gcp ...`, use `../cli-cloud/`.
If the task is about ASR, use `../audio-asr/`.

## What to read

- `references/workflows.md` for ImageNet and model-builder workflows.
- `references/troubleshooting.md` for fake-data, dataset, and shape issues.
- `scripts/inspect_vision_configs.py` for a safe config-inspection helper.

## Common routes

### Inspect a ResNet trainer catalog

```bash
python scripts/inspect_vision_configs.py --module axlearn.experiments.vision.resnet.imagenet_trainer --config ResNet-Test
```

### Run a CPU-safe fake-data probe

Use `DATA_DIR=FAKE` so the ImageNet helpers switch to synthetic inputs.

### Inspect the image-classification model API

The central model is `ImageClassificationModel`, which wraps a backbone plus classifier head.
The `ResNet` family provides backbone configs such as `resnet18_config()` and `resnet50_config()`.

## Decision points

- Choose this sub-skill when the user names a specific image-classification model or ImageNet recipe.
- Keep shared trainer mechanics in `training-core`.
- Do not route speech or GPT catalogs here just because they also use `SpmdTrainer`.
