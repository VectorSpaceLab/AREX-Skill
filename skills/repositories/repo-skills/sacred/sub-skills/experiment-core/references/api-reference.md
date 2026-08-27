# Sacred experiment-core API reference

Verified target: Sacred 0.8.7. This reference covers core construction and run APIs only. Observer storage backends, detailed CLI update grammar, and randomness/capture policy are intentionally outside this sub-skill.

## Core constructors

| API | Signature | Use |
|---|---|---|
| `Experiment` | `Experiment(name=None, ingredients=(), interactive=False, base_dir=None, additional_host_info=None, additional_cli_options=None, save_git_info=True)` | Create the root experiment. `name` defaults to the filename outside interactive mode. In interactive mode, provide `name` and set `interactive=True`. |
| `Ingredient` | `Ingredient(path, ingredients=(), interactive=False, _caller_globals=None, base_dir=None, save_git_info=True)` | Create a reusable configured module. `path` is the config/command namespace and may use dotted notation for explicit nesting. |
| `FileStorageObserver` | `FileStorageObserver(basedir, resource_dir=None, source_dir=None, template=None, priority=20, copy_artifacts=True, copy_sources=True)` | Mentioned here only because core runs often attach observers; storage behavior belongs to `observers-and-logging`. |

Constructor notes:

- `Experiment` is an `Ingredient` subclass. It inherits config, capture, command, hook, named-config, and ingredient traversal behavior.
- If `Experiment(name=None, interactive=True)` is used, Sacred raises because a name is required in interactive mode.
- If an experiment or ingredient is defined where no main file can be found and `interactive=False`, Sacred raises an interactive-mode safeguard error.
- `save_git_info=True` records git metadata for source files when GitPython support is available; use `save_git_info=False` for tiny temporary smoke tests that do not need source provenance.

## Experiment methods

| API | Signature | Behavior |
|---|---|---|
| `main` | `Experiment.main(function)` | Decorator that registers the default command. The decorated function is captured. |
| `automain` | `Experiment.automain(function)` | Decorator that registers the default command and runs `run_commandline()` when the function's module is `__main__`. Must be last in executable scripts. Rejects stdin/IPython automain use. |
| `run` | `Experiment.run(command_name=None, config_updates=None, named_configs=(), info=None, meta_info=None, options=None)` | Creates a `Run`, executes it, and returns the finished `Run`. `command_name=None` uses the default command. |
| `run_commandline` | `Experiment.run_commandline(argv=None)` | Parses a Sacred command-line argument vector and runs the selected command. If `argv` is omitted, uses `sys.argv`. |
| `open_resource` | `Experiment.open_resource(filename, mode="r")` | During a run, report a consumed file to observers and return an open file object. Asserts that a run is active. |
| `add_resource` | `Experiment.add_resource(filename)` | During a run, report a consumed file to observers without opening it. Asserts that a run is active. |
| `add_artifact` | `Experiment.add_artifact(filename, name=None, metadata=None, content_type=None)` | During a run, report a produced file. `name` defaults to the artifact filename when delegated to `Run`. |
| `log_scalar` | `Experiment.log_scalar(name, value, step=None)` | During a run, log a numeric scalar metric. If `step` is omitted, Sacred maintains an internal counter per metric name. |
| `info` | `Experiment.info` property | Shortcut to `current_run.info`; only meaningful during a run. |
| `get_default_options` | `Experiment.get_default_options()` | Returns default option keys such as Sacred CLI flags; useful before passing `options` to `run`. |

`run(...)` return object expectations:

- On success: `run.status == "COMPLETED"`, `run.result` contains the main/command return value, and `stop_time` is populated.
- On queue-only runs: `status == "QUEUED"` and no command body is executed.
- On failure: `status == "FAILED"`, `fail_trace` is populated, observers receive failure events, and the original exception is re-raised.
- On interrupts: `status` is `"INTERRUPTED"` or a custom Sacred interrupt status, and the interrupt is re-raised.

## Ingredient methods inherited by Experiment

| API | Signature | Behavior |
|---|---|---|
| `capture` | `Ingredient.capture(function=None, prefix=None)` | Decorator that fills missing function arguments from the active config. Optional `prefix` scopes lookup to a config subtree. |
| `command` | `Ingredient.command(function=None, prefix=None, unobserved=False)` | Decorator that registers a command and also captures the function. `unobserved=True` suppresses observer use for that command. |
| `config` | `Ingredient.config(function)` | Decorator that turns a function's JSON-serializable local variables into config entries. |
| `named_config` | `Ingredient.named_config(func)` | Decorator that registers a named configuration under the function name. |
| `add_config` | `Ingredient.add_config(cfg_or_file=None, **kw_conf)` | Add config from a dictionary, config file, or keyword arguments. Do not combine a positional config with keyword config. |
| `add_named_config` | `Ingredient.add_named_config(name, cfg_or_file=None, **kw_conf)` | Add a named config from a dictionary, file, or keyword arguments. |
| `pre_run_hook` | `Ingredient.pre_run_hook(func, prefix=None)` | Captured hook called just before command execution. |
| `post_run_hook` | `Ingredient.post_run_hook(func, prefix=None)` | Captured hook called just after command execution. |
| `config_hook` | `Ingredient.config_hook(func)` | Register a hook with exact signature `(config, command_name, logger)` that returns config updates. |
| `gather_commands` | `Ingredient.gather_commands()` | Traverse this ingredient and sub-ingredients, yielding dotted command names and functions. |
| `gather_named_configs` | `Ingredient.gather_named_configs()` | Traverse this ingredient and sub-ingredients, yielding dotted named-config names and config objects. |
| `add_source_file` | `Ingredient.add_source_file(filename)` | Add an extra source dependency. The file must exist. |
| `add_package_dependency` | `Ingredient.add_package_dependency(package_name, version)` | Add a package dependency with a PEP440-compatible version string. |

`add_config(...)` errors to expect:

- no dictionary/file and no keyword config: `ValueError` for empty config;
- dictionary/file plus keyword config: `ValueError`;
- unsupported type: `TypeError`;
- missing config file path: `OSError`.

## Run methods and attributes

| API | Signature | Behavior |
|---|---|---|
| `Run.__call__` | `run(*args)` | Start a not-yet-started run. A `Run` can only be started once. `Experiment.run(...)` calls this for you. |
| `Run.open_resource` | `Run.open_resource(filename, mode="r")` | Convert `filename` to an absolute path, emit a resource event, and return an open file object. |
| `Run.add_resource` | `Run.add_resource(filename)` | Convert `filename` to an absolute path and emit a resource event. |
| `Run.add_artifact` | `Run.add_artifact(filename, name=None, metadata=None, content_type=None)` | Convert `filename` to an absolute path and emit an artifact event. If `name is None`, uses the basename. |
| `Run.log_scalar` | `Run.log_scalar(metric_name, value, step=None)` | Record a scalar metric in the run metrics logger for observer heartbeat/final handling. |

Important `Run` attributes:

| Attribute | Meaning |
|---|---|
| `config` | Final run configuration. Treat nested config values as read-only inside captured functions. |
| `config_modifications` | Summary of added, modified, type-changed, and documented config entries. |
| `experiment_info` | Experiment metadata such as name, sources, dependencies, repositories, and mainfile. |
| `host_info` | Host metadata gathered for the run. |
| `info` | Custom mutable dictionary sent to observers; safe place for extra runtime metadata. |
| `meta_info` | Meta fields such as command, options, named configs, and caller-provided metadata. |
| `result` | Return value of the main function or command after completion. |
| `status` | Lifecycle status such as `RUNNING`, `COMPLETED`, `FAILED`, `INTERRUPTED`, or `QUEUED`. |
| `captured_out` | Captured stdout/stderr text according to capture settings. |
| `fail_trace` | Formatted traceback list when a run fails. |
| `observers` | Observer instances attached to this run, sorted by descending priority unless unobserved. |
| `unobserved` | If true, observer events are disabled for the run. |

## Captured argument semantics

For any captured function (`@ex.main`, `@ex.automain`, `@ex.command`, `@ing.command`, `@ex.capture`, `@ing.capture`, hooks):

| Parameter form | Source |
|---|---|
| Explicit positional/keyword argument | Highest priority. Always overrides config and defaults. |
| Name present in active config | Used for missing parameters and can override Python defaults. |
| Python default value | Used only when no explicit argument and no config value exist. |
| Missing required value | Raises an argument/config error. |
| Unexpected keyword or too many positional args | Raises normal call construction errors. |

Special argument names:

| Name | Injected value | Notes |
|---|---|---|
| `_run` | Current `Run` object | Use for `info`, direct artifact/resource/metric calls, and lifecycle state. |
| `_config` | Config visible to the captured function | Read-only in captured functions by default. |
| `_log` | Logger for that function | Use instead of creating ad-hoc print/logging behavior. |
| `_seed`, `_rnd` | Per-call randomness helpers | Owned by the reproducibility/capture layer. |

## Command names

- Experiment commands registered on the root experiment are addressed by function name, e.g. `train`.
- Ingredient commands are addressed by dotted path plus function name, e.g. `dataset.stats`.
- The default command is set by `@ex.main` or `@ex.automain`.
- Built-in helper commands such as printing configuration are registered as unobserved commands on the experiment.
