---
name: data-preparation
description: "Prepare and troubleshoot OpenPCDet dataset layouts, info pickle
  files, ground-truth databases, splits, and DATA_CONFIG settings."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# OpenPCDet Data Preparation

Use this sub-skill for dataset root layouts, `DATA_CONFIG`, info/database generation, split files, class lists, and dataloader/data-prep failures.

## Fast route

1. Read `references/dataset-workflows.md` for the dataset-specific map.
2. Use `scripts/check_openpcdet_dataset_layout.py` on the target dataset root before launching converters.
3. Use the root helper `../../scripts/plan_openpcdet_command.py --mode <dataset>-infos` to print dataset-prep commands for an OpenPCDet checkout.
4. Return to `../training-and-evaluation/SKILL.md` only after dataset info/database products and config paths are aligned.

## Required checks

- `DATA_CONFIG.DATASET` must match the intended dataset registry name.
- `DATA_CONFIG.DATA_PATH` must point at the dataset root expected by that dataset's implementation.
- `CLASS_NAMES` must match both generated infos and any checkpoint/config being reused.
- Database-sampling configs require `DB_INFO_PATH` and database object files generated from the same training split.

## Common ownership boundaries

- Dataset folder schemas and conversion: this sub-skill.
- Train/test CLI after data exists: `../training-and-evaluation/SKILL.md`.
- Custom `.bin`/`.npy` inference samples: `../inference-and-custom-data/SKILL.md`.
- Model-family assumptions in configs: `../models-and-configs/SKILL.md`.
