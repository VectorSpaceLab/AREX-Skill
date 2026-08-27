---
name: training-configs
description: "Construct and troubleshoot SchNetPack spktrain and spkpredict
  Hydra commands, training recipes, logging, callbacks, checkpoints, and
  prediction outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# SchNetPack Training Configs

Use this sub-skill when the task is to build, explain, or debug SchNetPack `spktrain` or `spkpredict` commands and Hydra configuration overrides.

## Route Here For

- `spktrain` commands for QM9, MD17, rMD17, or custom ASE database training.
- Hydra override syntax, config groups, slash-vs-dot semantics, and adding optional groups or new keys.
- Trainer, logger, callback, optimizer, scheduler, run directory, checkpoint, and resume settings.
- `spkpredict` commands for a trained model directory, ASE DB input, cutoff, prediction output, and checkpoint selection.
- Safe command validation using `--help`, config printing, bounded `fast_dev_run`, or tiny split limits.

## Route Elsewhere

- Dataset creation, ASE DB schemas, units, splits, and property preparation: `../data-pipelines/SKILL.md`.
- Model architecture internals, representation choices, output modules, and custom modules: `../models-atomistic/SKILL.md`.
- ASE calculators, deployment, MD, uncertainty, or LAMMPS use after a model is trained: `../interfaces-md/SKILL.md`.

## Fast Decision Guide

- For command-line syntax and config composition, start with [Hydra CLI](references/hydra-cli.md).
- For QM9, MD17/rMD17, custom-data, trainer, logger, callback, and checkpoint recipes, use [Training recipes](references/training-recipes.md).
- For inference over an ASE database from a trained run, use [Prediction](references/prediction.md).
- For common CLI/config failures, use [Troubleshooting](references/troubleshooting.md).

## Safety Defaults

- Do not run long training, dataset downloads, GPU jobs, or native tests as a smoke check.
- Prefer `spktrain ... --help` or `spkpredict --help` to inspect resolved configs without training.
- For bounded execution only when explicitly requested, add `trainer.fast_dev_run=true`, tiny `data.num_train`/`data.num_val`, and explicit local `run.data_dir`, `run.path`, and `run.id` values.
