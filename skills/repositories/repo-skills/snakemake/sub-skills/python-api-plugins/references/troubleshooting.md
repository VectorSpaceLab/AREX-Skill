# Python API and Plugin Troubleshooting

Use this checklist when embedded Snakemake code fails, differs from CLI behavior, or interacts with optional plugins.

## `workflow()` Fails Outside Context Manager

Signal:

- Error says the method can only be called when `SnakemakeApi` is used within a `with` statement.

Fix:

```python
with SnakemakeApi(output_settings=OutputSettings()) as api:
    workflow = api.workflow(ResourceSettings(cores=1), snakefile=Path("Snakefile"))
```

Do not construct one process-global `SnakemakeApi` and call `workflow()` later outside the context. The context owns logger setup, cleanup, and workdir restoration.

## Settings Mismatch

Signals:

- `TypeError` for unexpected dataclass keyword.
- `ApiError` from plugin validation.
- CLI option copied directly into the wrong settings class.

Fix:

- Put resources and cores in `ResourceSettings`, not `ExecutionSettings`.
- Put target selection and force/rerun/until filters in `DAGSettings`.
- Put log display flags such as `printshellcmds` and `verbose` in `OutputSettings`.
- Put retries, locking, debug, latency, and keep-going behavior in `ExecutionSettings`.
- Put scheduler selection in `SchedulingSettings`.
- Put storage provider/core storage behavior in `StorageSettings`; put plugin-specific values in plugin settings objects.

## Immutable Mapping or Default Confusion

Signals:

- Code tries `settings.resources["mem_mb"] = 1000` and fails.
- Mutating one settings object unexpectedly does not affect a parsed cached property.

Fix:

Create fresh mappings and fresh settings objects:

```python
resource_settings = ResourceSettings(
    cores=1,
    resources={"mem_mb": 1000},
    overwrite_threads={"align": 4},
)
```

Avoid mutating settings after a workflow or DAG has been created. Build a new API workflow for a materially different run.

## Local Execution Requires Cores

Signal:

- Error says cores have to be specified for local execution.

Fix:

```python
workflow = api.workflow(
    resource_settings=ResourceSettings(cores=1),
    snakefile=Path("Snakefile"),
)
workflow.dag().execute_workflow(executor="local")
```

For a non-mutating plan, prefer `executor="dryrun"`; it will set cores to 1 when needed.

## Unsupported or Missing Executor Plugin

Signals:

- ImportError for `snakemake_executor_plugin_*`.
- Registry lookup fails for the executor name.
- Plugin validation rejects `executor_settings`.

Fix:

1. Confirm the selected executor plugin is installed in the runtime environment.
2. Import the plugin's own `ExecutorSettings` class lazily.
3. Pass `ResourceSettings(nodes=N)` for non-local executors.
4. Do not substitute `local` for a remote executor silently; that changes semantics.

Route installation and deployment policy to `../../deployment-storage/SKILL.md`.

## Storage Provider Settings Shape

Signals:

- Error from `StoragePluginRegistry`.
- Attribute error like a dict has no plugin settings method.
- Default storage provider is rejected for source deployment or write operations.

Fix:

- Put `default_storage_provider` and `default_storage_prefix` in `StorageSettings`.
- Put provider-specific credentials/options in `storage_provider_settings`, keyed by provider name and represented as tagged/plugin settings from the installed storage plugin.
- Ensure the provider supports read-write behavior for operations that upload or deploy sources.
- For non-shared executors, configure default storage unless the executor can transfer local files.

## API Dry-Run Without Shelling Out

Use the dry-run executor rather than `subprocess.run(["snakemake", "--dry-run", ...])`:

```python
with SnakemakeApi(output_settings=OutputSettings(dryrun=True, printshellcmds=True)) as api:
    workflow = api.workflow(ResourceSettings(cores=1), snakefile=Path("Snakefile"))
    workflow.dag(DAGSettings(targets=frozenset({"all"}))).execute_workflow(
        executor="dryrun",
        execution_settings=ExecutionSettings(),
    )
```

Expected signals include a job plan and job reasons in dry-run output. Do not add `--reason`; it is not a Snakemake 9.23.1 flag.

## Output Capture Surprises

Signals:

- API call returns `None` even though useful text appeared on stdout/stderr.
- Capturing stdout misses logger output.
- Graph or summary text appears in a different stream than expected.

Fix:

- Treat `printdag()`, `summary()`, `list_rules()`, and dry-run execution as printing operations.
- Use `OutputSettings(stdout=True)` when stdout capture is important.
- Redirect stdout/stderr only around the operation and still expect Snakemake logging configuration to matter.
- In tests, assert stable substrings such as rule names, target file names, or DOT graph markers rather than full output order.

## Optional Plugin Imports Break Basic API Use

Signal:

- A library module fails to import because an optional executor/storage/report plugin package is missing, even for local or dry-run use.

Fix:

Move optional imports inside the branch that selects that plugin:

```python
def cluster_generic_settings(submit_cmd: str):
    try:
        from snakemake_executor_plugin_cluster_generic import ExecutorSettings
    except ImportError as exc:
        raise RuntimeError("Install the cluster-generic executor plugin first.") from exc
    return ExecutorSettings(submit_cmd=submit_cmd)
```

Keep dry-run and local execution paths free of optional plugin imports.

## Remote Snakefile and Workdir Confusion

Signals:

- Default snakefile discovery fails.
- A shorthand or remote snakefile string is unexpectedly converted to a local path.
- Relative config or output paths resolve from the wrong directory.

Fix:

- Pass `snakefile` explicitly.
- Pass `workdir` explicitly when embedding.
- Snakemake preserves supported remote/shorthand snakefile strings; local paths can be `Path` objects.
- Remember that `workflow()` may change workdir inside the API context and restore it on cleanup.

## Troubleshooting Command Parity

When comparing embedded behavior with CLI behavior, use current Snakemake 9.23.1 commands:

```bash
snakemake --snakefile Snakefile --cores 1 --dry-run --printshellcmds
python -m snakemake --snakefile Snakefile --cores 1 --dry-run --printshellcmds
```

If a copied command includes `--reason`, remove it. Reasons are shown in dry-run output without that flag.
