# Snakemake Python API Reference

This reference covers Snakemake 9.23.1 programmatic API usage. It is for agents embedding Snakemake in Python or translating a CLI operation into `SnakemakeApi`, `WorkflowApi`, `DAGApi`, and settings dataclasses.

## API Object Lifecycle

Use `SnakemakeApi` as a context manager. API methods that create workflows check that the API is inside a `with` block, and the context manager handles logger shutdown plus workdir restoration.

```python
from pathlib import Path
from snakemake.api import SnakemakeApi
from snakemake.settings.types import OutputSettings, ResourceSettings

with SnakemakeApi(output_settings=OutputSettings(printshellcmds=True)) as snakemake_api:
    workflow_api = snakemake_api.workflow(
        resource_settings=ResourceSettings(cores=1),
        snakefile=Path("Snakefile"),
        workdir=Path("."),
    )
```

Important constructor and method signatures in 9.23.1:

- `SnakemakeApi(output_settings=OutputSettings(...))`
- `SnakemakeApi.workflow(resource_settings, config_settings=None, storage_settings=None, workflow_settings=None, deployment_settings=None, storage_provider_settings=None, snakefile=None, workdir=None)`
- `WorkflowApi.dag(dag_settings=None)`
- `WorkflowApi.lint(json=False)`
- `WorkflowApi.list_rules(only_targets=False)`
- `DAGApi.execute_workflow(executor="local", execution_settings=None, remote_execution_settings=None, scheduling_settings=None, group_settings=None, executor_settings=None, updated_files=None, scheduler_settings=None, greedy_scheduler_settings=None)`
- `DAGApi.printdag()`
- `DAGApi.summary(detailed=False)`
- `DAGApi.archive(path)`
- `DAGApi.generate_unit_tests(path)`

## Settings Dataclasses

Import settings from `snakemake.settings.types` and pass them explicitly. Prefer constructing dataclasses over relying on defaults when the embedded use case must be reproducible.

Common dataclasses:

- `OutputSettings`: log/dry-run display flags such as `dryrun`, `printshellcmds`, `verbose`, `show_failed_logs`, `stdout`, `quiet`, `skip_plugin_handlers`, `enable_file_logging`.
- `ResourceSettings`: local and remote capacity such as `cores`, `nodes`, `local_cores`, `resources`, `overwrite_threads`, `overwrite_resources`, `default_resources`.
- `ConfigSettings`: `config`, `configfiles`, `config_args`, and `replace_workflow_config`; config files are loaded and merged during initialization.
- `StorageSettings`: `default_storage_provider`, `default_storage_prefix`, `shared_fs_usage`, `keep_storage_local`, `retrieve_storage`, `local_storage_prefix`, `notemp`, `all_temp`.
- `DeploymentSettings`: `deployment_method`, `conda_prefix`, `conda_cleanup_pkgs`, `conda_base_path`, `conda_frontend`, `apptainer_args`, `apptainer_prefix`.
- `WorkflowSettings`: `wrapper_prefix`, `exec_mode`, `cache`, `consider_ancient`, `runtime_source_cache_path`, persistence backend fields.
- `DAGSettings`: `targets`, `target_jobs`, `forceall`, `forcerun`, `until`, `omit_from`, `allowed_rules`, `rerun_triggers`, `strict_evaluation`, `print_dag_as`.
- `ExecutionSettings`: execution toggles such as `latency_wait`, `keep_going`, `debug`, `lock`, `ignore_incomplete`, `retries`, `use_threads`, `keep_incomplete`.
- `SchedulingSettings`: `scheduler`, `prioritytargets`, `greediness`, `subsample`, job-rate limits.
- `GroupSettings`: `overwrite_groups`, `group_components`, `local_groupid`.
- `RemoteExecutionSettings`: `jobname`, `jobscript`, status-check settings, `envvars`, `immediate_submit`, `precommand`, `job_deploy_sources`.

Many mapping defaults are immutable mappings or frozensets. If you need to extend them, create a new dict/set and pass it into a fresh settings instance rather than mutating a default value in place.

## CLI-to-API Equivalents

Start with a safe CLI command, then translate each concern to settings:

```bash
snakemake --snakefile Snakefile --cores 1 --dry-run --printshellcmds
```

```python
from pathlib import Path
from snakemake.api import SnakemakeApi
from snakemake.settings.types import DAGSettings, ExecutionSettings, OutputSettings, ResourceSettings

with SnakemakeApi(output_settings=OutputSettings(dryrun=True, printshellcmds=True)) as api:
    workflow = api.workflow(
        resource_settings=ResourceSettings(cores=1),
        snakefile=Path("Snakefile"),
        workdir=Path("."),
    )
    dag = workflow.dag(DAGSettings(targets=frozenset({"all"})))
    dag.execute_workflow(executor="dryrun", execution_settings=ExecutionSettings())
```

Mappings agents commonly need:

- `--snakefile PATH`: `snakefile=Path("PATH")` in `SnakemakeApi.workflow(...)`.
- `--directory DIR`: `workdir=Path("DIR")` in `SnakemakeApi.workflow(...)`.
- `--cores N`: `ResourceSettings(cores=N)`.
- `--jobs N` for non-local executors: `ResourceSettings(nodes=N)`.
- CLI targets: `DAGSettings(targets=frozenset({...}))`.
- `--config key=value`: `ConfigSettings(config={"key": "value"})`.
- `--configfile config.yaml`: `ConfigSettings(configfiles=[Path("config.yaml")])`.
- `--forceall`: `DAGSettings(forceall=True)`.
- `--forcerun rule`: `DAGSettings(forcerun=frozenset({"rule"}))`.
- `--until rule`: `DAGSettings(until=frozenset({"rule"}))`.
- `--allowed-rules rule`: `DAGSettings(allowed_rules=frozenset({"rule"}))`.
- `--printshellcmds`: `OutputSettings(printshellcmds=True)`.
- `--verbose` / `--show-failed-logs`: `OutputSettings(verbose=True, show_failed_logs=True)`.
- `--latency-wait N`: `ExecutionSettings(latency_wait=N)`.
- `--keep-going`: `ExecutionSettings(keep_going=True)`.
- `--scheduler greedy`: `SchedulingSettings(scheduler="greedy")`.
- `--summary`: `dag.summary(detailed=False)`.
- `--detailed-summary`: `dag.summary(detailed=True)`.
- `--dag`: `dag.printdag()`.
- `--archive archive.tar`: `dag.archive(Path("archive.tar"))`.
- generated unit tests: `dag.generate_unit_tests(Path(".tests/unit"))`.

Do not translate old `--reason` examples. The flag is absent in Snakemake 9.23.1; job reasons are already printed in dry-run output.

## Non-Mutating API Operations

Use these before modifying outputs or executing real jobs:

```python
with SnakemakeApi(output_settings=OutputSettings(stdout=True, printshellcmds=True)) as api:
    workflow = api.workflow(ResourceSettings(cores=1), snakefile=Path("Snakefile"))
    workflow.lint(json=False)
    workflow.dag(DAGSettings(targets=frozenset({"all"}))).summary(detailed=True)
    workflow.dag().printdag()
```

Notes:

- `WorkflowApi.lint()` and `WorkflowApi.list_rules()` construct a workflow without executing jobs and internally force a single core.
- `DAGApi.printdag()`, `summary()`, `archive()`, and `generate_unit_tests()` also avoid normal job execution, but may read workflow metadata and create their requested output artifacts.
- For a dry-run execution plan, call `execute_workflow(executor="dryrun")` rather than shelling out to `snakemake --dry-run`.

## Output Capture Expectations

Snakemake uses its logger and many API methods print to stdout/stderr rather than returning rich Python objects. If embedding in a service or test harness:

- Set `OutputSettings(stdout=True)` when stdout logs are easier to capture.
- Use `contextlib.redirect_stdout` / `redirect_stderr` only around the small API call that prints (`printdag`, `summary`, dry-run execution), and expect logger handlers to still matter.
- Use `SnakemakeApi.print_exception(ex)` for Snakemake-style error formatting in embedded runners.
- Use `SnakemakeApi.get_log_handlers()` only after logger setup when a test utility needs instantiated plugin log handlers.

## Safe Embedding Checklist

1. Resolve `Snakefile` and `workdir` explicitly; default snakefile discovery depends on current working directory.
2. Always enter `SnakemakeApi` with `with`; avoid keeping one global API object around multiple unrelated workflows.
3. Keep user-provided paths as `Path` values, but do not mutate process CWD outside the API context.
4. Use `executor="dryrun"` and `ResourceSettings(cores=1)` for validation probes.
5. For real local execution, set `ResourceSettings(cores=N)`; Snakemake raises an API error when local execution lacks cores.
6. For remote/non-local executors, set `ResourceSettings(nodes=N)` and storage/deployment settings appropriate to the plugin.
7. Let plugin registries validate plugin names and settings; catch `ApiError` at the embedding boundary and report actionable messages.
