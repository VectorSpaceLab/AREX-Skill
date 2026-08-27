---
name: tasks-datasets-and-envs
description: "Use Habitat-Lab task, dataset, environment, Gym, and vectorized
  environment workflows safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Habitat-Lab Tasks, Datasets, and Environments

Use this sub-skill when the user needs to load Habitat task configs, inspect dataset and episode layout, construct `habitat.Env` or `habitat.RLEnv`, wrap tasks as Gym environments, use `VectorEnv`/`ThreadedVectorEnv`, or diagnose environment/data/config smoke-check failures.

## Read First

- [API reference](references/api-reference.md): verified constructor signatures, object relationships, lifecycle calls, Gym conversion behavior, and vectorized-env methods.
- [Workflows](references/workflows.md): config-to-env recipes, Gym wrappers, VectorEnv debug mode, navigation/rearrangement/VLN/EQA patterns, validation steps, and skip conditions.
- [Data formats](references/data-formats.md): scene/task dataset layouts, `Episode` fields, task-specific episode extensions, DATASETS-derived paths, and tiny-fixture guidance.
- [Troubleshooting](references/troubleshooting.md): missing assets, Habitat-Sim/graphics failures, VectorEnv hidden errors, action/observation-space mismatches, Gym wrapper issues, and backend failures.

## Bundled Script

Use [scripts/habitat_config_smoke.py](scripts/habitat_config_smoke.py) for safe config inspection. It loads a Habitat config, applies Hydra overrides, prints environment/task/simulator/dataset summaries, and only attempts dataset construction when `--make-dataset` is explicitly provided. It never downloads data and never creates a simulator by default.

## Boundary Reminders

- For install, editable package setup, Hydra search path basics, Habitat-Sim installation, CUDA/graphics setup, and dependency repair, route to `setup-and-configuration`.
- For RL training, evaluator loops, checkpoints, policies, and Habitat-Baselines trainer configuration, route to `baselines-training-and-evaluation`.
- For real-time HITL apps, interactive keyboard/gamepad/VR control, and app services, route to `hitl-apps-and-interaction`.
- For registering custom sensors, actions, tasks, measures, datasets, or simulators, route to `extension-patterns`.
