---
name: data-configuration
description: "Configure MMSegmentation configs, datasets, transforms, class
  palettes, and safe dataset layout checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data Configuration

Use this sub-skill when an MMSegmentation task is about experiment config files, MMEngine config inspection, dataset layout preparation, dataset classes, transform pipelines, class metadata, palettes, or dataset conversion planning.

## Route Here For

- Inspecting a config, expanding `_base_` inheritance, checking config naming, or applying `--cfg-options` overrides before a run.
- Preparing semantic segmentation dataset directories, suffixes, split files, `data_prefix`, `ann_file`, and `BaseSegDataset` arguments.
- Choosing or editing `LoadAnnotations`, augmentation transforms, `PackSegInputs`, class subsets, palettes, `ignore_index`, or `reduce_zero_label`.
- Understanding packaged config catalogs, `model-index.yml`, `dataset-index.yml`, and native dataset converter patterns without depending on source checkout scripts.

## Stay Out Of

- Launching training, validation, testing, distributed jobs, checkpoint resume, and metric interpretation; use the training/evaluation sub-skill.
- Implementing segmentors, heads, losses, backbones, registries, or custom model components; use the model customization sub-skill.
- Running inference APIs, visualization of model predictions, or deployment runtimes; use the inference sub-skill.

## First Moves

1. Read `references/configuration.md` for config inheritance, naming, inspection, and override rules.
2. Read `references/datasets-and-transforms.md` for dataset layout, `BaseSegDataset`, transform, class, palette, and label-index contracts.
3. Read `references/dataset-conversion.md` before converting raw datasets; converters are dataset-specific and reference-only here.
4. Use `scripts/inspect_mmseg_config.py --help` and `scripts/check_dataset_layout.py --help` to inspect configs and validate dataset file pairing safely.
5. If behavior is surprising, check `references/troubleshooting.md` before editing configs or data files.

## Bundled Tools

- `scripts/inspect_mmseg_config.py` expands an MMEngine config, applies optional `--cfg-options`, prints selected keys, and only writes output when `--dump` is explicitly provided.
- `scripts/check_dataset_layout.py` checks image/annotation directory existence, suffix counts, expected image-to-mask pairing, optional split files, and label-index notes without importing MMSegmentation.
