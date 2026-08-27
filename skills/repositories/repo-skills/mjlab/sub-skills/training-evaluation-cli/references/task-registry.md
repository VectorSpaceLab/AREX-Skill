# Task registry

The live task registry is the authoritative source for mjlab task IDs,
environment configs, play configs, runner classes, and task-family metadata.
It is populated when the package imports registered task entry points, so
registry discovery should always use the installed package rather than source
files.

## Registry API

- `register_mjlab_task(task_id, env_cfg, play_env_cfg, rl_cfg, runner_cls=None)`
  registers one task under a unique ID.
- `list_tasks()` returns the live registry as a sorted list of task IDs.
- `load_env_cfg(task_name, play=False)` returns a deep copy of the training or
  play environment config.
- `load_rl_cfg(task_name)` returns a deep copy of the runner config.
- `load_runner_cls(task_name)` returns the custom runner class or `None`.

## Registry rules

- Task IDs are unique.
- `load_*` returns deep copies, so the caller can inspect or mutate them safely.
- `play=True` should return the evaluation variant for playback flows.
- If task package loading prints warnings, treat registry discovery as partial
  until the import problem is resolved.

## Naming and discovery

mjlab task IDs commonly follow the pattern `Mjlab-{Category}-{Terrain}-{Robot}`.
The registry is the source of truth for the CLI task list, but individual task
families can still provide custom runners and play-time overrides.

## Safe discovery commands

Helper examples assume the current directory is this sub-skill directory, or that
`scripts/...` has been replaced with the resolved bundled helper path.

- `uv run list-envs`
- `uv run list-envs --keyword Velocity`
- `uv run python scripts/check_task_registry.py --keyword velocity`
- `uv run python scripts/check_task_registry.py --task Mjlab-Cartpole-Balance --json`

## What the bundled checker reports

The bundled checker prints or serializes a concise live summary:

- task ID
- runner class
- training and play env class names
- experiment name
- scene environment count
- active action, observation, reward, command, and sensor keys
- key play-mode fields such as episode length and termination set

Use this page when you only need to know whether a task exists, what runner it
uses, and what the installed package exposes at runtime.
