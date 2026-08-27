# Dagster Pipes Workflows

Use these workflows to connect external processes to Dagster while keeping the external code mostly independent of Dagster internals.

## Retrofit an Existing Python Script

1. Install or declare the lightweight `dagster-pipes` package in the external script environment.
2. Add `from dagster_pipes import open_dagster_pipes` near the script entry point.
3. Wrap the script body, not top-level imports, in `with open_dagster_pipes() as pipes:`.
4. Replace important `print` status messages with `pipes.log.info(...)` where they should appear in Dagster event logs.
5. Report Dagster events at stable completion boundaries with `report_asset_materialization`, `report_asset_check`, or `report_custom_message`.
6. Keep the script runnable outside Dagster; inactive `open_dagster_pipes()` returns a no-op mock and emits a warning instead of failing.

Example external code:

```python
from dagster_pipes import open_dagster_pipes


def main() -> None:
    with open_dagster_pipes() as pipes:
        source = pipes.extras.get("source", "default")
        rows = run_existing_pipeline(source)
        pipes.log.info("processed %s rows from %s", rows, source)
        pipes.report_asset_materialization(metadata={"row_count": rows, "source": source})


if __name__ == "__main__":
    main()
```

Keep broad asset topology, resource configuration, and `Definitions` details in `../../asset-definitions/SKILL.md` and `../../configuration-resources/SKILL.md`; this workflow only covers the external process boundary.

## Define a Local Subprocess Asset

1. In Dagster code, define an asset that accepts `context: dg.AssetExecutionContext` and a `dg.PipesSubprocessClient` resource.
2. Build a command list with the executable and script path. Do not shell-concatenate user input.
3. Pass `context=context` so Dagster can inject run, asset, partition, and message-channel bootstrap data.
4. Pass `extras={...}` for user-defined values the external process can access via `pipes.extras` or `pipes.get_extra(key)`.
5. Return the right completed-invocation accessor.

```python
import shutil

import dagster as dg

@dg.asset
def external_orders(context: dg.AssetExecutionContext, pipes_subprocess_client: dg.PipesSubprocessClient):
    python = shutil.which("python")
    if python is None:
        raise RuntimeError("python executable not found")
    response = pipes_subprocess_client.run(
        command=[python, "external_orders.py"],
        context=context,
        extras={"source": "orders"},
    )
    return response.get_materialize_result()
```

Accessor choice:

- Use `get_materialize_result()` for exactly one asset materialization.
- Use `get_results()` for multi-assets or when yielding multiple Dagster events.
- Use `get_asset_check_result()` for one externally reported check.
- Use `get_custom_messages()` before returning a materialization result when the external process sends auxiliary payloads for orchestration code.

## Report Multi-Asset Results

External code must pass `asset_key` explicitly and cannot report the same asset key twice in one Pipes invocation.

```python
with open_dagster_pipes() as pipes:
    for name, row_count in compute_tables().items():
        pipes.report_asset_materialization(
            asset_key=name,
            metadata={"row_count": row_count},
        )
```

Dagster-side code should return or yield `get_results()` rather than `get_materialize_result()` because there are multiple events.

```python
@dg.multi_asset(specs=[dg.AssetSpec("orders"), dg.AssetSpec("customers")])
def external_tables(context: dg.AssetExecutionContext, pipes_subprocess_client: dg.PipesSubprocessClient):
    return pipes_subprocess_client.run(command=["python", "external_tables.py"], context=context).get_results()
```

## Report Asset Checks from External Code

1. Define the Dagster-side `@asset_check` or check specs in the asset layer.
2. In external code, call `pipes.report_asset_check(check_name=..., passed=..., asset_key=...)`.
3. On the Dagster side, call `get_asset_check_result()` for a single check or `get_results()` when mixed with other events.

```python
with open_dagster_pipes() as pipes:
    rows = validate_output()
    pipes.report_asset_check(
        asset_key="orders",
        check_name="row_count_positive",
        passed=rows > 0,
        severity="ERROR",
        metadata={"row_count": rows},
    )
```

If the check result never appears, verify that the check name and asset key match the Dagster-side definition exactly.

## Pass Custom Data Back to Dagster

Use custom messages for data that orchestration code needs but that is not itself a Dagster event.

External code:

```python
with open_dagster_pipes() as pipes:
    output_path = write_external_file()
    pipes.report_custom_message({"output_path": output_path})
    pipes.report_asset_materialization(metadata={"output_path": {"type": "path", "raw_value": output_path}})
```

Dagster side:

```python
response = pipes_subprocess_client.run(command=["python", "external_writer.py"], context=context)
messages = response.get_custom_messages()
context.log.info("external payloads: %s", messages)
return response.get_materialize_result()
```

Custom messages must be JSON serializable. Convert datetimes, decimals, paths, and custom classes to strings or dictionaries before reporting.

## Choose Env Vars vs CLI Args

Prefer env vars when the launcher can inject environment variables:

```python
with open_dagster_pipes() as pipes:
    ...
```

Use CLI args when the external platform only supports passing arguments:

```python
from dagster_pipes import PipesCliArgsParamsLoader, open_dagster_pipes

with open_dagster_pipes(params_loader=PipesCliArgsParamsLoader()) as pipes:
    ...
```

Decision guide:

- Local subprocess: default env-var loader is usually correct.
- Service accepts environment variables and local/temp files or shared files: default loader and writer often work.
- Service accepts command arguments but not env vars: `PipesCliArgsParamsLoader`.
- Service cannot share local files with Dagster: use a blob-store context loader/message writer pair that both sides can access.
- Existing Databricks cluster or Spark-like launch that cannot mutate env vars: often CLI args plus DBFS/S3/volume writers.

## Choose Message Writer and Reader Transport

Default local subprocess:

- Orchestration side: `dg.PipesSubprocessClient()` with default `PipesTempFileMessageReader`.
- External side: `open_dagster_pipes()` with default `PipesDefaultMessageWriter`.

File/stdio variants:

- Use temp-file reading/writing for local processes where both sides share a filesystem.
- Use stdout/stderr writing only when the launcher captures those streams reliably and does not mix unrelated output with protocol messages.
- Use `include_stdio_in_messages` through the orchestration-side reader when stdout/stderr should be forwarded as Pipes log messages.

Blob/cloud variants:

- Match the orchestration-side reader/context injector with the external-side loader/writer.
- Verify optional package imports and credentials before coding against S3, GCS, Azure Blob Storage, DBFS, or Unity Catalog Volumes.
- Increase polling intervals for expensive object stores if logs are high volume.

## Adapt a Non-Python Process

Preferred approach: add a tiny Python wrapper that opens Pipes, launches the non-Python command, captures its result, and reports Dagster events.

```python
import subprocess

from dagster_pipes import open_dagster_pipes

with open_dagster_pipes() as pipes:
    completed = subprocess.run(["./external_binary", "--json"], check=True, capture_output=True, text=True)
    pipes.log.info(completed.stdout)
    pipes.report_asset_materialization(metadata={"exit_code": completed.returncode})
```

Direct JSON-line protocol approach:

- Only use when a wrapper is impossible.
- Emit one JSON object per line to the writer-selected file or stream.
- Include `__dagster_pipes_version`, `method`, and `params`.
- Emit valid JSON; no comments, trailing commas, or non-serializable values.

Minimal custom message:

```json
{"__dagster_pipes_version":"0.1","method":"report_custom_message","params":{"payload":{"status":"ok"}}}
```

## Safe Local Smoke Check

This sub-skill includes `scripts/pipes_external_smoke.py`.

```bash
python scripts/pipes_external_smoke.py --help
python scripts/pipes_external_smoke.py --inactive-demo
python scripts/pipes_external_smoke.py --emit-json-message
```

The script does not launch Dagster, access cloud services, or require credentials. It demonstrates the inactive no-op behavior and the JSON-line message shape a non-Python process would need to emit.
