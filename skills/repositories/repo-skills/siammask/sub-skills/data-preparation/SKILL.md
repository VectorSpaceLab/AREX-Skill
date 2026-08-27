---
name: data-preparation
description: "Guides SiamMask benchmark and training data acquisition, layout
  validation, crop/index preprocessing, VOT JSON generation, and data-path
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SiamMask Data Preparation

Use this sub-skill when the task is about VOT/DAVIS/YouTube-VOS benchmark data, COCO/DET/VID/YouTube-VOS training data, `crop511` preprocessing, dataset JSON files, or missing data paths.

## Safety First

Most original preprocessing steps involve large downloads, unzips, symlinks, multiprocessing crops, or generated files. Keep commands in dry-run/read-only mode until the user explicitly approves network, disk, and runtime costs.

## Main Routes

| User intent | What to do |
| --- | --- |
| "Check whether data is prepared" | Run [scripts/check_dataset_layout.py](scripts/check_dataset_layout.py) and read [references/data-layouts.md](references/data-layouts.md). |
| "Generate VOT metadata JSON" | Use [scripts/generate_vot_json.py](scripts/generate_vot_json.py) on an existing VOT directory; it adapts the repo metadata generator without downloading data. |
| "Run original preprocessing/crop scripts" | Use [scripts/run_data_prep.py](scripts/run_data_prep.py) in dry-run mode, then add `--run` only after approving side effects. |
| "Prepare training data" | Read [references/workflows.md](references/workflows.md#training-data-preparation-order) and validate COCO/DET/VID/YouTube-VOS generated outputs before training. |
| "Dataset errors during tracking/training" | Read [references/troubleshooting.md](references/troubleshooting.md) and root troubleshooting. |

## Bundled Helpers

- `scripts/check_dataset_layout.py`: read-only JSON report for VOT, DAVIS, YouTube-VOS, COCO, DET, VID, or the full training data mix.
- `scripts/generate_vot_json.py`: self-contained VOT metadata generator for existing local VOT datasets.
- `scripts/run_data_prep.py`: dry-run-first launcher for checkout-local data-preparation scripts; useful for auditing cwd, `PYTHONPATH`, and arguments before heavy preprocessing.

Example read-only check:

```bash
python scripts/check_dataset_layout.py --data-root <siammask-checkout>/data --dataset training
```

Example VOT metadata generation:

```bash
python scripts/generate_vot_json.py \
  --dataset-root <siammask-checkout>/data/VOT2019 \
  --dataset-name VOT2019 \
  --output <siammask-checkout>/data/VOT2019.json
```

## Cross-Links

- After benchmark data exists, use [../tracking/SKILL.md](../tracking/SKILL.md) for test/eval/tune runs.
- After training data exists, use [../training/SKILL.md](../training/SKILL.md) for CUDA training dry-runs.
- Use root [install/setup](../../references/install-and-setup.md) for Cython extension and pycocotools build details.
