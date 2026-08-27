---
name: rl-training
description: "Use rl-training for Isaac Lab unified train/play entrypoints, RL
  library selection, checkpoint playback, video capture, and typed preset
  selectors in RL workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Reinforcement Learning Training

Use this sub-skill when the task is about training, evaluating, or replaying agents with Isaac Lab's RL wrappers.

## Route here for

- Running the unified `train` and `play` entrypoints.
- Choosing an RL backend library: `rl_games`, `rsl_rl`, `sb3`, `skrl`, or the contributed `rlinf` path when relevant.
- Loading or locating checkpoints, last-run folders, and best-model files.
- Recording videos during evaluation runs.
- Using typed preset selectors in RL commands.
- Diagnosing wrapper, checkpoint, or dependency errors that happen before the environment launches.

## Use other subskills for

- Selector grammar, environment listing, and task discovery: `../tasks-and-presets/SKILL.md`.
- Simulation backend choice or camera/runtime startup: `../simulation-core/SKILL.md`.
- Data collection, teleoperation, or imitation learning: `../imitation-and-teleop/SKILL.md`.

## Working references

- `references/rl-library-matrix.md` describes the supported libraries and install extras.
- `references/train-and-play-workflows.md` describes the command flow, common arguments, and checkpoint patterns.
- `references/troubleshooting.md` covers dispatch and run-time failures.
- `scripts/inspect_rl_dispatch.py` prints safe command skeletons and library metadata.

## Acceptance checks

- Name the correct `--rl_library` value and wrapper command for the requested workflow.
- Preserve typed preset tokens until `setup_preset_cli` and Hydra consume them.
- Identify the expected checkpoint path or run-directory convention for the selected library.
- Call out when the requested library or export path needs optional dependencies that are not part of the core install.
