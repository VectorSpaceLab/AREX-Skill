---
name: "dataset-config"
description: "Routes NanoDet dataset, preprocessing, and config-validation
  workflows for COCO, XML, YOLO, and model-assembly setups."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# dataset-config

Use this sub-skill when you need to understand or validate a NanoDet config, prepare a dataset layout, or check the preprocessing path before training or inference.

## Use this route for

- Reading or editing YAML config files.
- Verifying `save_dir`, `model`, `data`, `device`, `schedule`, `evaluator`, `log`, and `class_names` fields.
- Choosing between `CocoDataset`, `XMLDataset`, and `YoloDataset`.
- Checking `keep_ratio`, `multi_scale`, and augmentation pipeline settings.
- Confirming that a config can build the expected model family.

## Do not use this route for

- Training / validation / checkpoint lifecycle logic. Use `training` instead.
- Image/video/webcam inference or model export. Use `inference-export` instead.
- Repository maintenance or packaging chores.

## Read first

- `references/configuration.md` for the NanoDet config structure and field meanings.
- `references/data-formats.md` for COCO, XML, and YOLO data-layout details.
- `references/troubleshooting.md` for config, dataset, and preprocessing failures.
- `../../references/api-reference.md` when you need verified builder signatures.

## Skill-owned scripts

- `scripts/check_config.py` — load a config, check class counts, and build the model as a smoke test.
- `scripts/check_dataset.py` — build a dataset from a config and inspect a sample.

## Typical workflow

1. Load the YAML config.
2. Check the model/dataset fields that affect runtime behavior.
3. Verify the dataset layout and annotation format.
4. Run the skill-owned smoke script before moving to training or inference.

## Cross-links

- If the config is valid but training fails later, switch to `training`.
- If the config is valid and you only need to run a demo or export a model, switch to `inference-export`.
