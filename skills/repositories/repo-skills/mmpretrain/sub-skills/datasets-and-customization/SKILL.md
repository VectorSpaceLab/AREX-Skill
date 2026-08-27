---
name: datasets-and-customization
description: "Route dataset layouts, annotation validation, pipeline design, and
  registry-based customization for MMPretrain."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Datasets and Customization

Use this sub-skill for dataset layout decisions, annotation validation, pipeline construction, and registry-based extension of datasets, transforms, models, heads, losses, metrics, hooks, and optimizers.

## Route elsewhere when needed

- Training, testing, resume, or config execution details -> `../training-and-evaluation/SKILL.md`
- Inference, checkpoint choice, or model browsing -> `../model-zoo-inference/SKILL.md`
- Log/result analysis, visualization, FLOPs, CAM, t-SNE, publishing, or deployment utilities -> `../tools-analysis-and-deployment/SKILL.md`

## What to do first

1. Read `references/data-formats.md` to choose the right dataset layout and annotation shape.
2. Read `references/registry-customization.md` to register or expose a custom class.
3. Read `references/troubleshooting.md` when labels, paths, registries, or transforms do not line up.
4. Run `scripts/inspect_dataset_config.py` to inspect a config tree without building datasets or reading image files.

## What this sub-skill covers

- `CustomDataset`, `BaseDataset`, `ImageNet`, `KFoldDataset`, and dataset wrappers.
- OpenMMLab 2.0 annotation files with `metainfo` and `data_list`.
- Common image pipelines with `LoadImageFromFile`, `RandomResizedCrop`, `ResizeEdge`, `CenterCrop`, `RandAugment`, and `PackInputs`.
- Registry registration for `DATASETS`, `TRANSFORMS`, `MODELS`, `METRICS`, `HOOKS`, and `OPTIMIZERS`.
- Custom dataset/model/metric patterns and project-module import rules.

## Quick rule

If your samples only store `img_path`, the pipeline must load the image before augmentation. For classification-style pipelines, end with `PackInputs`.
