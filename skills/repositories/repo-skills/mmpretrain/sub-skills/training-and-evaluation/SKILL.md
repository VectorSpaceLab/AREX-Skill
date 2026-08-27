---
name: training-and-evaluation
description: "Inspect MMPreTrain configs, plan train/test commands, and choose
  safe single-machine, distributed, Slurm, resume, AMP, auto-scale-lr, TTA,
  result-dump, CPU fallback, and K-fold options."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training and Evaluation

Use this route when the user needs to prepare or modify a training or evaluation config, choose a launch pattern, or turn a model checkpoint into a reproducible train/test command.

## Covers

- Inspecting the merged config before launch.
- Understanding `_base_` inheritance, `_delete_`, and `--cfg-options`.
- Planning package-level `mim train mmpretrain` and `mim test mmpretrain` runs.
- Choosing between local, distributed, and Slurm launch patterns.
- Deciding when to use `--resume`, `--amp`, `--auto-scale-lr`, `--tta`, `--out`, and `--out-item`.
- Forcing CPU-only execution with `CUDA_VISIBLE_DEVICES=-1`.
- Planning K-fold cross-validation commands.

## Start here

- Read `references/configuration.md` when the question is about config inheritance, field placement, or `--cfg-options` syntax.
- Read `references/training-testing-cli.md` when the question is about train/test command shape, launcher choices, distributed environment variables, result outputs, or K-fold.
- Run `scripts/print_config.py` to expand a config and apply safe overrides before launching.
- Run `scripts/build_train_test_command.py` to print a reviewed command for train/test/dist/Slurm/K-fold without executing anything.
- Read `references/troubleshooting.md` for config merge, resume, AMP/TTA, distributed port, NCCL, or CPU fallback failures.

## Route elsewhere

- Dataset annotation, label files, registry-based dataset design, and data-format authoring belong in `../datasets-and-customization/SKILL.md`.
- Model zoo discovery, `get_model`, `inference_model`, inferencers, and feature extraction belong in `../model-zoo-inference/SKILL.md`.
- Log/result analysis, confusion matrices, FLOPs, CAM, t-SNE, visualization, checkpoint publishing, and serving belong in `../tools-analysis-and-deployment/SKILL.md`.

## Common triggers

- "How do I change the learning rate schedule?"
- "How do I inspect the final config after inheritance?"
- "What do I pass for resume versus load_from?"
- "How do I run on CPU only?"
- "How do I launch 8 GPUs or Slurm?"
- "How do I evaluate with TTA and dump predictions?"
- "How do I use K-fold cross validation?"

## Command-planning flow

1. Inspect the config with `scripts/print_config.py`.
2. Decide whether the run is direct, distributed, or Slurm.
3. Use `scripts/build_train_test_command.py` to print the command.
4. Apply the generated command in the shell only after the config and launcher choices are settled.
