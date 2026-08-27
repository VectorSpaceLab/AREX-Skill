---
name: training-evaluation-cli
description: "Operate mjlab training, playback, export, registry, and motion-data CLIs."
metadata:
  disco-role: operating
  scenarios:
    - reinforcement-learning-workflows
    - embodied-ai-simulation
disable-model-invocation: true
license: Apache 2.0
---

# training-evaluation-cli

Use this sub-skill when the request is about installed mjlab command-line
workflows: task discovery, training, playback, export, debug viewing, motion
preprocessing, checkpoint selection, W&B handling, or bounded verification.

## Use this sub-skill for
- `list-envs` and task registry inspection
- `train`, `play`, `demo`, `export-scene`, and `viz-nan`
- RSL-RL runner config, checkpoint, and W&B resume handling
- motion imitation CSV validation before conversion
- safe help checks and other bounded smoke tests

## Route elsewhere
- Environment config or manager-term wiring: environment-configuration
- Scene/entity/simulation/export API details: scene-simulation-assets
- Action, reward, observation, and command choices: mdp-components
- Sensors, terrain, and domain randomization: perception-terrain-randomization

## Bundled references
- [Task registry](references/task-registry.md)
- [Training CLI](references/training-cli.md)
- [Play, export, and debug](references/play-export-debug.md)
- [Motion imitation data](references/motion-imitation-data.md)
- [Troubleshooting](references/troubleshooting.md)

## Bundled helpers
- [check_task_registry.py](scripts/check_task_registry.py)
- [validate_motion_csv_schema.py](scripts/validate_motion_csv_schema.py)

## Safe first checks
1. `uv run list-envs`
2. `uv run train <TASK> --help`
3. `uv run play <TASK> --help`
4. `uv run export-scene <TARGET> --help`
5. `uv run viz-nan --help`

Treat `demo`, cloud launchers, W&B downloads, and benchmark jobs as networked or
long-running unless the user explicitly asks for them.
