---
name: customize-data-model
description: "Customize Lightning-Hydra-Template DataModules, LightningModules,
  network components, optimizers, schedulers, and Hydra target wiring."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Customize Data and Model Code

Use this sub-skill when adapting the template away from the MNIST example or repairing target imports after changing package/module names.

## Triggers

Read this sub-skill for tasks about:

- Replacing `MNISTDataModule`, adding a new `LightningDataModule`, or changing data splits/loaders.
- Replacing `MNISTLitModule`, adding model components, changing optimizers/schedulers, metrics, or `torch.compile` behavior.
- Editing `configs/data/*.yaml` or `configs/model/*.yaml` `_target_` strings.
- Renaming the default `src` package and fixing stale imports.
- Diagnosing batch-size/world-size, metric key, dataloader dtype/shape, or target import errors.

## Quick workflow

1. Before editing, render the composed config and note current data/model targets.
2. Add or update Python classes in the target checkout's package.
3. Update config `_target_` strings and constructor parameters together.
4. Run the bundled target checker:
   ```bash
   python <this-skill>/sub-skills/customize-data-model/scripts/check_hydra_targets.py --repo-root . --config configs/data/mnist.yaml --config configs/model/mnist.yaml
   ```
5. Compose and instantiate train/eval configs without data download:
   ```bash
   python <this-skill>/scripts/check_lightning_hydra_project.py --repo-root . --config-name train.yaml --instantiate
   ```
6. If the task needs real data behavior, adapt pytest fixtures or use cached/tiny data before running training tests.

## Read references

- [Data and model API](references/data-model-api.md): verified signatures, method contracts, metrics, optimizer/scheduler wiring, and config fields.
- [Customization recipes](references/customization-recipes.md): replacing data/model modules, renaming packages, and keeping configs/tests aligned.
- [Troubleshooting](references/troubleshooting.md): stale `_target_`, batch-size divisibility, metric mismatch, dataloader/data-download issues, and `torch.compile` problems.

## Bundled script

- [scripts/check_hydra_targets.py](scripts/check_hydra_targets.py): scans YAML configs for `_target_` dotted paths, imports them from a target checkout, and optionally instantiates composed train/eval configs via the root inspector.

## Boundaries

- For experiment YAML, sweeps, overrides, and paths, use [configure-experiments](../configure-experiments/SKILL.md).
- For running train/eval/checkpoints/loggers/accelerators, use [train-evaluate](../train-evaluate/SKILL.md).
- For package metadata, tests, CI, and rename gates, use [test-maintain-template](../test-maintain-template/SKILL.md).
