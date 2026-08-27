---
name: training
description: "Configure PPO training runs, resolve log and checkpoint paths, and
  interpret the repository's environment presets and action-std schedule."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Training

Use this sub-skill when the user wants to start a PPO training run, change the environment preset, understand the log/checkpoint layout, or adjust the continuous-action exploration schedule.

Do not use this sub-skill for pretrained checkpoint evaluation, plotting, or GIF composition. Route those tasks to the sibling sub-skills. Route low-level PPO class behavior to the root [API reference](../../references/api-reference.md).

## What this sub-skill owns

- The native training flow from environment creation through checkpoint and CSV logging.
- The repository's default training environment and the environment-specific preset values in the pretrained README.
- The output naming scheme for logs and checkpoints.
- Continuous-action `action_std` initialization and decay.
- The training-specific failure modes that appear when Gym, Roboschool, or Box2D dependencies are missing or mismatched.

## Quick workflow

1. **Resolve the training preset before running anything heavy.** Use the bundled helper from this sub-skill directory:

   ```bash
   python scripts/training_config_helper.py --list-presets
   python scripts/training_config_helper.py --env-name RoboschoolWalker2d-v1 --create-dirs
   ```

   The helper is configuration-only by default. It does not import Gym or start a long training loop.

2. **Choose the environment family carefully.**

   - Discrete environments use `has_continuous_action_space = False` and `action_std = None`.
   - Continuous environments use `has_continuous_action_space = True` and a starting `action_std` such as `0.6`.

3. **Keep the output layout consistent.** The native training pattern writes logs and checkpoints into environment-specific subdirectories so repeated runs do not overwrite one another.

4. **Use the root API reference for PPO internals.** The same `PPO` constructor and `RolloutBuffer` behavior back both training and evaluation.

## Core references

- [Training workflow](references/training-workflow.md) - the native training loop shape, output directories, and helper usage.
- [Hyperparameters and outputs](references/hyperparameters-and-outputs.md) - environment presets, default frequencies, and filename conventions.
- [Troubleshooting](references/troubleshooting.md) - missing dependencies, API drift, output path problems, and action-std mistakes.
- [Root PPO API reference](../../references/api-reference.md) - shared class and save/load behavior.

## Validation commands

Safe checks for this sub-skill should stay configuration-first unless the environment packages are already installed and the user explicitly wants a long run:

```bash
python scripts/training_config_helper.py --help
python scripts/training_config_helper.py --env-name CartPole-v1 --json
python -m py_compile scripts/training_config_helper.py
```

Do not treat the absence of Gym, Roboschool, or Box2D as a failure of the helper. Those packages are required only for the live training route.
