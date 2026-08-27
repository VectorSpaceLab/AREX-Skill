---
name: configure-experiments
description: "Configure Lightning-Hydra-Template experiments with Hydra
  defaults, CLI overrides, debug presets, log paths, multiruns, and Optuna
  sweeps."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Configure Experiments

Use this sub-skill when the user needs to edit or debug the template's Hydra configuration rather than implement model/data code or run long training.

## Triggers

Read this sub-skill for tasks about:

- `configs/train.yaml`, `configs/eval.yaml`, defaults ordering, config groups, or `MissingConfigException`.
- CLI overrides such as `trainer.max_epochs=20`, `+trainer.precision=16`, `experiment=example`, `debug=fdr`, or list-style `tags=[...]`.
- Experiment YAML files, reproducible hyperparameter settings, or converting ad-hoc commands into `configs/experiment/*.yaml`.
- Hydra multiruns (`-m`), globbed experiments, repeated seeds, or `hparams_search=mnist_optuna`.
- Hydra output directories, `${paths.*}` interpolation, `PROJECT_ROOT`, tags, config printing, and debug presets.

## Quick workflow

1. Inspect the config groups and composed config without training:
   ```bash
   python <this-skill>/sub-skills/configure-experiments/scripts/render_config_summary.py --repo-root . --config-name train.yaml --list-groups
   python <this-skill>/sub-skills/configure-experiments/scripts/render_config_summary.py --repo-root . --config-name train.yaml --override experiment=example --resolve
   ```
2. Decide whether the change belongs in:
   - a group file under `configs/data`, `configs/model`, `configs/trainer`, `configs/callbacks`, or `configs/logger`;
   - a top-level defaults edit in `configs/train.yaml` or `configs/eval.yaml`;
   - a reproducible experiment file under `configs/experiment`;
   - a one-off CLI override.
3. For debugging, prefer `debug=fdr` for one train/val/test step, `debug=limit` for reduced batches, `debug=overfit` for overfit-to-batches checks, and `debug=profiler` for timing.
4. Before using sweeps, ensure `optimized_metric` matches a metric logged by the model. The default Optuna config expects `val/acc_best`.
5. If config targets fail to import, route to [customize-data-model](../customize-data-model/SKILL.md) and run its `_target_` checker.

## Read references

- [Hydra configuration](references/hydra-configuration.md): defaults list, config groups, override syntax, paths, tags, and composed config checks.
- [Sweeps and debugging](references/sweeps-and-debugging.md): multiruns, Optuna, repeated seeds, debug presets, and safe sweep cautions.
- [Troubleshooting](references/troubleshooting.md): config group misses, interpolation failures, tag prompts, metric mismatch, and stale target strings.

## Bundled script

- [scripts/render_config_summary.py](scripts/render_config_summary.py): compose a train/eval config from a target checkout, list groups, print selected fields, and optionally resolve interpolations. It does not run training or data downloads.

## Boundaries

- For `train_command`, checkpoint resume/eval, callbacks/loggers as runtime behavior, or accelerator execution, use [train-evaluate](../train-evaluate/SKILL.md).
- For adding DataModules, LightningModules, components, optimizers, schedulers, or package renames, use [customize-data-model](../customize-data-model/SKILL.md).
- For pytest/CI smoke selection or package metadata maintenance, use [test-maintain-template](../test-maintain-template/SKILL.md).
