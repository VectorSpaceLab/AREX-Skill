---
name: training-and-evaluation
description: "Safely build and adapt pytorch-semseg training and validation
  workflows, including dry-run commands, checkpoints, logs, metrics, and costly
  prerequisite checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# pytorch-semseg Training and Evaluation

Use this sub-skill when the task is to run, adapt, or explain the repository's
training and validation workflows without reopening the original source files.
The bundled scripts are dry-run command builders: they print commands and
warnings, but never launch training, validation, downloads, dataset scans, or
writes.

## Start here

- Build a training command with [scripts/build_train_command.py](scripts/build_train_command.py), then review [references/workflows.md](references/workflows.md) before running it manually.
- Build a validation command with [scripts/build_validate_command.py](scripts/build_validate_command.py), then review [references/checkpoints-and-metrics.md](references/checkpoints-and-metrics.md) for checkpoint and metric interpretation.
- For failures, use [references/troubleshooting.md](references/troubleshooting.md).

## Covered capabilities

- Training entry point: `python train.py --config CONFIG`.
- Validation entry point: `python validate.py --config CONFIG --model_path CHECKPOINT` with `--eval_flip` / `--no-eval_flip` and `--measure_time` / `--no-measure_time`.
- Training loop wiring: seeds, augmentations, `get_loader`, `get_model`, `DataLoader`, `runningScore`, optimizer, scheduler, loss, TensorBoardX `SummaryWriter`, checkpoint save/resume.
- Validation loop wiring: checkpoint `model_state`, `convert_state_dict`, flip averaging, fps reporting, metric keys, and per-class IoU output.
- Safety decisions for dataset-bound or expensive runs.

## Route elsewhere

- YAML schema design, dataset layouts, loader-specific split names, and config validation belong to the sibling `data-and-configs` sub-skill.
- Model constructor parameters, loss/optimizer/scheduler registry tables, and API-level model selection belong to `model-zoo-and-apis`.
- `test.py` single-image inference, output masks, palettes, and DenseCRF belong to `single-image-inference`.

## Safe workflow pattern

1. Use the relevant command builder in this directory.
2. Treat every warning as a pre-run checklist item.
3. Resolve dataset/checkpoint/config compatibility issues using the routed sibling sub-skills when needed.
4. Only after explicit user approval for compute, dataset reads, and log/checkpoint writes should a future agent run the printed command manually from an appropriate repository checkout.
