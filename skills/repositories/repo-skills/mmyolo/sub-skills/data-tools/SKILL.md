---
name: data-tools
description: "Prepare and validate datasets for MMYOLO:
  COCO/YOLO/VOC/DOTA/LabelMe layouts, converters, analysis tools, and data
  APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# MMYOLO data-tools

Use this sub-skill when the task is about making dataset annotations usable by MMYOLO before training, evaluation, browsing, anchor analysis, or config wiring.

## Fast route

1. For annotation schema and config wiring, read [data formats](references/data-formats.md).
2. For converter, browser, statistics, anchor, subset, split, and DOTA recipes, read [data tools](references/data-tools.md).
3. For data-prep failures and MMYOLO-specific gotchas, read [troubleshooting](references/troubleshooting.md).
4. Run the bundled validators when possible before sending a user to training/evaluation:

```bash
python scripts/inspect_coco_annotations.py annotations/trainval.json --image-root images --require-annotations
python scripts/convert_yolo_txt_to_coco_skeleton.py ./my_yolo_dataset --out annotations/result.json --image-width 640 --image-height 480
```

## Own these tasks

- Validate COCO-style `images`, `annotations`, and `categories` consistency, including image/category references, duplicate ids, bbox shape, and image file presence.
- Convert a small YOLO normalized-txt dataset into a COCO detection JSON skeleton and catch invalid normalized coordinates early.
- Explain COCO, YOLO txt, VOC, DOTA, LabelMe, cat, and balloon data layouts.
- Wire dataset fields into MMYOLO configs: `data_root`, `ann_file`, `data_prefix`, `metainfo`, and evaluator `ann_file`.
- Summarize MMYOLO data utilities for browsing annotations/datasets, dataset statistics, anchor optimization, COCO subset extraction, COCO splitting, and DOTA splitting without requiring the original source checkout.
- State dataset and transform API facts from MMYOLO's package surface.

## Route away

- Actual training, testing, resume, AMP, distributed launch, or metric execution: route to `training-evaluation`.
- Config inheritance, model-family selection, and complete model/head edits: route to `config-customization`.
- Model internals, registries, custom modules, and low-level model API behavior: route to `model-api`.
- Deployment export or checkpoint conversion: route to `deployment-conversion`.

## Safety notes

The bundled scripts are deterministic, local-file-only helpers. They do not download datasets, run training, invoke MMYOLO, or require OpenMMLab packages. Treat MMYOLO's heavier visual/statistical utilities as reference recipes unless the user explicitly has a prepared checkout/environment and accepts their plotting, copying, or compute side effects.
