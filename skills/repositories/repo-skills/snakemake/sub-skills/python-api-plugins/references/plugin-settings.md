# Plugin Settings and Registries

Snakemake 9.23.1 routes several runtime surfaces through interface packages and plugin registries. Programmatic callers should pass plugin-specific settings objects and let the registry validate them instead of fabricating ad-hoc dicts.

## Interface Packages

The core package depends on these plugin interface packages:

- `snakemake-interface-executor-plugins>=9.3.2,<10.0`
- `snakemake-interface-storage-plugins>=4.4.1,<5.0`
- `snakemake-interface-report-plugins>=1.2.0,<2.0.0`
- `snakemake-interface-logger-plugins>=1.1.0,<3.0.0`
- `snakemake-interface-scheduler-plugins>=2.0.0,<3.0.0`

These interfaces define settings base classes and registries used by `snakemake.api`. The concrete plugin packages, such as executor or storage plugins, may need separate installation in the target runtime. Plugin installation/deployment policy belongs in `../../deployment-storage/SKILL.md`; this reference focuses on API shapes.

## Executor Plugins

`DAGApi.execute_workflow()` resolves the executor by name through `ExecutorPluginRegistry().get_plugin(executor)`.

```python
from snakemake.settings.types import ExecutionSettings, ResourceSettings

with SnakemakeApi(output_settings=OutputSettings()) as api:
    workflow = api.workflow(
        resource_settings=ResourceSettings(cores=1),
        snakefile=Path("Snakefile"),
    )
    workflow.dag().execute_workflow(
        executor="local",
        execution_settings=ExecutionSettings(latency_wait=5),
    )
```

Rules of thumb:

- Use `executor="dryrun"` for API dry-runs instead of shelling out.
- Use `executor="local"` with `ResourceSettings(cores=N)` for real local execution.
- Non-local executors usually require `ResourceSettings(nodes=N)` and may imply no shared filesystem or job source deployment.
- Pass `executor_settings=<plugin ExecutorSettings object>` only after importing it from the concrete executor plugin package.
- Snakemake calls `executor_plugin.validate_settings(executor_settings)` when settings are provided.

Example for a concrete executor package shape:

```python
from snakemake_executor_plugin_cluster_generic import ExecutorSettings

executor_settings = ExecutorSettings(submit_cmd="qsub")
dag.execute_workflow(executor="cluster-generic", executor_settings=executor_settings)
```

If the plugin package is not installed, the import or registry lookup should fail early. Do not hide that failure by falling back to a different executor unless the user explicitly accepts different execution semantics.

## Storage Provider Settings

Storage settings have two layers:

1. Core storage policy in `StorageSettings`, such as `default_storage_provider`, `default_storage_prefix`, `shared_fs_usage`, `keep_storage_local`, and `notemp`.
2. Plugin-specific settings in `storage_provider_settings`, keyed by provider name and represented with tagged settings objects from the plugin interface.

```python
from snakemake.settings.types import ResourceSettings, StorageSettings

workflow = api.workflow(
    resource_settings=ResourceSettings(cores=1),
    storage_settings=StorageSettings(
        default_storage_provider="s3",
        default_storage_prefix="s3://example-bucket/workflow-prefix",
    ),
    storage_provider_settings={
        # "s3": tagged_settings_from_the_installed_s3_plugin,
    },
    snakefile=Path("Snakefile"),
)
```

Behavior to preserve:

- If `default_storage_provider` is set, Snakemake checks the provider through `StoragePluginRegistry`.
- Some operations require the default provider to be read-write.
- When plugin settings exist, the plugin validates the settings object before constructing a provider instance.
- Non-shared filesystem executor modes can require a default storage provider and prefix unless the executor can transfer local files.

Do not pass a plain nested dict just because the CLI accepted strings. Use the concrete plugin's documented settings factory or tagged settings type.

## Scheduler Plugins

`SchedulingSettings(scheduler="ilp")` is the default. `DAGApi.execute_workflow()` resolves scheduler names through the scheduler plugin registry.

```python
from snakemake.settings.types import SchedulingSettings

dag.execute_workflow(
    executor="dryrun",
    scheduling_settings=SchedulingSettings(scheduler="greedy"),
)
```

Notes:

- Dry-run, touch, and immediate-submit modes force greedy scheduling behavior internally.
- `SchedulingSettings.greediness` is accepted but deprecated in favor of scheduler-specific settings where available.
- If ILP solver support is unavailable, Snakemake can warn and fall back to greedy scheduling.

## Logger Plugins and Output Settings

`OutputSettings` implements logger-interface settings and can carry plugin log handler settings:

```python
from snakemake.settings.types import OutputSettings

output_settings = OutputSettings(
    printshellcmds=True,
    verbose=True,
    show_failed_logs=True,
    log_handler_settings={},
    stdout=True,
)
```

Use `skip_plugin_handlers=True` for embedding contexts where plugin log handlers should not be initialized, for example remote queue modes or tests that need deterministic logging.

## Report Plugins

Reports use `DAGApi.create_report(reporter="html", report_settings=None, global_report_settings=None)`. The reporter is resolved through the report plugin registry, and provided report settings are validated by the plugin.

```python
from snakemake.settings.types import GlobalReportSettings

dag.create_report(
    reporter="html",
    global_report_settings=GlobalReportSettings(metadata_template=Path("report-metadata.yaml")),
)
```

Route report content design and report troubleshooting to `../../debugging-reporting/SKILL.md`; use this section only for API invocation and plugin settings shape.

## Optional Plugin Imports

Use import guards when embedding optional plugin behavior:

```python
try:
    from snakemake_executor_plugin_cluster_generic import ExecutorSettings
except ImportError as exc:
    raise RuntimeError(
        "The cluster-generic executor plugin is required for this execution mode. "
        "Install it before selecting executor='cluster-generic'."
    ) from exc
```

Do not import optional plugins at module import time in a library unless every user needs them. Lazy imports keep basic local and dry-run API use working without extra dependencies.

## Validation Signals

Good plugin-aware API code should surface these errors clearly:

- Unknown executor, storage, scheduler, reporter, or logger plugin name.
- Missing concrete plugin package for a selected plugin.
- Plugin settings object is the wrong class or fails plugin validation.
- Non-local executor selected without `ResourceSettings(nodes=...)`.
- Local executor selected without `ResourceSettings(cores=...)` for real execution.
- No shared filesystem plus no default storage provider/prefix for executors that cannot transfer local files.
- Default storage provider selected for a write operation but the provider is not read-write.
