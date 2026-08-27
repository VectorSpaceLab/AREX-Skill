---
name: "data-preparation"
description: "Routes BasicTS dataset layout, raw conversion, and fixture
  validation workflows for forecasting, classification, imputation, and BLAST
  data."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# data-preparation

Use this sub-skill when the task is about dataset files, raw-data conversion, or validating that a BasicTS dataset folder matches the expected layout.

## Typical triggers

- "Validate a BasicTS dataset folder"
- "How do I create a tiny forecasting fixture?"
- "What files does BasicTS expect for UEA classification?"
- "Why is the BLAST memmap layout failing?"
- "How do the data-preparation scripts work?"

## What this sub-skill covers

- forecasting dataset layout used by `BasicTSForecastingDataset`
- imputation dataset layout used by `BasicTSImputationDataset`
- UEA classification layout used by `UEADataset`
- BLAST memmap shard layout used by `BLAST`
- safe validation of folder/file layouts
- safe creation of tiny forecasting fixtures for smoke use

## Read these bundled references first

- `references/data-formats.md` for the on-disk schemas.
- `references/troubleshooting.md` for missing-file and shape problems.
- `scripts/validate_basicts_dataset.py` for read-only validation.
- `scripts/make_tiny_forecasting_dataset.py` for a tiny fixture generator.

## Route here when the user asks for

- raw dataset conversion
- split-file naming conventions
- timestamp array requirements
- classification label file layout
- BLAST memmap shard or shape validation
- a tiny dataset folder for CPU smoke tests

## Route elsewhere when the user asks for

- launcher commands, checkpoint paths, or run execution → `training-evaluation`
- model forward contracts or output shapes → `model-development`
- callbacks, metrics, scalers, or taskflow hooks → `pipeline-extension`

## Working guidance

1. Identify the task family first: forecasting, classification, imputation, or BLAST.
2. Validate the folder layout before trying to run a trainer against it.
3. Check whether timestamps are required before claiming a fixture is usable.
4. Use the tiny fixture helper when you need a self-contained smoke dataset.

## When to read the helper scripts

- Run `scripts/validate_basicts_dataset.py` to check an existing dataset folder.
- Run `scripts/make_tiny_forecasting_dataset.py` to create a minimal forecasting fixture with timestamps and `meta.json`.

## Why this sub-skill exists

BasicTS data workflows are mostly about file layout and split conventions. Keeping those rules separate from training and model contracts makes it easier for future agents to validate datasets without opening the original repository scripts.
