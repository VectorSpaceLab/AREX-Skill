# Hooks And Extensions Troubleshooting

Use this reference when extension behavior is missing, import/entry point discovery fails, hooks fire in the wrong context, custom datasets fail catalog creation, custom commands conflict, or serving/deployment integrations fail.

## Triage Flow

1. Reproduce with a telemetry-safe command when using the CLI: `KEDRO_DISABLE_TELEMETRY=1 kedro --help` or `KEDRO_DISABLE_TELEMETRY=1 kedro info`.
2. Decide which extension surface is involved: project hook, plugin hook, CLI hook, project `cli.py`, plugin command, dataset class, runner, notebook magic, server, or platform plugin.
3. Confirm the extension package is importable in the same Python environment as `kedro`.
4. Check exact names: hook method names, hook argument names, entry point group names, Click command names, dataset class paths, and runner dotted paths.
5. Reduce to the smallest safe probe: import the object, instantiate it, list entry points, run `kedro info`, or validate one `DataCatalog.from_config()` snippet.
6. Route non-extension failures to the sibling skill: catalog/config to `../data-catalog-and-config/SKILL.md`, execution flags/runners to `../runners-and-execution/SKILL.md`, project/session setup to `../project-cli-and-sessions/SKILL.md`, and server endpoint details to `../inspection-and-server/SKILL.md`.

## Hook Does Not Fire

| Signal | Likely cause | Fix |
| --- | --- | --- |
| No hook output and no import error | Hook class was never registered in `HOOKS` | Add an instance to `src/<package_name>/settings.py`: `HOOKS = (MyHooks(),)`. |
| `KedroSession expects hooks to be registered as instances` | Registered a class, not an instance | Change `HOOKS = (MyHooks,)` to `HOOKS = (MyHooks(),)`. |
| Hook method never called | Method name does not match a Kedro spec | Rename to a valid spec such as `after_catalog_created`, `before_pipeline_run`, or `before_node_run`. |
| Hook receives stale/default argument values | Hook parameters have default values | Remove defaults from hook arguments; use local fallback logic inside the method body. |
| Node/dataset hook silent under `ParallelRunner` | Multiprocessing path does not run node/dataset hooks in workers | Re-run with `SequentialRunner` or `ThreadRunner`, or redesign with pipeline/catalog hooks. |
| Plugin hook fires but project wants it disabled | Plugin auto-discovered from `kedro.hooks` | Add the plugin distribution name to `DISABLE_HOOKS_FOR_PLUGINS`. |
| Hook behavior order changes | Multiple hooks implement the same spec | Avoid relying on order; if necessary, use `@hook_impl(tryfirst=True)` or `@hook_impl(trylast=True)`. |

For debugging hook registration, set Kedro logging to `DEBUG` temporarily. Kedro enables Pluggy tracing when the effective logger level is debug; this can be noisy, so return to `INFO` after diagnosis.

## Hook Signature Errors

Kedro uses Pluggy's opt-in arguments: a hook implementation can omit arguments it does not need. It cannot invent argument names.

Correct:

```python
@hook_impl
def before_node_run(self, node, inputs, run_id) -> None:
    ...
```

Risky or wrong:

```python
@hook_impl
def before_node_run(self, node, input_data=None) -> None:
    ...
```

Use the hook argument table in `hooks-and-plugins.md` to match names. For `before_node_run`, return only `None` or a `dict[str, Any]` keyed by existing node input dataset names. A non-dictionary replacement raises a `TypeError`; a dictionary with unexpected keys can make the node fail with an input mismatch.

## Plugin Entry Point Not Loaded

| Signal | Likely cause | Fix |
| --- | --- | --- |
| `kedro info` does not list plugin | Package not installed or metadata not visible | Install the plugin in the active environment and re-run `kedro info`. |
| Plugin listed but wrong entry points | `pyproject.toml` group misspelled | Use exact groups: `kedro.hooks`, `kedro.cli_hooks`, `kedro.project_commands`, `kedro.global_commands`, `kedro.init`, `kedro.line_magic`. |
| Hook entry point loads but hook methods do not run | Entry point exposes a class instead of an instance | Expose `hooks = MyHooks()` and point to `module:hooks`. |
| CLI hook not invoked | Used runtime `hook_impl` instead of CLI `cli_hook_impl` | Import `cli_hook_impl` from `kedro.framework.cli.hooks`. |
| Command import warning mentions failed entry point | Entry point target imports optional dependency at module import time | Move heavy imports inside commands or use lazy loading. |
| Plugin hook disabled unexpectedly | Distribution name appears in `DISABLE_HOOKS_FOR_PLUGINS` | Remove it from settings or use a separate test environment. |

`DISABLE_HOOKS_FOR_PLUGINS` only affects auto-registered runtime hooks from `kedro.hooks`; it does not remove plugin Click commands or CLI hooks.

## Custom CLI Command Problems

| Signal | Likely cause | Fix |
| --- | --- | --- |
| `Cannot load commands from <package>.cli` | `src/<package_name>/cli.py` exists but has no `cli` object | Define a Click group named `cli`. |
| Built-in `run` behavior disappeared | Project `cli.py` or plugin command overrode `run` | Preserve the built-in run command or intentionally reimplement all needed options. |
| Command option on group ignored | Kedro merges Click groups and can lose group-level processing | Move validation/options onto subcommands. |
| Project command unavailable outside project | `kedro.project_commands` or project `cli.py` requires project metadata | Use `kedro.global_commands` only for commands intended outside projects. |
| Plugin command import is slow or fails on missing optional package | Heavy imports at command module import time | Use `LazyGroup` or delay imports until command execution. |
| A typo gives no helpful match | Unknown command | Run `kedro --help` and inspect grouped commands; Kedro suggests close command names for usage errors. |

Command conflict order for project commands is built-in < plugin < project `cli.py`. When debugging, temporarily rename the project command or uninstall the plugin to isolate the layer that wins.

## Custom Dataset Fails

| Signal | Likely cause | Fix |
| --- | --- | --- |
| `An exception occurred when parsing config for dataset` | Bad `type`, versioning config, or dataset definition parsing | Check the fully qualified class path and YAML shape. |
| `Dataset '<name>' cannot be instantiated` | Abstract methods missing | Implement `load`, `save`, and `_describe`; for versioned datasets follow `AbstractVersionedDataset` requirements. |
| `must only contain arguments valid for the constructor` | YAML contains keys not accepted by `__init__` | Rename YAML keys or update constructor parameters. |
| `all dataset types must extend 'AbstractDataset'` | `type` points to a non-dataset class | Subclass `kedro.io.AbstractDataset` or `AbstractVersionedDataset`. |
| `Saving 'None' to a 'Dataset' is not allowed` | Node returned `None` for a saved dataset | Fix node output or use a dataset that explicitly handles optional values through another representation. |
| Works sequentially but fails with `ParallelRunner` | Dataset is not serializable or is single-process-only | Set `_SINGLE_PROCESS = True` and use `SequentialRunner`/`ThreadRunner`, or redesign for multiprocessing. |
| Import error for `pandas.CSVDataset`, cloud, image, or Spark backend | Optional dataset backend missing | Install the relevant `kedro-datasets` package/extras and backend libraries in the active environment. |

Use `DataCatalog.from_config()` with one dataset entry to separate constructor/config errors from pipeline execution errors.

## Custom Runner Fails

| Signal | Likely cause | Fix |
| --- | --- | --- |
| `expect an instance of Runner instead of a class` | Passed `runner=MyRunner` | Pass `runner=MyRunner()`. |
| Server rejects runner module | Dotted path outside allowlist | Put the runner in the project package or add its module prefix to `RUNNER_MODULES_WHITELIST`. |
| Server rejects runner class | Class is not an `AbstractRunner` subclass | Subclass `kedro.runner.AbstractRunner`. |
| Multiprocessing error mentions serialization | Node function, decorator, or dataset cannot be pickled | Avoid lambdas/nested functions/closures and wrap decorators with `functools.wraps()`. |
| Hooks do not run in distributed workers | Hook manager not serializable or not recreated on worker | Register hooks inside the worker task or redesign the hook behavior. |
| Downstream task cannot find data | Intermediate dataset was in memory | Persist intermediates through `DataCatalog` or platform storage. |

Do not debug custom runner scheduling inside this sub-skill unless the task is about extension design. Route normal runner selection and `kedro run` behavior to `../runners-and-execution/SKILL.md`.

## IPython And Notebook Problems

| Signal | Likely cause | Fix |
| --- | --- | --- |
| `%reload_kedro` not found | Extension not loaded or optional IPython/Jupyter deps missing | Run `%load_ext kedro.ipython` or install notebook dependencies. |
| Warning says project not found | Current directory is not inside a Kedro project | Run `%reload_kedro <project_root>` with an explicit project root. |
| `%reload_kedro --invalid_arg=...` fails | Unsupported magic option | Use supported path, `--env`/`-e`, `--params`, and `--conf-source` options. |
| `%load_node` cannot find node | Used function name or non-unique/missing node name | Use a named node that appears in registered pipelines. |
| `%load_node` cannot load inputs | Inputs are not persisted in catalog | Add catalog entries for the node inputs or debug manually. |
| Generated cells miss imports | Complex dynamic imports cannot be recovered perfectly | Add the missing imports manually in the notebook. |

A `KedroSession` supports one successful run per session. In notebooks, use `%reload_kedro` to get a fresh session before another successful `session.run()`.

## Server And Serving Problems

| Signal | Likely cause | Fix |
| --- | --- | --- |
| `Kedro HTTP server requires 'fastapi', 'pydantic', and 'uvicorn'` | Server optional dependencies absent | Install with `pip install 'kedro[server]'` in the active environment. |
| `--reload` warning | Development auto-reload enabled | Do not use `--reload` in production. |
| `/snapshot` returns status `failure` | Project metadata, catalog, or config snapshot failed | Read the response `error.type` and `error.message`; route inspection details to `../inspection-and-server/SKILL.md`. |
| `/run` returns runner module not allowed | Runner dotted path outside allowlist | Add module prefix to `RUNNER_MODULES_WHITELIST` or use a runner in the project package. |
| Concurrent API runs interfere | Built-in server reuses one `KedroServiceSession` and has no queue/isolation | Add queueing, run isolation, or use an orchestrator. |
| Security review blocks deployment | Built-in server lacks auth/authorization | Put it behind an authenticated service or build a production API wrapper. |

Do not bind to `0.0.0.0` or expose the server beyond localhost without explicit security controls.

## Deployment And Platform Problems

| Signal | Likely cause | Fix |
| --- | --- | --- |
| Airflow task cannot read upstream output | Intermediate stayed in `MemoryDataset` | Persist the dataset in an Airflow/cloud config environment or group memory-connected nodes if the plugin supports it. |
| Cloud/orchestrator task cannot import project | Package not installed in worker/container | Run `kedro package` and install the wheel in the target image/environment. |
| Spark job cannot see local files | Remote Spark executors cannot access local paths | Use cloud/object storage, Databricks Volumes, or platform-visible paths in the catalog. |
| Plugin command missing | Platform plugin not installed or wrong environment | Install plugin and check `kedro info` entry points. |
| Dependency conflict in platform image | Too many local/dev dependencies copied | Keep production requirements lean and platform-specific. |
| Credentials printed in logs | Hook/server/deploy code logs raw config | Redact credentials and tokens; load secrets from environment or secret stores. |

Before running platform commands, inspect `--help`, identify side effects, and ask for confirmation when commands may create cloud resources, start containers, upload files, or use credentials.

## Hard Usability Cases For Verification

- Add a project hook that validates the catalog after creation and logs run metadata before execution, with no default hook arguments, safe redaction of runtime parameters, and registration as an instance in `HOOKS`.
- Diagnose a plugin whose runtime hook and custom command are not invoked: verify `kedro info`, exact entry point groups, exposed instances, project-vs-global command scope, `DISABLE_HOOKS_FOR_PLUGINS`, and command precedence with project `cli.py`.
