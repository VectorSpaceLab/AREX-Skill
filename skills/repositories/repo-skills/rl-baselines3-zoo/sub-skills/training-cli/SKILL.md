---
name: training-cli
description: "Operate RL Baselines3 Zoo training, resume, checkpoint,
  evaluation-callback, and log-folder command workflows safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# training-cli

Use this sub-skill when the task is to build, run, resume, or debug RL Baselines3 Zoo training commands for an installed `rl_zoo3` package. It covers `rl_zoo3 train` and `python -m rl_zoo3.train`, algorithm/environment selection, bounded training runs, continuation from a saved zip, replay-buffer continuation, evaluation/checkpoint callbacks, vectorized environment choice, seeds/UUID/progress/device options, and the training output layout.

## Start here

1. Prefer the module command unless the caller specifically needs the console entry point:
   - `python -m rl_zoo3.train ...` avoids importing the `rl_zoo3` console router and its plotting modules.
   - `rl_zoo3 train ...` is valid when the console entry point imports successfully; if it fails on plotting extras, switch to the module command or use the root install guidance at `../../references/install-and-environment.md`.
2. For command recipes and training lifecycle details, read [references/training-workflows.md](references/training-workflows.md).
3. For the complete train flag surface, read [references/cli-reference.md](references/cli-reference.md).
4. For known failures and recovery actions, read [references/troubleshooting.md](references/troubleshooting.md).
5. To build a command without launching training, run [scripts/train_command_builder.py](scripts/train_command_builder.py). The helper validates common unsafe combinations and only prints a shell command.

## Operating checklist

- Identify `--algo`, `--env`, intended run length, backend/device, and whether this is a smoke test, full run, resume run, or off-policy replay-buffer continuation.
- Use a caller-controlled `--log-folder`; do not rely on a shared `logs/` directory unless that is intentional.
- For any potentially long run, pass `--n-timesteps`, `--eval-freq`, `--save-freq`, `--seed`, and optionally `--uuid` and `--progress`.
- Validate that the Gymnasium environment id is registered before training. For custom packages, pass `--gym-packages` so registration happens before RL Zoo checks the registry.
- For `--trained-agent`, provide an existing `.zip` path. For off-policy continuation, place `replay_buffer.pkl` next to that zip and use `--save-replay-buffer` if the replay buffer should be saved again.
- Remember that RL Zoo divides positive `--eval-freq` and `--save-freq` by the configured number of training envs (`n_envs`) before creating callbacks.
- Treat `--device cuda` and service integrations as optional. Use `--device cpu` for portable CPU smoke tests.

## Boundaries and routes

- Deep YAML/Python config grammar, `--conf-file`, and complex `--hyperparams` values: route to `../config-hyperparams/SKILL.md`.
- Optuna tuning via `-optimize` / `--optimize-hyperparameters`: route to `../tuning-optimization/SKILL.md`.
- Loading/enjoying models, best/checkpoint/latest selection, video, and artifact inspection after training: route to `../evaluation-and-artifacts/SKILL.md` and `../integrations-hub-tracking/SKILL.md` as appropriate.
- Wrappers, callbacks, custom Gymnasium registration modules, and custom algorithm/component imports: route to `../custom-components/SKILL.md`.
- Plotting or benchmark interpretation: route to `../plotting-benchmarking/SKILL.md`.

## Minimal safe command pattern

```bash
python -m rl_zoo3.train --algo ppo --env CartPole-v1 --n-timesteps 1000 \
  --log-folder ./runs/rl-zoo --eval-freq 500 --save-freq 500 \
  --seed 123 --device cpu --progress
```

Use the command builder to produce this pattern safely:

```bash
python scripts/train_command_builder.py \
  --algo ppo --env CartPole-v1 --n-timesteps 1000 --log-folder ./runs/rl-zoo \
  --eval-freq 500 --save-freq 500 --seed 123 --device cpu --progress
```
