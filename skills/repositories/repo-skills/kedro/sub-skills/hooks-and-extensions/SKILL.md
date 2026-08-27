---
name: hooks-and-extensions
description: "Extend Kedro with hooks plugins custom CLI commands custom
  datasets custom runners notebooks serving and deployment integration points."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Hooks And Extensions

Use this sub-skill when a task asks how to extend Kedro rather than only use a standard project: project hooks, installable plugins, custom Click commands, custom datasets, custom runner surfaces, IPython/Jupyter line magics, minimal HTTP serving, or deployment-platform integration patterns.

## Route Here

- Add project hooks with `from kedro.framework.hooks import hook_impl`, register instances in `settings.py` as `HOOKS = (...)`, or disable installed plugin hooks with `DISABLE_HOOKS_FOR_PLUGINS`.
- Build or debug installable plugins that expose `kedro.hooks`, `kedro.cli_hooks`, `kedro.global_commands`, `kedro.project_commands`, `kedro.init`, `kedro.line_magic`, or starter entry points.
- Override or add project CLI commands through `src/<package_name>/cli.py`, or expose reusable Click command groups from a plugin.
- Implement an `AbstractDataset` or `AbstractVersionedDataset` subclass, especially when the task is about the extension contract rather than basic `catalog.yml` syntax.
- Design custom runner classes, integration runners, or HTTP/serving wrappers while routing detailed run semantics to runners and execution.
- Extend notebook/IPython workflows with `%reload_kedro`, `%load_node`, or `kedro.line_magic` plugin entry points.
- Adapt Kedro projects for Airflow, Databricks, Dask, MLflow, Pandera, Great Expectations, Spark, or minimal FastAPI serving.

## Route Elsewhere

- Basic project creation, project detection, `KedroSession`, `kedro new`, `kedro package`, or stock `kedro ipython`/`kedro jupyter`: read [`../project-cli-and-sessions/SKILL.md`](../project-cli-and-sessions/SKILL.md).
- Runner choice, `kedro run` flags, slicing, resume, `ParallelRunner` multiprocessing details, or async I/O behavior: read [`../runners-and-execution/SKILL.md`](../runners-and-execution/SKILL.md).
- Dataset YAML, credentials, versioning, factories, `OmegaConfigLoader`, and catalog validation basics: read [`../data-catalog-and-config/SKILL.md`](../data-catalog-and-config/SKILL.md).
- Pipeline graph authoring, `node()`, `Pipeline`, namespacing, tags, and registry design: read [`../pipelines-and-nodes/SKILL.md`](../pipelines-and-nodes/SKILL.md).
- Inspection snapshots, server endpoint schemas, or read-only server diagnostics: read [`../inspection-and-server/SKILL.md`](../inspection-and-server/SKILL.md).
- Package install/import checks or broad task routing: return to [`../../SKILL.md`](../../SKILL.md).

## Current Facts

- Kedro target version is `1.4.0`; import and distribution name are `kedro`; Python requirement is `>=3.10`.
- Hook implementations import `hook_impl` from `kedro.framework.hooks`; CLI hook implementations import `cli_hook_impl` from `kedro.framework.cli.hooks`.
- Project hooks are registered as instances in `settings.py` under `HOOKS`; installed plugin hooks are discovered from the `kedro.hooks` entry point group.
- `DISABLE_HOOKS_FOR_PLUGINS = ("<plugin-distribution-name>",)` prevents auto-registered hooks for selected plugin distributions.
- Hook implementation arguments must not have default values; Pluggy may otherwise pass the defaults instead of Kedro's runtime values.
- `ParallelRunner` in Kedro 1.4.0 warns that node and dataset hooks are not executed in worker processes; choose `SequentialRunner` or `ThreadRunner` when those hooks are essential.
- CLI plugin entry point groups include `kedro.global_commands`, `kedro.project_commands`, `kedro.init`, `kedro.line_magic`, `kedro.hooks`, and `kedro.cli_hooks`.
- Project command resolution order is built-in commands, then plugin commands, then project `cli.py`; later sources can override earlier commands.

## Reference Map

- Read [`references/hooks-and-plugins.md`](references/hooks-and-plugins.md) for hook specs, hook signatures, registration, plugin entry point groups, CLI hooks, command precedence, and plugin debugging.
- Read [`references/custom-datasets-and-cli.md`](references/custom-datasets-and-cli.md) for `AbstractDataset` contracts, versioned datasets, project `cli.py` overrides, reusable plugin commands, custom runner extension surfaces, and validation checks.
- Read [`references/deployment-and-integrations.md`](references/deployment-and-integrations.md) for notebooks/IPython, line magics, HTTP serving extension, deployment-platform patterns, and optional dependency/security notes.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) when hooks are not firing, plugin entry points do not load, custom commands conflict, datasets fail to instantiate, optional extras are missing, or serving/deployment integration fails.

## Fast Patterns

1. For a project hook, create `src/<package_name>/hooks.py`, decorate methods with `@hook_impl`, omit unused parameters, do not use defaults, then register instances in `src/<package_name>/settings.py` as `HOOKS = (ProjectHooks(),)`.
2. For hook ordering, treat order as non-guaranteed; project hooks follow last-in-first-out registration and plugin hooks are auto-registered first, but prefer `@hook_impl(tryfirst=True)` or `@hook_impl(trylast=True)` only when order is essential.
3. For plugin hooks, expose an object instance through `[project.entry-points."kedro.hooks"]`; for CLI lifecycle hooks, expose an instance through `[project.entry-points."kedro.cli_hooks"]`.
4. For custom CLI, use project `src/<package_name>/cli.py` for project-specific overrides and plugin `kedro.global_commands` or `kedro.project_commands` for reusable commands.
5. For custom datasets, subclass `kedro.io.AbstractDataset` or `AbstractVersionedDataset`, implement `load`, `save`, and `_describe`, and configure by fully qualified class path in `catalog.yml`.
6. For serving or deployment, first decide whether you need a Kedro-native extension point, an orchestrator plugin, or a thin wrapper around `KedroServiceSession`; warn before network, cloud, credential, or public-server operations.

## Safety Notes

- Set `KEDRO_DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` for CLI probes or automated examples when telemetry must be disabled.
- Avoid printing credential dictionaries, runtime params with secrets, personal access tokens, or full platform paths from hooks and server endpoints.
- `kedro server start --reload` is development-only; the built-in server does not include authentication, authorization, request queuing, or per-request session isolation.
- Deployment commands for Airflow, Databricks, cloud platforms, Docker, or plugin CLIs may create files, contact networks, upload artifacts, or use credentials; ask before executing them.
