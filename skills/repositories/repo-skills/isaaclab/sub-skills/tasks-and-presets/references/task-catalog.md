# Task Catalog and Config Loading

## Task registration

`isaaclab_tasks` registers Isaac Lab Gymnasium environments. Task IDs commonly start with `Isaac-`. Importing `isaaclab_tasks` is enough to populate the registry for the core task package; importing `isaaclab_tasks_experimental` adds experimental tasks when the package is installed.

## Listing environments

Use the bundled `scripts/list_task_presets.py` helper when you need a self-contained task listing:

```bash
python scripts/list_task_presets.py --keyword Cartpole
python scripts/list_task_presets.py --keyword Cartpole --show-presets
```

The helper prints a table or JSON depending on `--format`. `--show-presets` asks Isaac Lab to load each matching env config and enumerate typed preset groups.

## Config entry points

Task registry entries usually carry an `env_cfg_entry_point` kwarg. `load_cfg_from_registry(task_name, entry_point_key)` resolves that entry point and returns either a YAML dictionary or an instantiated config class.

Useful calls:

- `load_cfg_from_registry(task_name, "env_cfg_entry_point")`
- `parse_env_cfg(task_name, device="cuda:0", num_envs=None, use_fabric=None)`
- `get_checkpoint_path(log_path, run_dir=".*", checkpoint=".*", preferred_checkpoint=None)`

## Safe config-loading contract

Environment configs are pure data and should be constructable before a simulator is launched. Config loading should not import these forbidden runtime modules:

- `pxr`
- `omni`
- `carb`
- `isaacsim`
- `scipy`

If a config import pulls in one of those modules, move the runtime import behind a function boundary, use lazy package exports, or store callable references as import strings that are resolved only after launch.

## Preset discovery signal

For a known task, preset enumeration returns groups like:

- `physics: newton_kamino, newton_mjwarp, ovphysx, physx`
- `renderer: newton_renderer, isaacsim_rtx_renderer`
- `domain: rgb, depth, albedo`

The exact groups depend on the task config. Treat missing groups as task-specific rather than global absence.

## Maintainer checks

Useful safe checks from the source evidence:

- Preset CLI unit tests confirm that `setup_preset_cli` returns a verbatim remainder and does not mutate `sys.argv`.
- Config-loading tests confirm that env configs do not import forbidden simulator/runtime modules before launch.
- Unified RL train/play tests confirm that typed preset tokens reach the Isaac Lab resolver rather than raw Hydra struct checks.
