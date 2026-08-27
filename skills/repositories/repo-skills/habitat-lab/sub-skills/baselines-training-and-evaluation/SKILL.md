---
name: baselines-training-and-evaluation
description: "Use Habitat-Baselines training, evaluation, Hydra configs,
  trainers, checkpoints, and benchmark scripts safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Habitat-Baselines Training And Evaluation

Use this sub-skill when the task is about running, inspecting, or adapting Habitat-Baselines training and evaluation workflows rather than implementing Habitat core environments or new model code.

## Read This First

- For CLI syntax, Hydra config groups, legacy command conversion, and safe config inspection, read [references/cli-reference.md](references/cli-reference.md).
- For choosing RL/IL configs, training versus evaluation, checkpoint handling, TensorBoard/video outputs, and trainer APIs, read [references/training-workflows.md](references/training-workflows.md).
- For Habitat 2.0/3.0 benchmark scripts, expensive runtime expectations, and safe adaptation patterns, read [references/benchmarking.md](references/benchmarking.md).
- For PyTorch/CUDA, missing data/checkpoints, Hydra override errors, multiprocessing, DD-PPO, and video/TensorBoard failures, read [references/troubleshooting.md](references/troubleshooting.md).
- To inspect CLI availability or compose a baseline config without starting training, use [scripts/baselines_cli_probe.py](scripts/baselines_cli_probe.py).

## Use For

- Running `habitat-baselines` or `python -m habitat_baselines.run` with `--config-name` and Hydra overrides.
- Converting old `--exp-config ... --run-type train/eval` commands to current Hydra-style commands.
- Selecting PointNav, ObjectNav, ImageNav, InstanceImageNav, Rearrange, SocialNav, SocialRearrange, or EQA baseline configs.
- Switching among `ppo`, `ddppo`, `ver`, and IL trainers such as `pacman`, `vqa`, and `eqa-cnn-pretrain`.
- Resuming training, evaluating checkpoint files or checkpoint folders, and interpreting log, checkpoint, TensorBoard, video, and metric outputs.
- Deciding whether Habitat 2/3 benchmark scripts are safe to adapt or should be treated as reference-only.

## Do Not Use For

- Creating Habitat tasks, datasets, sensors, measurements, or core `Env` APIs; use the tasks/datasets/envs sub-skill.
- Installation, package selection, and global config basics; use setup/configuration guidance first.
- HITL app or interactive policy integration; use the HITL sub-skill.
- Writing a new trainer, policy, registry entry, or observation transformer implementation; use extension-patterns.

## Safe Default Workflow

1. Confirm that `habitat-baselines --help` or `python -m habitat_baselines.run --help` works before proposing a long run.
2. Use the probe script to list likely config names or compose the requested config with overrides.
3. If the user asks for actual training or evaluation, verify simulator support, dataset paths, checkpoint paths, GPU expectations, output directories, and whether the command is intended as a local smoke run or an expensive experiment.
4. Prefer short dry-run config composition and small override examples over running benchmark scripts or full training in an agent session.

## Key Entry Points

- Console script: `habitat-baselines`, registered to `habitat_baselines.run:main`.
- Module CLI: `python -m habitat_baselines.run`.
- Programmatic config loader: `habitat_baselines.config.default.get_config(config_path, overrides=None)`.
- Programmatic execution: `habitat_baselines.run.execute_exp(config, "train")` or `execute_exp(config, "eval")`.
- Trainer registry: `habitat_baselines.common.baseline_registry.baseline_registry.get_trainer(config.habitat_baselines.trainer_name)`.
