# API Reference

This reference covers the runtime surface that future agents should use for safe local generation and workflow execution.

## Core signatures

### `DataDesigner`

```python
DataDesigner(
    artifact_path: Path | str | None = None,
    *,
    model_providers: list[ModelProvider] | None = None,
    secret_resolver: SecretResolver | None = None,
    seed_readers: list[SeedReader] | None = None,
    managed_assets_path: Path | str | None = None,
    person_reader: PersonReader | None = None,
    mcp_providers: list[MCPProviderT] | None = None,
    auto_configure_logging: bool = True,
)
```

Public methods:

```python
validate(config_builder: DataDesignerConfigBuilder) -> None
check_models(
    config_builder: DataDesignerConfigBuilder,
    *,
    max_attempts: int = 1,
    retry_backoff_seconds: float = 0,
) -> None
preview(
    config_builder: DataDesignerConfigBuilder,
    *,
    num_records: int = 10,
) -> PreviewResults
create(
    config_builder: DataDesignerConfigBuilder,
    *,
    num_records: int = 10,
    dataset_name: str = "dataset",
    resume: ResumeMode = ResumeMode.NEVER,
    artifact_path: Path | str | None = None,
    on_batch_complete: Callable[[Path], None] | None = None,
) -> DatasetCreationResults
acreate(
    config_builder: DataDesignerConfigBuilder,
    *,
    num_records: int = 10,
    dataset_name: str = "dataset",
    resume: ResumeMode = ResumeMode.NEVER,
    artifact_path: Path | str | None = None,
) -> DatasetCreationResults
set_run_config(run_config: RunConfig) -> None
compose_workflow(*, name: str) -> CompositeWorkflow
list_mcp_tool_names(mcp_provider_name: str, *, timeout_sec: float = 10.0) -> list[str]
```

Behavior notes:

- `validate` compiles the configuration with the active secret resolver, seed readers, model registry, and MCP registry.
- `check_models` probes every referenced model alias and MCP tool alias. It is the external-readiness gate, not a configuration-shape check.
- `preview` is in-memory only; it returns a `PreviewResults` object and does not write the dataset artifact tree.
- `create` persists artifacts and profiling results.
- `acreate` is a thread offload wrapper around `create`; it is the safe async entry point.
- `set_run_config` replaces the active runtime settings and recreates request admission state.
- `compose_workflow` returns the experimental linear workflow API.
- `list_mcp_tool_names` only consults configured MCP providers and raises `ValueError` when the requested provider name is missing.

### `DataDesignerConfigBuilder`

Installed-package signature:

```python
DataDesignerConfigBuilder(
    model_configs: list[ModelConfig] | str | Path | None = None,
    tool_configs: list[ToolConfig] | None = None,
)
```

Runtime-relevant methods:

```python
build() -> DataDesignerConfig
from_config(config: dict | str | Path | BuilderConfig) -> Self
with_seed_dataset(
    seed_source,
    *,
    sampling_strategy: SamplingStrategy = SamplingStrategy.ORDERED,
    selection_strategy: IndexRange | PartitionBlock | None = None,
) -> Self
get_column_configs() -> list[ColumnConfigT]
get_profilers() -> list[ColumnProfilerConfigT]
```

Notes:

- The runtime API only needs a builder object; column-authoring details belong to `config-authoring`.
- `build()` materializes the immutable config object consumed by `validate`, `preview`, `create`, and `check_models`.
- `with_seed_dataset()` is the bridge used by result round-trips and workflow seeding.

### `DatasetCreationResults`

Constructor signature:

```python
DatasetCreationResults(
    *,
    artifact_storage: ArtifactStorage,
    analysis: DatasetProfilerResults,
    config_builder: DataDesignerConfigBuilder,
    dataset_metadata: DatasetMetadata,
    task_traces: list[TaskTrace] | None = None,
)
```

Public methods and fields:

```python
artifact_storage: ArtifactStorage
dataset_metadata: DatasetMetadata
task_traces: list[TaskTrace]
load_dataset() -> pd.DataFrame
load_analysis() -> DatasetProfilerResults
to_config_builder(columns: list[str] | None = None) -> DataDesignerConfigBuilder
count_records() -> int
load_processor_dataset(processor_name: str) -> pd.DataFrame
get_path_to_processor_artifacts(processor_name: str) -> Path
export(path: Path | str, *, format: ExportFormat | None = None) -> Path
push_to_hub(
    repo_id: str,
    description: str,
    *,
    token: str | None = None,
    private: bool = False,
    tags: list[str] | None = None,
) -> str
```

Behavior notes:

- Disk-backed methods (`load_dataset`, `count_records`, `load_processor_dataset`, `get_path_to_processor_artifacts`, `export`, `push_to_hub`) reflect the current on-disk artifact tree.
- `load_analysis()` returns the profiler result object captured during the current invocation.
- `task_traces` only includes traces from the current run; resumed runs do not merge old in-memory traces.
- `count_records()` reads parquet metadata only, so it is cheap and also sees any extra batch files that were added later.
- `to_config_builder()` copies the result dataset into a seed dataset builder for interactive follow-up work.
- `display_sample_record()` is inherited from the shared record-sampler mixin and samples from the loaded dataset.

### `PreviewResults`

`DataDesigner.preview()` returns a `PreviewResults` object from `data_designer.config.preview_results`.

Runtime fields:

```python
dataset: pd.DataFrame | None
analysis: DatasetProfilerResults | None
processor_artifacts: dict[str, list[dict]] | None
dataset_metadata: DatasetMetadata | None
task_traces: list[Any] | None
```

Runtime method:

```python
to_config_builder(columns: list[str] | None = None) -> DataDesignerConfigBuilder
```

Notes:

- Preview results stay in memory.
- The preview result object is useful for interactive inspection and for seeding a new builder from an existing preview.
- `display_sample_record()` comes from the shared record-sampler mixin and samples from the in-memory preview dataset.

### `CompositeWorkflow` and `CompositeWorkflowResults`

```python
compose_workflow(*, name: str) -> CompositeWorkflow
```

Stage and run methods:

```python
add_stage(
    name: str,
    config_builder: DataDesignerConfigBuilder,
    *,
    num_records: int | None = None,
    on_success: OnSuccessCallback | None = None,
    on_success_version: str | None = None,
    output_processors: list[ProcessorConfig] | None = None,
    output: str = "final",
    allow_empty: bool = False,
    sampling_strategy: SamplingStrategy = SamplingStrategy.ORDERED,
    selection_strategy: IndexRange | PartitionBlock | None = None,
) -> CompositeWorkflow
run(
    *,
    resume: ResumeMode = ResumeMode.NEVER,
    targets: StageTargets | None = None,
    rerun_from: str | None = None,
    stage_output_overrides: dict[str, Path | str] | None = None,
) -> CompositeWorkflowResults
```

Selected `CompositeWorkflowResults` methods:

```python
final_result: DatasetCreationResults
load_dataset() -> pd.DataFrame
load_analysis() -> DatasetProfilerResults
count_records() -> int
get_stage_output_path(stage_name: str) -> Path
load_stage_output(stage_name: str) -> pd.DataFrame
count_stage_output_records(stage_name: str) -> int
export(path: Path | str, *, format: ExportFormat | None = None) -> Path
export_stage(stage_name: str, path: Path | str, *, format: ExportFormat | None = None) -> Path
push_to_hub(*args, **kwargs) -> str
```

Workflow notes:

- `output="processor:<name>"` selects a processor artifact to hand downstream.
- `on_success` can replace the stage output handed to the next stage.
- Workflow output reuse is fingerprinted by stage config, output selection, and the previous stage fingerprint.
- `push_to_hub()` only works when the final selected output is the raw final-stage dataset.

## Shared enums and formats

### `ResumeMode`

```python
ResumeMode.NEVER
ResumeMode.ALWAYS
ResumeMode.IF_POSSIBLE
```

### `ExportFormat`

```python
Literal["jsonl", "csv", "parquet"]
```

### Supported export behavior

- `jsonl` writes one record per line.
- `csv` writes a single header row and streams batch files in order.
- `parquet` unifies batch schemas before writing a single file.

## Runtime knobs that matter most

Use `set_run_config()` to control these generation-time behaviors:

| Field | Why it matters |
| --- | --- |
| `buffer_size` | Records per row group; affects memory use and resume boundaries. |
| `max_concurrent_row_groups` | Active row-group cap for the async scheduler. |
| `max_in_flight_tasks` | Scheduler task-lease cap. |
| `display_tui` | Terminal throughput panel; only visible when a TTY is present. |
| `write_scheduler_events` | Writes `scheduler_events.jsonl` in the dataset directory. |
| `async_trace` | Captures per-task trace data. |
| `otel_metrics_port` | Set to `None` to disable metrics export. |
| `preserve_dropped_columns` | Controls whether dropped columns are written to a sidecar artifact tree. |
| `jinja_rendering_engine` | Chooses secure vs native Jinja evaluation. |
| `request_admission` | Advanced model request-admission tuning. |

Notes:

- When `disable_early_shutdown=True`, `RunConfig` normalizes `shutdown_error_rate` to `1.0`.
- `progress_bar` is deprecated; use `display_tui`.

## Readiness order

1. `validate` if you only need to confirm config shape.
2. `check_models` when the config references model aliases or MCP tool aliases.
3. `preview` for a quick in-memory sample.
4. `create` when you want persisted artifacts, export, resume, or hub upload.
