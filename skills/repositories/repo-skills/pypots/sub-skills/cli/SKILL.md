---
name: "cli"
description: "Guides PyPOTS CLI workflows for model listing, configuration,
  training, prediction, evaluation, tuning, benchmarking, and data preparation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# PyPOTS CLI

Use this sub-skill when the user wants to work through `pypots-cli` instead of
direct Python calls.

## Natural Triggers

- "run PyPOTS from the command line"
- "generate a model config"
- "train with a YAML file"
- "predict from a checkpoint"
- "evaluate predictions"
- "benchmark multiple models"
- "recommend a model or hyperparameters"
- "prepare CSV/HDF5 time-series data"

## First References

- Read `../../references/cli-reference.md` for commands, flags, and config
  shapes.
- Read `../../references/data-formats.md` for the HDF5/CSV schema used by the
  data commands.
- Read `../../references/api-reference.md` for model and checkpoint contracts.
- Read `../../references/troubleshooting.md` for YAML, backend, and root-dir
  failures.
- Run [`../../scripts/check_install.py`](../../scripts/check_install.py) for a safe package and CLI smoke check.

## Scope

This route covers:

- `pypots-cli info`
- `pypots-cli model list/describe/config/inspect`
- `pypots-cli train`
- `pypots-cli predict`
- `pypots-cli evaluate`
- `pypots-cli tune`
- `pypots-cli recommend`
- `pypots-cli benchmark`
- `pypots-cli data profile/prepare/reconstruct/convert/split/describe/load/list`

Route elsewhere:

- Model API work without CLI -> the task subskill for that task family.
- Maintainer-only repo chores such as docs generation or test harness changes ->
  treat as repository maintenance, not a user workflow.

## Core Workflow

1. Start with `pypots-cli info` or `pypots-cli model list` when the user wants
   to inspect the environment or supported models.
2. Use `pypots-cli model describe` and `pypots-cli model config` to generate a
   task-specific config before training.
3. Use `pypots-cli train` with a YAML or JSON config, then `predict` with the
   saved checkpoint and the same architecture config.
4. Use `evaluate` to score saved predictions against HDF5 ground truth.
5. Use `tune` for Optuna-based search and `benchmark` for side-by-side model
   comparison.
6. Use `data` commands to convert CSV, profile datasets, split HDF5 files, or
   load benchmark datasets into the PyPOTS HDF5 layout.

## Minimal Example Shape

```bash
pypots-cli info
pypots-cli model list --task imputation
pypots-cli model describe --name SAITS --task imputation
pypots-cli model config --name SAITS --task imputation --output config.yaml
pypots-cli train --config train.yaml
pypots-cli predict --model_path model.pypots --test_set test.h5 --config train.yaml
pypots-cli evaluate --predictions predictions.h5 --ground_truth ground_truth.h5 --task imputation
```

## Common Decision Points

- Use JSON configs if PyYAML is unavailable; use YAML when you want readable
  config templates.
- `model config` and `recommend` are useful before writing a training config by
  hand.
- `data prepare` is the normal bridge from CSV to the HDF5 shapes required by
  the model APIs.
- `benchmark` is the best way to compare a couple of models against the same
  data and metrics.
- `env`, `dev`, and `doc` are maintainer commands; they can mutate the current
  environment or checkout and should not be run casually.

## Validation Signals

A successful CLI workflow prints a model list, config, prediction summary, or
metric table and exits with code 0. Data commands should create the requested
HDF5 or CSV artifacts at the expected paths.
