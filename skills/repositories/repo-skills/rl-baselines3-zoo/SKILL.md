---
name: rl-baselines3-zoo
description: "Operate RL Baselines3 Zoo package and CLI workflows for
  Stable-Baselines3 reinforcement-learning experiments."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# RL Baselines3 Zoo

Use this repo skill when the task involves RL Baselines3 Zoo / `rl_zoo3`: training Stable-Baselines3 or SB3-Contrib agents from Zoo hyperparameter files, evaluating saved agents, tuning with Optuna, using Gymnasium env IDs and wrappers/callbacks, plotting Zoo logs, or managing Hub/W&B/video integrations.

## Start here

1. Confirm the package and command surface with [install and environment guidance](references/install-and-environment.md).
2. Use [CLI command map](references/cli-command-map.md) to choose the correct command family.
3. If an error occurs before a workflow is clear, use [cross-cutting troubleshooting](references/troubleshooting.md).
4. If working against a checkout or a newer package version, compare against [repository provenance](references/repo-provenance.md).
5. Use [router metadata](references/repo-routing-metadata.json) only for managed repo-skill routing context.

## Minimal package checks

```bash
python - <<'PY'
import rl_zoo3
print(rl_zoo3.__version__)
print(sorted(rl_zoo3.ALGOS))
PY

python -m rl_zoo3.train --help
python -m rl_zoo3.enjoy --help
```

For a bundled, non-mutating check:

```bash
python scripts/check_rl_zoo3_install.py --check-plots
```

## Route by task

| User task | Read |
| --- | --- |
| Build, run, resume, or debug a training command; choose `--algo`, `--env`, `--log-folder`, eval/checkpoint/replay flags, device, `--gym-packages`, or W&B route flags | [training-cli](sub-skills/training-cli/SKILL.md) |
| Read, write, or validate RL Zoo YAML/Python hyperparameter configs, `default`/`atari` entries, `normalize`, wrappers/callback config, `--conf-file`, or `--hyperparams` quoting | [config-hyperparams](sub-skills/config-hyperparams/SKILL.md) |
| Run or diagnose Optuna HPO: `-optimize`, samplers/pruners, storage/study reuse, `--trial-id`, distributed workers, HPO report artifacts | [tuning-optimization](sub-skills/tuning-optimization/SKILL.md) |
| Load/evaluate an existing local model with `enjoy`, choose final/best/checkpoint/latest, inspect log/model folders, use no-render evaluation, or plan local benchmark smoke checks | [evaluation-and-artifacts](sub-skills/evaluation-and-artifacts/SKILL.md) |
| Register custom Gymnasium envs, validate wrapper/callback/policy import strings, use built-in wrappers/callbacks, patch custom algorithms/SBX | [custom-components](sub-skills/custom-components/SKILL.md) |
| Plan Hugging Face Hub download/upload/model-card commands, W&B tracking, `record_video`, `record_training`, display/ffmpeg/gif requirements | [integrations-hub-tracking](sub-skills/integrations-hub-tracking/SKILL.md) |
| Plot monitor/evaluation curves, build `all_plots` / `plot_from_file` commands, run bounded benchmark output flows, troubleshoot `rliable`/plot deps | [plotting-benchmarking](sub-skills/plotting-benchmarking/SKILL.md) |

## Command stance

- Prefer installed-package module commands for train/evaluate:
  ```bash
  python -m rl_zoo3.train --algo ppo --env CartPole-v1 --n-timesteps 1000
  python -m rl_zoo3.enjoy --algo ppo --env CartPole-v1 -f logs --exp-id 0 --no-render
  ```
- Use `rl_zoo3 train` / `rl_zoo3 enjoy` only when the console router imports cleanly. The console router imports plotting modules, so base installs can fail unless plot dependencies are installed.
- Use helper scripts in this skill to build commands, check imports, inspect local layouts, or validate config/component shapes. They do not train, upload, download, render, or call live services unless the helper explicitly says it only reads local files.

## Bundled root scripts

- [scripts/check_rl_zoo3_install.py](scripts/check_rl_zoo3_install.py): import/version/optional plotting/CUDA probe; safe and non-mutating.
- [scripts/build_rl_zoo3_command.py](scripts/build_rl_zoo3_command.py): quick command router that prints an installed-package command and the owning sub-skill. Use sub-skill helpers for deeper validation.

Example:

```bash
python scripts/build_rl_zoo3_command.py train -- --algo ppo --env CartPole-v1 --n-timesteps 1000
```

## Optional dependencies and backends

- CPU is enough for CartPole/Pendulum smoke workflows, static config validation, command construction, local artifact inspection, and most troubleshooting.
- Optional simulator families (Atari, MuJoCo, Box2D, PyBullet, highway, Minigrid, robotics, custom envs) require their own packages and sometimes data/ROMs.
- CUDA or another accelerator is optional unless the user specifically asks for accelerator training. Validate PyTorch device availability before using `--device cuda` in a long run.
- Hub, W&B, video, and plot workflows may require network, credentials, display/offscreen rendering, `ffmpeg`, or plot extras; route to the owning sub-skill first.

## Do not use this skill for

- Raw Stable-Baselines3 algorithm API questions that do not involve RL Zoo commands, hyperparams, artifact layout, or scripts.
- Generic Gymnasium environment authoring unless the env must be registered/used through RL Zoo.
- LLM RLHF/post-training workflows unrelated to Gymnasium/SB3 agents.
