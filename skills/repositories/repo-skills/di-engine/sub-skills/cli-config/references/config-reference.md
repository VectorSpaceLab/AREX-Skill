# Config reference

DI-engine config files are Python modules, not plain YAML-only payloads. The
package loads them as importable objects and then compiles them into a runtime
`EasyDict`.

## Core objects

- `main_config`: the experiment settings used by the runtime.
- `create_config`: the object factory and type-routing settings.
- `system_config`: optional distributed/system settings for `dist` workflows.

## Core helpers

| Helper | Role |
| --- | --- |
| `read_config(path)` | load a Python config module and return `(main_config, create_config)` |
| `read_config_directly(path)` | load a Python config module and return the full module dictionary |
| `read_config_with_system(path)` | load `(main_config, create_config, system_config)` |
| `save_config(cfg, path, type_='py')` | write a Python or YAML config |
| `save_config_py(cfg, path)` | write a formatted Python config |
| `compile_config(...)` | merge user config, create config, and runtime defaults |
| `compile_config_parallel(...)` | compile distributed/system-aware configs |

## Typical shape

A representative config pair usually looks like this:

- `main_config.env`: env counts, stop values, replay path, manager settings.
- `main_config.policy`: model parameters, learn/collect/eval blocks, and
  replay-buffer settings.
- `create_config.env.type`: env registry key or adapter name.
- `create_config.env.import_names`: modules that register the env class.
- `create_config.env_manager.type`: env-manager backend.
- `create_config.policy.type`: policy identifier used by the factory.

## Compilation workflow

1. Load the Python config module.
2. Keep `main_config` and `create_config` in sync.
3. Call `compile_config` or `compile_config_parallel` before creating managers
   or policies.
4. Inspect the compiled `cfg` rather than assuming the source module already has
   all defaults filled in.

## Why this matters

Most DI-engine examples and scripts rely on compile-time merging for:

- default batch sizes and learning settings
- env manager selection
- policy factory selection
- replay buffer and collector defaults
- distributed runtime ports and placement

If a config file fails to compile, fix the Python module shape first instead of
trying to patch the runtime loop.
