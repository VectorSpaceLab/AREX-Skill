# Workflow Overview

This repository revolves around one shared PPO implementation and three user-facing workflows: training, evaluation, and visualization.

## Routes

| Workflow | Sub-skill | What it does | Typical outputs |
| --- | --- | --- | --- |
| Training | `sub-skills/training/` | Starts a PPO run, chooses the environment preset, and resolves log/checkpoint paths. | `PPO_logs/<env>/...csv`, `PPO_preTrained/<env>/...pth` |
| Evaluation | `sub-skills/evaluation/` | Loads a pretrained checkpoint and runs rollout episodes or render checks. | Episode reward output and optional render frames |
| Visualization | `sub-skills/visualization/` | Plots reward logs and composes GIFs from saved frames. | `PPO_figs/<env>/...png`, `PPO_gifs/<env>/...gif` |

## Shared file layout

The native repository uses these directories and naming conventions:

- `PPO_preTrained/<env_name>/PPO_<env_name>_<random_seed>_<run_num>.pth`
- `PPO_logs/<env_name>/PPO_<env_name>_log_<run_num>.csv`
- `PPO_figs/<env_name>/PPO_<env_name>_fig_<fig_num>.png`
- `PPO_gif_images/<env_name>/<frame>.jpg`
- `PPO_gifs/<env_name>/PPO_<env_name>_gif_<gif_num>.gif`

## Recommended route selection

1. **Need a new run?** Start with training.
2. **Need to evaluate a saved policy?** Start with evaluation.
3. **Need plots or GIFs?** Start with visualization.
4. **Need to understand the PPO implementation itself?** Read the root API reference and `scripts/ppo_core.py`.

## Native workflow shape

- Training creates logs and checkpoints.
- Evaluation loads a checkpoint and reports episode rewards.
- Visualization reads training logs or saved frames and produces figures or GIFs.
- The notebook combines all three workflows plus optional headless-display setup for remote sessions.

## Why the routes are separate

The workflows share the same PPO class, but they differ in:

- dependency set,
- output files,
- safety profile,
- runtime length,
- and failure modes.

Keeping them separate makes the skill easier to use and easier to troubleshoot.
