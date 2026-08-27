---
name: training-workflows
description: "Build and troubleshoot training, evaluation, checkpoint playback,
  and environment-wrapper workflows for pytorch-a2c-ppo-acktr-gail."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training Workflows

Use this sub-skill when the task is to run, adapt, or debug the repository's A2C, PPO, ACKTR, evaluation, or checkpoint-playback workflows from the command line.

## Route First

- For training/evaluation command patterns, recommended Atari/MuJoCo/PyBullet settings, checkpoint layout, and log behavior, read [references/training-and-evaluation.md](references/training-and-evaluation.md).
- For Gym environment creation, vectorization, normalization, frame stacking, image handling, and time-limit masking, read [references/environment-wrappers.md](references/environment-wrappers.md).
- For optional dependencies, Gym version issues, stale flags, long-running jobs, missing checkpoints, and simulator/backend failures, read [references/troubleshooting.md](references/troubleshooting.md).
- To construct a safe command without launching training, run [scripts/build_training_command.py](scripts/build_training_command.py).

## Best-Fit Tasks

Load this sub-skill for requests such as:

- Build a PPO/A2C/ACKTR command for Atari, MuJoCo/PyBullet, or a Gym-compatible task.
- Convert a stale experiment command to the current parser flags.
- Decide when to use `--use-gae`, `--use-linear-lr-decay`, `--use-proper-time-limits`, or CPU/CUDA options.
- Explain log directories, saved checkpoint names, evaluation intervals, or `enjoy` playback.
- Debug environment-wrapper behavior for Atari frame stacks, vector observations, time-limit truncation, or DeepMind Control Suite ids.

## Route Elsewhere

- Programmatic policy, rollout-storage, optimizer, distribution, and tensor-shape work belongs in the model-components sub-skill.
- Expert demonstration conversion, `ExpertDataset`, `Discriminator`, and `--gail` data-shape issues belong in the gail-imitation sub-skill.
- Cross-cutting installation and package import issues are also summarized in the root troubleshooting reference.

## Safe Command Builder

The bundled helper prints command lines; it never starts a Gym environment or training loop.

```bash
python scripts/build_training_command.py \
  --preset atari-ppo \
  --env-name PongNoFrameskip-v4 \
  --log-dir runs/pong \
  --seed 1
```

Use the output as a template for a checkout or packaged copy that contains the training entrypoint. Prefer editing the printed command over launching the helper from automation that assumes training is quick.
