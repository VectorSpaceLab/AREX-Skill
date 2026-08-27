---
name: runners-and-execution
description: "Run Kedro pipelines, choose runners, configure execution flags,
  resume missing outputs, load versions, and troubleshoot runner failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Runners and Execution

Use this sub-skill when a task is about executing Kedro pipelines with `kedro run`, `KedroSession.run()`, `AbstractRunner`, `SequentialRunner`, `ThreadRunner`, `ParallelRunner`, async load/save, run slicing, load versions, or missing-output resume behavior.

## Route Here

- Choose between `SequentialRunner`, `ThreadRunner`, `ParallelRunner`, or a custom `AbstractRunner` subclass.
- Build a `kedro run` command with `--runner`, `--async`, `--tags`, `--nodes`, `--from-nodes`, `--to-nodes`, `--from-inputs`, `--to-outputs`, `--load-versions`, `--pipelines`, `--namespaces`, `--params`, `--config`, `--conf-source`, or `--only-missing-outputs`.
- Use `KedroSession.run()` programmatically after a project has already been bootstrapped or opened through a session.
- Diagnose execution-time failures from missing inputs, empty slices, wrong runner instances, multiprocessing serialization, async I/O, resume suggestions, hook behavior, or persistent-output skipping.

## Route Elsewhere

- Pipeline graph construction, `node()`, `Pipeline`, `pipeline()`, tags, namespaces, and slice semantics before execution: read [`../pipelines-and-nodes/SKILL.md`](../pipelines-and-nodes/SKILL.md).
- `DataCatalog`, catalog YAML, credentials, dataset versioning, `OmegaConfigLoader`, and dataset optional dependencies: read [`../data-catalog-and-config/SKILL.md`](../data-catalog-and-config/SKILL.md).
- Project creation, project detection, `kedro new`, `KedroSession.create()`, `bootstrap_project()`, and CLI command availability: read [`../project-cli-and-sessions/SKILL.md`](../project-cli-and-sessions/SKILL.md).
- Hook implementation, plugin hooks, custom CLI commands, custom datasets, and custom runner design beyond selection/use: read [`../hooks-and-extensions/SKILL.md`](../hooks-and-extensions/SKILL.md).
- Package-wide installation, optional extras, and root routing: read [`../../SKILL.md`](../../SKILL.md).

## Current Facts

- Kedro version target: `1.4.0`; distribution and import name: `kedro`; Python requirement: `>=3.10`.
- Runner constructors: `SequentialRunner(is_async=False)`, `ThreadRunner(max_workers=None, is_async=False)`, and `ParallelRunner(max_workers=None, is_async=False)`.
- `KedroSession.run()` accepts `pipeline_name=None`, `pipeline_names=None`, `tags=None`, `runner=None`, `node_names=None`, `from_nodes=None`, `to_nodes=None`, `from_inputs=None`, `to_outputs=None`, `load_versions=None`, `namespaces=None`, and `only_missing_outputs=False`.
- `kedro run` defaults to `SequentialRunner` and supports the execution flags documented in [`references/run-options.md`](references/run-options.md).
- `ParallelRunner` uses multiprocessing, requires serializable nodes/datasets, uses `SharedMemoryDataCatalog` through the CLI/session path, and does not execute node/dataset hooks in worker processes.
- `ThreadRunner` uses threads, does not support async load/save, and is the recommended concurrent runner for Spark-style workflows sharing one Spark session.

## Reference Map

- Read [`references/run-options.md`](references/run-options.md) to construct safe CLI and `KedroSession.run()` calls, including slicing, load versions, runtime params, config files, and only-missing-output runs.
- Read [`references/runner-selection.md`](references/runner-selection.md) to choose a runner, configure `max_workers`, use `KEDRO_MP_CONTEXT`, handle async I/O, and understand programmatic output objects.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) when a run fails, skips unexpected nodes, cannot find inputs, cannot serialize for multiprocessing, ignores hooks, or rejects CLI/session arguments.

## Fast Patterns

- Safe default run: `KEDRO_DISABLE_TELEMETRY=1 kedro run`.
- Explicit concurrent run for thread-safe work: `KEDRO_DISABLE_TELEMETRY=1 kedro run --runner=ThreadRunner`.
- Multiprocessing run when nodes and datasets are serializable: `KEDRO_DISABLE_TELEMETRY=1 KEDRO_MP_CONTEXT=spawn kedro run --runner=ParallelRunner`.
- Resume only missing persistent outputs: `KEDRO_DISABLE_TELEMETRY=1 kedro run --only-missing-outputs`.
- Load a versioned input: `KEDRO_DISABLE_TELEMETRY=1 kedro run --load-versions=raw_data:2024-01-01T00.00.00.000Z`.
- Programmatic run: create a new `KedroSession` for each successful run, pass a runner instance such as `SequentialRunner()`, and load returned output datasets from the catalog or dataset objects.

## Safety Notes

- `kedro run` executes user pipeline code and can read/write configured datasets; do not treat it as a dry-run command.
- For automation or privacy-sensitive checks, set `KEDRO_DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` before CLI probes or runs.
- `--conf-source` may point at local or remote configuration; confirm trust and credentials handling before using remote configuration sources.
- `--params` values may override runtime parameters used by nodes; avoid echoing secrets and route parameter/config validation to [`../data-catalog-and-config/SKILL.md`](../data-catalog-and-config/SKILL.md).
