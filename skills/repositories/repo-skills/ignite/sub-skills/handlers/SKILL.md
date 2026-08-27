---
name: handlers
description: "Routes Ignite checkpointing, logging, scheduling, progress, and
  profiling workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Ignite handlers workflows

Use this sub-skill when the request is about attaching helpers around an Ignite training loop: checkpointing, early stopping, EMA, progress bars, logger integrations, parameter schedulers, LR finding, timers, or profiling.

## Include here

- `Checkpoint`, `DiskSaver`, `ModelCheckpoint`, and checkpoint-retention / restore patterns.
- `EarlyStopping`, `TerminateOnNan`, `TimeLimit`, `Timer`, and `EMAHandler`.
- `ProgressBar`, `BaseLogger`, `TensorboardLogger`, `WandBLogger`, `MLflowLogger`, `NeptuneLogger`, `ClearMLLogger`, `PolyaxonLogger`, `VisdomLogger`, and the logger setup helpers.
- Parameter schedulers, state schedulers, `BatchSizeScheduler`, `ReduceLROnPlateauScheduler`, and LR-finder helpers.
- Time profilers and related training instrumentation.
- Common handler recipes from the MNIST logging examples, CIFAR10 logging examples, and other monitoring-oriented workflows.

## Exclude or route elsewhere

- Training-loop structure, resume state mechanics, and deterministic engine details belong in `sub-skills/engine/`.
- Metric definitions and metric math belong in `sub-skills/metrics/`.
- Distributed backend selection and `Parallel` belong in `sub-skills/distributed/`.
- Legacy `ignite.contrib` notes live in `references/legacy-contrib.md`.

## Start here

- Read `references/api-reference.md` when you need exact class names, handler groups, or setup helper signatures.
- Read `references/workflows.md` for checkpoint/resume, early-stopping, logger, and scheduler recipes.
- Read `references/troubleshooting.md` when optional packages, logger credentials, or handler wiring fail.
- Run `scripts/smoke_handlers.py` for a small synthetic check that exercises checkpointing, early stopping, and scheduler previews.

## Common triggers

- "How do I save the best checkpoint?"
- "How do I stop training early when validation stops improving?"
- "How do I attach TensorBoard, W&B, MLflow, or ClearML logging?"
- "How do I configure a learning-rate scheduler or LR finder?"
- "How do I add a progress bar or a time profiler?"

## Useful boundary notes

This sub-skill owns the training extras that sit around the loop, but not the loop itself. If the user mainly needs to build or resume the loop, stay in `sub-skills/engine/` and link out to this route for the checkpoint or logging parts.
