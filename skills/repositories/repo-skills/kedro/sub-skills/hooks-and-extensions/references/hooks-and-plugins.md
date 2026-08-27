# Hooks And Plugins

Use this reference to add behavior around Kedro lifecycle events, build installable plugins, debug entry point discovery, or extend the Kedro CLI lifecycle.

## Hook Model

Kedro hooks are Pluggy implementations. The public implementation marker is:

```python
from kedro.framework.hooks import hook_impl
```

Define hook methods with the same name as the Kedro hook spec. You may declare only the arguments you need, but each declared argument must be named exactly like the spec argument. Do not give hook arguments default values.

```python
# src/<package_name>/hooks.py
import logging
from typing import Any

from kedro.framework.hooks import hook_impl


class ProjectHooks:
    @hook_impl
    def before_pipeline_run(self, run_params: dict[str, Any]) -> None:
        logging.getLogger(__name__).info("Run parameters: %s", sorted(run_params))

    @hook_impl
    def after_catalog_created(self, catalog, parameters: dict[str, Any]) -> None:
        required = {"raw_data", "parameters"}
        missing = required - set(catalog.list())
        if missing:
            raise ValueError(f"Catalog is missing required entries: {sorted(missing)}")
```

Register hook instances in project settings:

```python
# src/<package_name>/settings.py
from <package_name>.hooks import ProjectHooks

HOOKS = (ProjectHooks(),)
```

Kedro raises a `TypeError` if a hook class is registered instead of an instance; `HOOKS = (ProjectHooks,)` is wrong and `HOOKS = (ProjectHooks(),)` is correct.

## Hook Specifications

| Hook | Available arguments | Typical use |
| --- | --- | --- |
| `after_context_created` | `context` | Capture `context.env`, mutate config loader credentials, inspect project context after creation. |
| `after_catalog_created` | `catalog`, `conf_catalog`, `conf_creds`, `parameters`, `save_version`, `load_versions` | Validate catalog entries, inspect dataset metadata, add catalog-level observability. |
| `before_pipeline_run` | `run_params`, `pipeline`, `catalog` | Log run selections, validate pipeline/catalog before execution, start tracking runs. |
| `after_pipeline_run` | `run_params`, `run_result`, `pipeline`, `catalog` | Emit summaries, close tracking runs, inspect outputs. |
| `on_pipeline_error` | `error`, `run_params`, `pipeline`, `catalog` | Report pipeline-level failures or launch debugging in interactive contexts. |
| `before_node_run` | `node`, `catalog`, `inputs`, `is_async`, `run_id` | Validate or mutate node inputs, log node start, add retry/decorator behavior. |
| `after_node_run` | `node`, `catalog`, `inputs`, `outputs`, `is_async`, `run_id` | Validate outputs, emit metrics, record lineage. |
| `on_node_error` | `error`, `node`, `catalog`, `inputs`, `is_async`, `run_id` | Capture node failure context, start post-mortem debugging, notify observers. |
| `before_dataset_loaded` | `dataset_name`, `node` | Log load start, collect timing, enforce load policies. |
| `after_dataset_loaded` | `dataset_name`, `data`, `node` | Validate loaded data, record memory or row counts. |
| `before_dataset_saved` | `dataset_name`, `data`, `node` | Validate save payloads, reject unsafe outputs. |
| `after_dataset_saved` | `dataset_name`, `data`, `node` | Emit save metrics, confirm writes. |

`before_node_run` may return `None` or a dictionary mapping existing node input dataset names to replacement values. Returning any other object raises a `TypeError` similar to `'before_node_run' must return either None or a dictionary mapping dataset names to updated values`. The returned keys must match inputs expected by the node.

## Safe Project Hook Template

This template supports a common verification case: validate catalog state and log run parameters without default hook arguments.

```python
# src/<package_name>/hooks.py
import logging
from typing import Any

from kedro.framework.hooks import hook_impl


class ValidationAndLoggingHooks:
    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)

    @hook_impl
    def after_catalog_created(self, catalog) -> None:
        dataset_names = set(catalog.list())
        required = {"raw_data", "parameters"}
        missing = required - dataset_names
        if missing:
            raise ValueError(f"Missing required catalog entries: {sorted(missing)}")
        self._logger.info("Catalog has %d entries", len(dataset_names))

    @hook_impl
    def before_pipeline_run(self, run_params: dict[str, Any]) -> None:
        safe_keys = [key for key in run_params if key not in {"runtime_params"}]
        self._logger.info("Kedro run metadata keys: %s", sorted(safe_keys))
```

```python
# src/<package_name>/settings.py
from <package_name>.hooks import ValidationAndLoggingHooks

HOOKS = (ValidationAndLoggingHooks(),)
```

Do not write `def before_pipeline_run(self, run_params: dict[str, Any] = {})`; Pluggy can keep the default value instead of Kedro's runtime value.

## Ordering And Runner Caveats

- Project hooks in `HOOKS = (hook_a, hook_b)` run in last-in-first-out order for the same hook spec, so `hook_b` is called before `hook_a`.
- Auto-discovered plugin hooks are registered from `kedro.hooks`; do not rely on a stable cross-plugin order.
- Use `@hook_impl(tryfirst=True)` or `@hook_impl(trylast=True)` only for unavoidable ordering needs.
- `ParallelRunner` does not execute node and dataset hooks in worker processes. Context, catalog, and pipeline hooks run in the main process, but choose `SequentialRunner` or `ThreadRunner` when `before_node_run`, `after_node_run`, `before_dataset_loaded`, or `after_dataset_saved` behavior is required.
- Keep hook state small. Hook instances live for a session, so attributes set in `after_context_created` can be read later, but mutable shared state can surprise repeated or service-style runs.

## Plugin Entry Points

Kedro plugins are separate Python packages discovered with Python entry points. Use `pyproject.toml` entry point tables.

### Project Commands

Expose reusable project commands with `kedro.project_commands`. These commands are available only inside a Kedro project.

```toml
[project.entry-points."kedro.project_commands"]
myplugin = "myplugin.commands:commands"
```

The target should be a `click.Group`. Kedro merges the group into the main CLI. Group-level callback processing and group options can be lost during merge, so put important logic on subcommands rather than relying on the group callback.

### Global Commands

Expose commands that work outside projects with `kedro.global_commands`.

```toml
[project.entry-points."kedro.global_commands"]
myplugin = "myplugin.global_commands:commands"
```

### Init Hooks

Run plugin initialization before Kedro starts with `kedro.init`. The target should be a no-argument function; define it as accepting `**kwargs` for future compatibility.

```toml
[project.entry-points."kedro.init"]
myplugin = "myplugin.init:init"
```

### Runtime Hooks

Auto-register hook implementations with `kedro.hooks`. The entry point must expose an instance, not a class.

```python
# myplugin/plugin.py
from kedro.framework.hooks import hook_impl


class MyHooks:
    @hook_impl
    def after_catalog_created(self, catalog) -> None:
        catalog.list()


hooks = MyHooks()
```

```toml
[project.entry-points."kedro.hooks"]
myplugin = "myplugin.plugin:hooks"
```

A project can disable selected installed plugin hooks by distribution name:

```python
# src/<package_name>/settings.py
DISABLE_HOOKS_FOR_PLUGINS = ("myplugin",)
```

### CLI Hooks

CLI hooks wrap Kedro command execution. Use `cli_hook_impl`, not `hook_impl`.

```python
# myplugin/cli_hooks.py
import logging

from kedro.framework.cli.hooks import cli_hook_impl


class MyCLIHooks:
    @cli_hook_impl
    def before_command_run(self, project_metadata, command_args: list[str]) -> None:
        logging.getLogger(__name__).info("Running kedro %s", " ".join(command_args))

    @cli_hook_impl
    def after_command_run(self, project_metadata, command_args: list[str], exit_code: int) -> None:
        logging.getLogger(__name__).info("kedro %s exited %s", " ".join(command_args), exit_code)


cli_hooks = MyCLIHooks()
```

```toml
[project.entry-points."kedro.cli_hooks"]
myplugin = "myplugin.cli_hooks:cli_hooks"
```

`before_command_run` receives `project_metadata` and the parsed command arguments. `after_command_run` also receives the Click exit code.

### IPython Line Magics

Plugins can provide line magics with `kedro.line_magic`. Kedro loads these when `%reload_kedro` runs in an IPython/Jupyter context.

```toml
[project.entry-points."kedro.line_magic"]
myplugin_magic = "myplugin.magics:my_line_magic"
```

## Command Precedence

For project commands, Kedro command resolution is:

1. Built-in project commands such as `run`, `catalog`, `pipeline`, `registry`, `ipython`, `jupyter`, `package`, and `server`.
2. Installed plugin project commands from `kedro.project_commands`, which can override built-ins.
3. Project-specific `src/<package_name>/cli.py`, which can override plugin and built-in commands.

For global commands, installed plugin global commands are merged with built-in global commands. Kedro's CLI note states that plugin commands can take precedence when they conflict with built-ins.

Use `KEDRO_DISABLE_TELEMETRY=1 kedro info` to list installed plugins and their Kedro entry point groups without intentionally sending telemetry. Expected plugin output looks like `<plugin>: <version> (entry points:hooks,project,...)` when plugins are installed.

## Debug Checklist

- Check the plugin package is installed in the same Python environment as `kedro`.
- Run `kedro info` and confirm the plugin appears with the expected entry point group.
- Verify `pyproject.toml` entry point group spelling exactly: `kedro.hooks`, `kedro.cli_hooks`, `kedro.project_commands`, `kedro.global_commands`, `kedro.init`, or `kedro.line_magic`.
- Verify hook entry points expose instances, not classes.
- Verify project hooks are in `settings.py` as `HOOKS = (HookClass(),)` and that the project package is importable.
- If a hook is silent under `ParallelRunner`, retry with `SequentialRunner` or `ThreadRunner` before changing hook code.
- If a plugin hook is not wanted, add the plugin distribution name to `DISABLE_HOOKS_FOR_PLUGINS`; this does not disable CLI command entry points.
