---
name: training-scripts
description: "Choose, run, inspect, and safely adapt CleanRL single-file training scripts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# CleanRL Training Scripts

Use this sub-skill when the task is to choose a CleanRL algorithm script, inspect its CLI, build a safe local training smoke command, or adapt script flags for a specific RL environment. CleanRL training entry points are intentionally single-file scripts under `cleanrl/`, plus specialized nested variants for PPO-TrXL and IsaacGym.

## Route the Request

- For a local CPU smoke run on classic control, prefer `ppo.py`, `dqn.py`, or `c51.py`; see [algorithm-catalog.md](references/algorithm-catalog.md) and [cli-and-runs.md](references/cli-and-runs.md).
- For Atari, EnvPool, Procgen, PettingZoo, MuJoCo, JAX, PPO-TrXL, RND, PQN, QDagger, RPO, or IsaacGym, check the optional dependency and backend matrix before recommending execution.
- For `--save-model`, `--upload-model`, model artifacts, or Hugging Face evaluation, route details to [`../evaluation-and-sharing/SKILL.md`](../evaluation-and-sharing/SKILL.md) after selecting the training script.
- For benchmark sweeps, W&B report reproduction, cloud jobs, Docker, Slurm, or tuning, route to [`../experiment-operations/SKILL.md`](../experiment-operations/SKILL.md).
- For editing algorithm source, adding flags, docs/tests, or contribution checks, route to [`../repo-maintenance/SKILL.md`](../repo-maintenance/SKILL.md).

## First Checks

1. Confirm Python satisfies CleanRL's supported range: `>=3.8,<3.11`.
2. Identify the environment family: classic control, Atari, continuous control, EnvPool, Procgen, PettingZoo, PPO-TrXL, or IsaacGym.
3. Use `scripts/inspect_cleanrl_script.py` to inspect a script's `Args` defaults without importing optional backends.
4. Use `scripts/build_tiny_run_command.py` to generate a conservative smoke command; do not run long defaults by accident.
5. Keep `--track`, `--capture-video`, `--save-model`, and `--upload-model` disabled unless the user explicitly wants tracking, video, local model files, or network upload.

## Safe Defaults

- Use CPU-first commands for smoke tests: add `--no-cuda` for tyro scripts or `--cuda False` for the argparse PettingZoo script.
- For PPO-style scripts, reduce `--num-envs`, `--num-steps`, and `--total-timesteps` together so at least one rollout/update can complete.
- For replay-buffer scripts such as DQN, C51, Rainbow, TD3, and DDPG, keep `--learning-starts < --total-timesteps` and `--batch-size <= --buffer-size` when forcing tiny runs.
- Treat Atari ROMs, JAX, EnvPool, MuJoCo, DM Control, Procgen, PettingZoo, memory-gym, and IsaacGym as optional backends; explain the extra before prescribing commands.
- Keep benchmark shell launchers reference-only for training-script work; use experiment-operations for matrices or long-running reproduction.

## Bundled Helpers

- `python sub-skills/training-scripts/scripts/inspect_cleanrl_script.py cleanrl/ppo.py --format markdown`
- `python sub-skills/training-scripts/scripts/build_tiny_run_command.py classic-ppo`
- `python sub-skills/training-scripts/scripts/build_tiny_run_command.py --list`

## When Unsure

- Inspect the script's defaults before guessing flag names; most current scripts use tyro dataclasses, while `ppo_pettingzoo_ma_atari.py` uses argparse with an underscore `--capture_video` flag.
- Prefer help checks (`python cleanrl/<script>.py --help`) before execution when optional extras may be missing.
- If a tiny run fails from missing environment packages, route to [troubleshooting.md](references/troubleshooting.md) rather than broad-installing every extra.
