---
name: generated-artifacts
description: "Helps agents work inside a completed automl-gs artifact folder to
  train, predict, inspect encoders, and troubleshoot generated runtime files."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Generated Artifacts

Use this sub-skill when you already have a timestamped folder created by
`automl_grid_search` and need to work with the generated runtime files.

This route covers the generated `model.py`, `pipeline.py`, `requirements.txt`,
`encoders/`, `metadata/`, and framework-specific model files inside the
artifact folder.

## Use this sub-skill for

- Running `train` or `predict` in a completed generated folder.
- Inspecting the frozen CSV schema, encoder files, or metadata outputs.
- Checking whether a generated folder is ready for XGBoost or TensorFlow
  runtime use.
- Diagnosing missing encoder, metadata, model, or prediction files.
- Comparing the generated XGBoost artifact path with the legacy TensorFlow
  artifact path.

## Do not use this sub-skill for

- Choosing the search space, framework, or hyperparameters.
- Starting a new search run from CSV + target.
- Explaining the package-level `automl_gs` CLI or grid-search loop.

If you need to generate a new timestamped folder, use the sibling
`grid-search` sub-skill instead: [grid-search](../grid-search/SKILL.md).

## Read first

- `references/generated-artifacts.md` for the folder layout, generated modes,
  CSV loading contract, encoders, metadata, prediction formats, and framework
  differences.
- `references/troubleshooting.md` for the common runtime failures and recovery
  steps.
- `scripts/check_generated_folder.py` to validate a generated folder and print
  the expected modes and files without importing the original repository.

## What to expect in a valid folder

A usable generated folder usually contains:

- `model.py` with `-d/--data`, `-m/--mode`, `-s/--split`, `-e/--epochs`,
  `-c/--context`, and `-t/--type` flags.
- `pipeline.py` with helper functions for encoder loading, data processing,
  prediction, and training.
- `requirements.txt` for the generated runtime, not the search loop.
- `encoders/` with JSON encoder state.
- `metadata/` with the per-epoch metrics log.
- `model.bin` for XGBoost or `model_weights.hdf5` for TensorFlow after train.

## Quick workflow

1. `cd` into the generated folder before running anything.
2. Use `scripts/check_generated_folder.py` to confirm the folder layout.
3. Run `python model.py -d <csv> -m train` to refresh encoders and model files.
4. Run `python model.py -d <csv> -m predict -t csv` or `-t json` to write
   predictions.

## Mode summary

- `train` rebuilds encoders, writes `metadata/results.csv`, and saves the
  framework model artifact.
- `predict` loads the saved encoders and model, then writes a predictions file.
- `--context automl-gs` is for the search loop; standalone use normally leaves
  the default context alone.

## Common checks

- If files are missing, confirm the working directory is the generated folder,
  not the parent search directory.
- If the runtime package does not match the artifact framework, read the
  troubleshooting guide before retrying.
- If the CSV schema no longer matches the generated `model.py`, do not rename
  the CSV headers to normalized Python names; use the original raw headers that
  appear in the generated script.
- If an XGBoost train run fails on label conversion, read the troubleshooting
  guide: this artifact path expects a numeric-compatible target column in the
  frozen dtype map.
