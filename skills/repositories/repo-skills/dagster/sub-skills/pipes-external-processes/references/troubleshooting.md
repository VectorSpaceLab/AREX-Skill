# Dagster Pipes Troubleshooting

Use this guide when an external process runs but Dagster does not show the expected materializations, checks, logs, or custom messages.

## Import and Install Failures

### `ModuleNotFoundError: No module named 'dagster_pipes'`

Cause: the external process environment does not include the lightweight `dagster-pipes` package.

Fix:

- Install `dagster-pipes` in the environment used by the external script, not only in the Dagster orchestration environment.
- Keep external scripts importing `dagster_pipes`, not `dagster`, unless they intentionally run in the Dagster project environment.
- If the process is remote or containerized, rebuild that image/environment after adding the dependency.

### `ImportError` for S3, GCS, Azure, DBFS, Spark, or Databricks helpers

Cause: cloud/blob writers and some platform loaders require optional provider packages or runtime services.

Fix:

- Verify provider imports before choosing a cloud transport.
- For local subprocesses, use default temp-file transport instead of a cloud writer.
- For Databricks/DBFS/Spark paths, verify `pyspark`, `py4j`, and an active platform session when the selected writer requires them.
- Do not import optional provider clients at module import time in scripts that should also run locally; import them only inside the branch that uses that transport.

## Inactive Pipes Warnings

### Warning that the process was not launched by Dagster

Cause: `open_dagster_pipes()` did not find Pipes bootstrap params. This is expected when running the script directly.

Fix:

- For a direct local script run, treat the warning as safe; the returned mock makes calls no-ops.
- For a Dagster-launched subprocess, verify `PipesSubprocessClient.run(..., context=context)` is called with the real execution context.
- Confirm the external code uses the same params loader as the launcher: default env vars for `DAGSTER_PIPES_CONTEXT`/`DAGSTER_PIPES_MESSAGES`, or `PipesCliArgsParamsLoader()` for `--dagster-pipes-context`/`--dagster-pipes-messages`.

## Missing `DAGSTER_PIPES_*` Params

Symptoms:

- Inactive warning during a Dagster run.
- External process runs, but no materialization/check/log messages appear.
- `PipesCliArgsParamsLoader` says expected CLI args are missing.

Fix checklist:

1. Dagster side passes `context=context` into the Pipes client `run` call.
2. External process is launched by the Pipes client, not by a nested command that drops env vars or CLI args.
3. If using env vars, subprocess environment merges the injected env with custom env values instead of replacing it completely.
4. If using CLI args, external code passes `params_loader=PipesCliArgsParamsLoader()` and the launcher appends the two `--dagster-pipes-*` args.
5. If using a wrapper script, the wrapper forwards env vars or CLI args to the real child process when the child imports `dagster_pipes`.

## Loader and Writer Mismatches

### Context loader cannot find `path` or `data`

Cause: `PipesDefaultContextLoader` received params that do not contain `path` or `data`, or the orchestration-side context injector does not match the external loader.

Fix:

- Use default `open_dagster_pipes()` with default local `PipesSubprocessClient` first.
- If customizing, pair the orchestration-side context injector with the external-side context loader intentionally.
- For blob/cloud contexts, verify both sides can read/write the same object location.

### Message writer cannot find `path`, `stdio`, or `buffered_stdio`

Cause: `PipesDefaultMessageWriter` received params from an incompatible message reader.

Fix:

- Use `PipesTempFileMessageReader` or another reader that produces params understood by the writer.
- If using stdout/stderr protocol messages, keep unrelated prints out of the same stream or use buffered/file transport instead.
- If using blob writers, match the external writer with the orchestration-side blob reader.

## Dagster-Side Results Do Not Appear

### Messages are sent, but no Dagster events are yielded

Cause: the asset did not return or yield the completed invocation results.

Fix:

- Single materialization: `return pipes_subprocess_client.run(...).get_materialize_result()`.
- Multi-event invocation: `return pipes_subprocess_client.run(...).get_results()`.
- Lower-level session: call `yield from pipes_session.get_results()` after the `open_pipes_session` block closes, and optionally while the process is running.

### `get_materialize_result()` fails for multi-assets or mixed results

Cause: the completed invocation contains zero, multiple, or non-materialization events.

Fix:

- Use `get_results()` for multi-assets and mixed materialization/check streams.
- Use `get_asset_check_result()` for a single check result.
- Use `get_custom_messages()` for custom payloads; custom messages are not materialization results.

## Asset Key and Check Name Problems

### Duplicate materialization error

Message resembles: `Asset has already been materialized, so no additional data can be reported for it`.

Cause: `report_asset_materialization` was called more than once for the same asset key in one Pipes invocation.

Fix:

- Aggregate metadata and call `report_asset_materialization` once per asset key.
- For incremental progress, use `pipes.log` or `report_custom_message` before the final materialization.

### Unknown or undefined asset key

Cause: the external process reported an `asset_key` that is not in the current Dagster step, or omitted `asset_key` in a multi-asset step.

Fix:

- Use `pipes.asset_key` only for a single-asset step.
- Use `pipes.asset_keys` to inspect multi-asset scope.
- Pass `asset_key="..."` exactly matching the Dagster asset key string for every multi-asset event.

### Asset check result missing

Cause: `check_name` or `asset_key` does not match the Dagster-side asset check definition, or the Dagster-side code used the wrong result accessor.

Fix:

- Match `check_name` exactly.
- Pass `asset_key` when checks are associated with a specific asset or when multiple assets are in scope.
- Return `get_asset_check_result()` for one check or `get_results()` for mixed events.

## Metadata and Custom Payload Failures

### Metadata serialization errors

Cause: metadata or custom messages contain values that are not JSON serializable, or rich metadata dictionaries use the wrong shape.

Fix:

- Convert `datetime`, `Decimal`, `Path`, numpy/pandas objects, and custom classes to strings, numbers, lists, or dictionaries.
- For rich metadata, use `{"type": "json", "raw_value": {...}}`, `{"type": "url", "raw_value": "example destination"}`, `{"type": "md", "raw_value": "..."}`, and similar supported type strings.
- Keep `report_custom_message` payloads JSON serializable.

## Closed Context and Lifecycle Errors

### `Cannot send message after pipes context is closed`

Cause: code calls `pipes.report_*` or `pipes.log` after leaving the `with open_dagster_pipes()` block or after `close()`.

Fix:

- Keep all reporting inside the context manager.
- If helper functions need the context, pass `pipes` into them or call `PipesContext.get()` while still inside the context.
- Do not keep global references to a `PipesContext` across process invocations.

### Exceptions in external code do not show useful details

Fix:

- Let exceptions propagate out of the `with open_dagster_pipes()` block when the run should fail; the context manager records exception information in the close message.
- Log important external state before raising.
- Avoid swallowing exceptions and returning success unless the Dagster asset should succeed.

## Subprocess Command Misuse

Symptoms:

- Command works in a shell but fails from Dagster.
- `python` executable cannot be found.
- Quoting differs between local shells and Dagster runs.

Fix:

- Pass `command` as a list, not a shell string.
- Use `shutil.which("python")` or an explicit executable appropriate for the target environment.
- Avoid `shell=True` unless the user explicitly needs shell features and understands injection risks.
- Ensure relative script paths are resolved from the working directory used by the Dagster code location.

## Workflow-Specific Debugging

### Retrofitting an existing script

- Start with only `with open_dagster_pipes() as pipes:` and `pipes.log.info("started")`.
- Run directly once to confirm inactive behavior is safe.
- Run through Dagster and confirm the log appears before adding materializations/checks.
- Add one final materialization or check after the external work succeeds.

### Choosing env vs CLI params

- If env vars are absent in the child process, inspect whether custom `env={...}` replaced inherited env values.
- If CLI args are absent, inspect whether the launcher appended args to the wrapper but the wrapper failed to forward them to the real script.
- Prefer env vars for local subprocesses; use CLI args for launchers that cannot mutate env vars.

### Non-Python direct JSON messages

- Validate each emitted line with a JSON parser.
- Include `__dagster_pipes_version` with value `0.1`.
- Use method names such as `log`, `report_asset_materialization`, `report_asset_check`, and `report_custom_message`.
- Keep unrelated process output separate from the protocol stream when using stdout/stderr message writing.
