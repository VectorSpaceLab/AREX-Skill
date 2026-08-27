---
name: data-configs
description: "Guides FCOS YAML config selection, MODEL.FCOS options, dataset
  catalog layouts, custom data planning, and safe config validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# FCOS Data and Configs

Use this sub-skill when the task involves FCOS YAML files, `cfg.merge_from_file`, `MODEL.FCOS` keys, dataset catalog names, COCO/VOC/Cityscapes directory layouts, Cityscapes conversion, or validation before train/eval.

## Start here

1. Read [`references/configuration.md`](references/configuration.md) for config merge behavior and core FCOS options.
2. Read [`references/model-catalog.md`](references/model-catalog.md) to choose a config family.
3. Read [`references/data-formats.md`](references/data-formats.md) for COCO/VOC/Cityscapes layouts and custom dataset constraints.
4. Run [`scripts/validate_fcos_config.py`](scripts/validate_fcos_config.py) to merge a config safely.
5. Run [`scripts/validate_dataset_layout.py`](scripts/validate_dataset_layout.py) before starting train/eval.
6. Read [`references/troubleshooting.md`](references/troubleshooting.md) for YAML, override, dataset-key, and class-count failures.

## Boundaries

- Route actual training/evaluation commands to [`../training-evaluation/SKILL.md`](../training-evaluation/SKILL.md).
- Route single-image demos to [`../inference-demo/SKILL.md`](../inference-demo/SKILL.md).
- Route ONNX export configuration to [`../onnx-export/SKILL.md`](../onnx-export/SKILL.md).
- Route source-code registry edits or tests to [`../internals-maintenance/SKILL.md`](../internals-maintenance/SKILL.md).

## Common workflow

For a user who wants to train or evaluate:

1. Pick the closest config family and model size.
2. Validate that the config loads.
3. Validate dataset paths for the dataset keys in `DATASETS.TRAIN` and `DATASETS.TEST`.
4. Only then build training/evaluation commands.
