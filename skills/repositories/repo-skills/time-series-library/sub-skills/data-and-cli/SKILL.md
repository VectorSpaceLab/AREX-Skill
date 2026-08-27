---
name: data-and-cli
description: "Prepare Time-Series-Library data layouts, choose safe run.py
  flags, validate local files, and understand checkpoints, result folders, and
  smoke-test commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TSLib Data and CLI

Use this sub-skill when the task is about getting a TSLib command to start correctly: local data files, `run.py` flags, dataset names, CPU/GPU flags, smoke checks, output locations, or confusing path/download behavior.

## Route Here

- Choose or validate `--task_name`, `--data`, `--root_path`, `--data_path`, `--features`, `--target`, and `--freq`.
- Prepare a local `custom` CSV, ETT-style CSV, M4 folder, anomaly folder, or UEA `.ts` folder.
- Debug Hugging Face fallback/download surprises when local files are missing.
- Interpret `checkpoints/`, `results/`, `test_results/`, `m4_results/`, and result text file locations.
- Decide whether to use `--no_use_gpu`, `--gpu`, `--gpu_type`, `--use_multi_gpu`, or `CUDA_VISIBLE_DEVICES` for a safe check.
- Build a tiny smoke-test dataset before routing to a task-specific sub-skill.

## Reroute

- Long-term, short-term/M4, exogenous, or zero-shot forecasting details: use `../forecasting/SKILL.md`.
- Imputation, anomaly detection, or classification recipes: use `../imputation-anomaly-classification/SKILL.md`.
- Model catalog, optional Mamba/LTSM dependencies, augmentation flags, or adding a model: use `../foundation-models-and-customization/SKILL.md`.
- Cross-cutting installation failures: start with `../../references/installation-and-environment.md` and `../../references/troubleshooting.md`.

## Fast Preflight

From this sub-skill directory, point helpers at the user's TSLib checkout:

```bash
python ../../scripts/check_tslib_environment.py --repo-root /path/to/Time-Series-Library --check-torch --check-core-imports
python ../../scripts/create_tiny_tslib_dataset.py --output /path/to/Time-Series-Library/dataset/tiny-custom/tiny.csv
python scripts/validate_tslib_data.py \
  --task long_term_forecast --data custom \
  --root-path /path/to/Time-Series-Library/dataset/tiny-custom \
  --data-path tiny.csv --target OT
```

Then run a task smoke from the TSLib checkout with `--no_use_gpu`, `--train_epochs 1`, `--num_workers 0`, and small windows before scaling up.

## Data Routing Rules

1. Match `--task_name` to a loader-compatible `--data` value. For example, `classification` normally uses `--data UEA`, while anomaly detection uses one of `PSM`, `MSL`, `SMAP`, `SMD`, or `SWAT`.
2. For local CSV forecasting/imputation, make sure `--root_path` points to the directory and `--data_path` is the filename. If the file is absent, the loader may try a Hub dataset whose config name is derived from the filename.
3. For `custom`, include a `date` column and a numeric target column. `--target` defaults to `OT`.
4. For UEA, `--model_id` is the dataset name used to locate `<DatasetName>_TRAIN.ts` and `<DatasetName>_TEST.ts`.
5. For benchmark scripts, review and rewrite hard-coded `CUDA_VISIBLE_DEVICES` and dataset folders before running.

## References and Helpers

- `references/data-layouts.md` details local files expected for CSV, M4, anomaly, and UEA loaders.
- `references/cli-and-outputs.md` explains required flags, GPU controls, setting strings, and output folders.
- `references/troubleshooting.md` maps common path, parser, download, and output problems to fixes.
- `scripts/validate_tslib_data.py` performs file/header/layout checks without training or downloading data.
- `../../references/cli-arguments.md` is the shared root CLI reference.
- `../../references/data-formats.md` is the shared cross-task data-format reference.

## Avoid

- Do not run full benchmark shell scripts as a preflight. Render a smaller command or use the forecasting command builder.
- Do not assume a missing local file is harmless; it can trigger network fallback and fail with a misleading Hub error.
- Do not let CUDA defaults choose the device for a smoke test; add `--no_use_gpu` unless GPU behavior is the point of the test.
- Do not treat tiny synthetic data as benchmark evidence. It validates plumbing only.
