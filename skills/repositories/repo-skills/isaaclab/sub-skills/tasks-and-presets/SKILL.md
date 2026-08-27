---
name: tasks-and-presets
description: "Use tasks-and-presets for Isaac Lab task registration, preset
  selectors, environment discovery, and environment config parsing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Tasks and Presets

Use this sub-skill when the task is about Isaac Lab environment IDs, preset selectors, task config loading, or environment discovery.

## Route here for

- Listing available Isaac task IDs and their Gymnasium entry points.
- Understanding `physics=`, `renderer=`, and `presets=` selectors.
- Parsing task configs from the Gym registry.
- Reasoning about `PresetCfg`, `PresetTarget`, and Hydra preset resolution.
- Debugging preset-related parser or resolver errors.
- Checking that task config loading stays Kit-free before the simulator launches.

## Use other subskills for

- RL train/play wrappers and checkpoint playback: `../rl-training/SKILL.md`.
- Launching the simulation app itself: `../simulation-core/SKILL.md`.
- Asset and sensor catalog choices used inside a task config: `../assets-and-sensors/SKILL.md`.

## Working references

- `references/preset-system.md` explains the typed selector grammar and resolver behavior.
- `references/task-catalog.md` explains environment listing, config loading, and safe discovery checks.
- `references/troubleshooting.md` covers preset and config-loading failure modes.
- `scripts/list_task_presets.py` lists task IDs and optionally prints preset groups from an installed Isaac Lab environment.

## Acceptance checks

- Explain the selector grammar for the requested task.
- Identify the correct task or preset names for the requested environment.
- Preserve typed selector tokens verbatim until Hydra registration resolves them.
- Use the bundled helper to confirm the task registry or preset groups when needed.
