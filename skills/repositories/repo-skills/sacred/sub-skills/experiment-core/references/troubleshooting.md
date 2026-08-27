# Sacred experiment-core troubleshooting

Use this guide for core experiment construction and run-time failures. For observer backend storage, full CLI grammar, or randomness/capture-mode issues, route to the sibling sub-skill that owns that area.

| Symptom | Likely cause | Fix |
|---|---|---|
| Code below `@ex.automain` is not registered before the run starts. | `@ex.automain` immediately runs the command-line interface when the decorated function is defined in `__main__`. | Move `@ex.automain` to the end of the executable file, or change to `@ex.main` and call `ex.run_commandline()` under `if __name__ == "__main__":`. |
| Runtime error says Sacred cannot use automain in interactive mode. | `@ex.automain` was used from stdin/IPython/Jupyter-like context. | Use `Experiment("name", interactive=True)`, decorate with `@ex.main`, and call `ex.run(...)` explicitly. |
| Runtime error says no main file was found or asks whether this is interactive mode. | Experiment/ingredient was defined dynamically with `interactive=False`, so Sacred cannot store source reliably. | For notebooks/REPL/dynamic smoke scripts, pass `interactive=True` and an explicit experiment name. For normal scripts, define the experiment in a real module file. |
| Runtime error says name is required in interactive mode. | `Experiment(name=None, interactive=True)` was used. | Provide a stable name: `Experiment("my_experiment", interactive=True)`. |
| `ex.run()` raises “No command found to be run”. | No default command has been registered. | Add one `@ex.main`/`@ex.automain`, or pass `command_name="..."` for a registered command. |
| Command not found. | The command name does not match the registered root command or ingredient dotted command. | Check `dict(ex.gather_commands())`. Root commands use function names; ingredient commands use `ingredient_path.function_name`. |
| Missing argument/config error from a captured function. | A required parameter was neither explicitly passed nor present in the visible config/prefix subtree. | Add the config value, pass the argument explicitly, provide a Python default, or adjust `prefix=` so the function sees the intended subtree. |
| A config update is rejected as unused/added. | Sacred rejects updates that are not in config and not consumed by captured functions. Prefixes are considered when deciding whether an update is consumed. | Add the key to a config scope/dict, add a captured function parameter that legitimately consumes it, correct the prefix, or remove the typo. |
| A helper receives an unexpected value without being passed one. | Accidental config injection by matching parameter name. Config values override Python defaults for missing parameters. | Rename generic parameters, pass explicit values, or decorate with `@ex.capture(prefix="subtree")` to narrow the injection namespace. |
| Attempting to edit `_config` or nested config containers raises a Sacred error. | Captured-function config is read-only by default so changes are not silently untracked. | Copy before mutation: `mutable = dict(_config["section"])` or return derived values through `Run.info`, artifacts, or normal function results. Do not disable read-only config unless you own the reproducibility trade-off. |
| `open_resource`, `add_resource`, `add_artifact`, or `log_scalar` asserts/fails outside a run. | Experiment-level methods require `current_run` and can only be called while a command is active. | Move the call inside `@ex.main`, `@ex.command`, a captured helper called by the run, or use the captured `_run` object. |
| Resource or artifact file path error. | The file does not exist at the time it is opened/registered, or the process working directory differs from the assumed relative path. | Create produced artifacts before `add_artifact`. Resolve resources relative to a known project/config directory. Prefer `pathlib.Path` and validate `path.exists()` before registering. |
| Artifact has an unexpected display name. | `Run.add_artifact(..., name=None)` defaults to the basename of the file. | Pass `name="desired-name.ext"` explicitly when observer-visible naming matters. |
| Scalar metrics do not appear in storage. | Metrics are logged in the run but only supported by specific observers, and observer flushing/heartbeat behavior belongs to observer storage. | Verify a compatible observer in the observer/logging layer. In core code, call `_run.log_scalar("metric.name", value, step)` or `ex.log_scalar(...)` during a run. |
| Warning: “No observers have been added to this run”. | No observer is attached and the run is neither debug nor unobserved. The experiment still executes, but run data will not be persisted by observers. | Attach an observer in the observer/logging layer for persistent tracking, or intentionally mark helper commands `unobserved=True` / run with unobserved options when persistence is not desired. |
| Config hook registration fails. | `config_hook` function has the wrong signature. | Use exactly `def hook(config, command_name, logger): ...` and return a dictionary. |
| A `Run` cannot be started twice. | `Run.__call__` was invoked after the run already started. | Use `ex.run(...)` again to create a fresh `Run` for each execution. |

## Diagnostic snippets

List registered commands without running them:

```python
commands = dict(ex.gather_commands())
print(sorted(commands))
```

Make a dynamic/notebook-safe experiment:

```python
ex = Experiment("debug_session", interactive=True, save_git_info=False)

@ex.main
def main():
    return "ok"

run = ex.run()
```

Use explicit arguments to test whether a failure is injection-related:

```python
@ex.capture
def build_path(root, filename):
    return root / filename

# If this works but build_path() fails, inspect config keys/prefixes.
build_path(root=Path("."), filename="data.txt")
```
