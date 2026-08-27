---
name: train-evaluate
description: "Run and debug Lightning-Hydra-Template training and evaluation
  commands, checkpoints, callbacks, loggers, accelerators, and safe repeated
  runs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Train and Evaluate

Use this sub-skill when the user wants to run, resume, debug, or adapt the template's Lightning training/evaluation workflow.

## Triggers

Read this sub-skill for tasks about:

- `python src/train.py`, `python src/eval.py`, `train_command`, or `eval_command`.
- Checkpoint resume/evaluation using `ckpt_path`, `last.ckpt`, or `ModelCheckpoint` output.
- Callbacks, loggers, `logger=csv`, W&B/Neptune/Comet/MLflow/Aim configs, or hyperparameter logging.
- Trainer presets such as `trainer=cpu`, `trainer=gpu`, `trainer=ddp`, `trainer=ddp_sim`, and `trainer=mps`.
- Fast-dev, batch-limit, overfit, or profiler training commands.
- Repeated training commands or adapting the repo's scheduling shell pattern.

## Quick workflow

1. Inspect CLI/config without training:
   ```bash
   train_command --help
   eval_command --help
   python <this-skill>/scripts/check_lightning_hydra_project.py --repo-root . --config-name train.yaml --instantiate
   ```
2. For a safe smoke run, disable online loggers and use a debug config. Remember the MNIST example can download data:
   ```bash
   python src/train.py debug=fdr logger=null
   ```
3. For normal training, choose experiment, trainer, logger, and tags explicitly:
   ```bash
   python src/train.py experiment=example trainer=cpu logger=csv tags='[mnist,baseline]'
   ```
4. For resume, pass the checkpoint to the train config:
   ```bash
   python src/train.py ckpt_path=/path/to/checkpoints/last.ckpt
   ```
5. For evaluation, pass a checkpoint to the eval config:
   ```bash
   python src/eval.py ckpt_path=/path/to/checkpoints/last.ckpt logger=null
   ```
6. To preview repeated runs without executing them, use [scripts/run_scheduled_training.sh](scripts/run_scheduled_training.sh).

## Read references

- [Training and evaluation](references/training-evaluation.md): train/eval object flow, checkpoint semantics, commands, metrics, and safe validation.
- [Loggers, callbacks, and accelerators](references/loggers-callbacks-accelerators.md): logger packages/credentials, callback defaults, trainer groups, and backend scope.
- [Troubleshooting](references/troubleshooting.md): missing checkpoint, monitor metric, logger credentials, MNIST/data download, DDP, batch divisibility, and Hydra output paths.

## Bundled script

- [scripts/run_scheduled_training.sh](scripts/run_scheduled_training.sh): safe adaptation of the repository's `scripts/schedule.sh`; defaults to dry-run and requires `--execute` before launching training.

## Boundaries

- For Hydra defaults, experiment YAML, sweeps, and debug config composition, use [configure-experiments](../configure-experiments/SKILL.md).
- For adding new data/model code or fixing `_target_` imports, use [customize-data-model](../customize-data-model/SKILL.md).
- For pytest/CI choices or no-network smoke gates, use [test-maintain-template](../test-maintain-template/SKILL.md).
