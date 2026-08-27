# Dagster Pipes API Reference

This reference focuses on APIs that future agents need when integrating an external process through Dagster Pipes. Keep asset graph design in `../../asset-definitions/SKILL.md`; this page covers the external process protocol and the minimal Dagster-side bridge.

## Package Split

- External process package: `dagster-pipes`, imported as `dagster_pipes`. It is intentionally lightweight and does not require importing `dagster`.
- Dagster orchestration package: `dagster`, usually imported as `import dagster as dg`, exposes `PipesSubprocessClient`, `PipesEnvContextInjector`, `PipesTempFileMessageReader`, `PipesFileMessageReader`, `PipesCompositeMessageReader`, `open_pipes_session`, and `PipesClientCompletedInvocation`.
- Generic local subprocess path: Dagster asset code calls `dg.PipesSubprocessClient().run(...)`; external Python code wraps work in `with open_dagster_pipes() as pipes:`.

## External Entry Point

```python
from dagster_pipes import open_dagster_pipes

with open_dagster_pipes() as pipes:
    pipes.log.info("external process started")
    pipes.report_asset_materialization(metadata={"row_count": 42})
```

`open_dagster_pipes()`:

- Should be called near the entry point of the process launched by Dagster.
- Defaults to `PipesEnvVarParamsLoader`, `PipesDefaultContextLoader`, and `PipesDefaultMessageWriter`.
- Returns the singleton `PipesContext`; `PipesContext.get()` retrieves it after initialization.
- Emits an inactive warning and returns a no-op mock when the process was not launched with Pipes bootstrap params, which lets scripts remain runnable outside Dagster.
- Acts as a context manager; exiting closes the Pipes connection and flushes buffered messages.

## Context Data Available Externally

`PipesContext` exposes:

- Asset scope: `is_asset_step`, `asset_key`, `asset_keys`, `provenance`, `provenance_by_asset_key`, `code_version`, `code_version_by_asset_key`.
- Partition scope: `is_partition_step`, `partition_key`, `partition_key_range`, `partition_time_window`.
- Run scope: `run_id`, `job_name`, `retry_number`.
- User extras: `extras` and `get_extra(key)`, populated from `PipesSubprocessClient.run(..., extras={...})` or equivalent launcher support.
- Logging: `pipes.log` is a standard `logging.Logger` that streams log messages to Dagster.

Properties that require a single asset or a partition raise `DagsterPipesError` if the current step does not provide that scope. For multi-assets, prefer `asset_keys` and pass explicit `asset_key=` to reporting methods.

## Reporting Methods

### Logs

```python
with open_dagster_pipes() as pipes:
    pipes.log.info("loaded %s rows", row_count)
```

Use `pipes.log.debug/info/warning/error/critical` for structured log levels. `log_external_stream(stream, text, extras=None)` is available for forwarding external stream chunks when building custom integrations.

### Materializations

```python
pipes.report_asset_materialization(
    asset_key="orders",  # required for multi-assets, optional for single-asset scope
    metadata={
        "row_count": 1200,
        "preview": {"type": "md", "raw_value": "| rows |\n| ---: |\n| 1200 |"},
    },
    data_version="orders-2026-06-21",
)
```

Rules:

- The process must be scoped to one or more Dagster assets.
- In a single-asset step, `asset_key` can be omitted.
- In a multi-asset step, pass `asset_key` on every materialization.
- Each asset key can be materialized only once per Pipes invocation.
- Raw metadata values may be `int`, `float`, `str`, `dict`, `list`, `bool`, or `None`; rich metadata uses `{"type": ..., "raw_value": ...}`.

Supported rich metadata type strings include `text`, `url`, `path`, `notebook`, `json`, `md`, `float`, `int`, `bool`, `dagster_run`, `asset`, `null`, `table`, `table_schema`, `table_column_lineage`, and `timestamp`.

### Asset Checks

```python
pipes.report_asset_check(
    check_name="row_count_positive",
    passed=row_count > 0,
    severity="ERROR",
    metadata={"row_count": row_count},
    asset_key="orders",
)
```

Rules:

- `check_name` must match the Dagster-side asset check name.
- `passed` must be a boolean.
- `severity` is `"WARN"` or `"ERROR"`; default is `"ERROR"`.
- `asset_key` is required when there are multiple assets or when the associated check is not inferable from a single asset scope.

### Custom Messages

```python
pipes.report_custom_message({"output_path": "s3://bucket/prefix/file.parquet", "rows": row_count})
```

Custom payloads must be JSON serializable. Dagster-side code reads them from the completed invocation with `response.get_custom_messages()` and can use them to construct outputs, metadata, or follow-up work.

## Params Loaders

### Environment Variables

Default external-side loader:

```python
from dagster_pipes import open_dagster_pipes

with open_dagster_pipes() as pipes:
    ...
```

`PipesEnvVarParamsLoader` reads `DAGSTER_PIPES_CONTEXT` and `DAGSTER_PIPES_MESSAGES`. Use this for ordinary local subprocess launches and any platform where the launcher can inject environment variables.

### CLI Arguments

```python
from dagster_pipes import PipesCliArgsParamsLoader, open_dagster_pipes

with open_dagster_pipes(params_loader=PipesCliArgsParamsLoader()) as pipes:
    ...
```

`PipesCliArgsParamsLoader` reads `--dagster-pipes-context` and `--dagster-pipes-messages` from `sys.argv`. Use it when the launcher cannot set environment variables but can append command-line arguments, such as some notebook, Spark, or existing-cluster launch paths.

### Mapping Loader

`PipesMappingParamsLoader(mapping)` is useful for tests or custom launchers that already have encoded bootstrap params in a mapping. It checks the same keys as the env-var loader.

## Context Loaders and Message Writers

### Defaults

`PipesDefaultContextLoader` reads context either from params key `path` pointing to JSON or `data` containing the context dict directly.

`PipesDefaultMessageWriter` writes messages to params key `path`, `stdio`, or `buffered_stdio`. It can include captured stdout/stderr messages when the orchestration-side reader sets `include_stdio_in_messages`.

This default pair matches the common `PipesSubprocessClient` + temp-file reader path.

### File and Stream Channels

- `PipesFileMessageWriterChannel(path)` writes one JSON Pipes message per line.
- `PipesStreamMessageWriterChannel(stream)` writes one JSON message per line to `stdout` or `stderr`.
- `PipesBufferedStreamMessageWriterChannel(stream)` buffers and flushes messages at close.
- `PipesStdioFileLogWriter` captures stdout and stderr into files named `stdout` and `stderr` in a configured `logs_dir`.

### Blob and Cloud Transports

The external package includes optional context loaders and message writers for S3, GCS, Azure Blob Storage, DBFS, Unity Catalog Volumes, and Databricks notebook widgets. Treat these as protocol options, not guaranteed dependencies:

- Use S3/GCS/Azure blob writers when both orchestration and external process can access the same object store.
- Use DBFS or Unity Catalog Volumes for Databricks-style filesystem exchange.
- Use `PipesCliArgsParamsLoader` for launchers that pass bootstrap data through CLI args instead of env vars.
- Verify provider packages and credentials before writing executable code that imports cloud clients.

## Dagster-Side Subprocess Pattern

```python
import shutil

import dagster as dg

@dg.asset

def external_orders(context: dg.AssetExecutionContext, pipes_subprocess_client: dg.PipesSubprocessClient):
    python = shutil.which("python")
    if python is None:
        raise RuntimeError("python executable not found")

    return pipes_subprocess_client.run(
        command=[python, "external_orders.py"],
        context=context,
        extras={"source": "orders"},
    ).get_materialize_result()


def defs() -> dg.Definitions:
    return dg.Definitions(
        assets=[external_orders],
        resources={"pipes_subprocess_client": dg.PipesSubprocessClient()},
    )
```

Result accessors:

- `get_materialize_result()` for a single materialized asset.
- `get_results()` for multi-assets, checks plus materializations, or yielding multiple Dagster events.
- `get_asset_check_result()` when the external process reports a single asset check.
- `get_custom_messages()` to retrieve payloads sent with `report_custom_message`.

If using lower-level `dg.open_pipes_session(...)`, launch the process inside the session, then `yield from pipes_session.get_results()` during and/or after process completion so buffered messages become Dagster events.

## Non-Python Process Strategy

Non-Python processes do not import `dagster_pipes`, but they can still emit protocol messages if a wrapper supplies bootstrap params and the process writes JSON-line messages to the configured stream or file. The safe message shape is:

```json
{"__dagster_pipes_version":"0.1","method":"report_custom_message","params":{"payload":{"status":"ok"}}}
```

Prefer a thin Python wrapper using `open_dagster_pipes()` when possible; it handles encoded params, open/closed messages, metadata normalization, logging, and inactive no-op behavior. Use direct JSON messages only when a non-Python executable cannot be wrapped.
