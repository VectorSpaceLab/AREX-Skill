# Troubleshooting

Use this guide when the tracing stack looks silent, noisy, or misconfigured.

## Quick checks

1. Confirm the `.env` file exists and the path is correct.
2. Confirm tracing is enabled before the provider or spans are created.
3. Confirm the logger or trace save directory is writable.
4. Confirm the generator name is registered before call logging.
5. Confirm MLflow is optional and only required when you explicitly want that backend.

## Common problems

| Symptom | Likely cause | Recovery |
|---|---|---|
| `setup_env` raises `FileNotFoundError` | The `.env` path is wrong or the file was never created. | Pass the correct path or create a local `.env` file before loading it. |
| Existing env values do not change after loading `.env` | `setup_env` uses `override=False`. | Clear the variable first if you want the file value to win, or use a different key. |
| No log file appears | File logging was disabled, the directory is not writable, or the logger was never used. | Pass `enable_file=True`, point `save_dir` at a writable directory, and flush or close handlers after logging. |
| Logs are too noisy | Console/file handlers are enabled at a low level or the named logger is propagating unexpectedly. | Raise the level, disable console output, or use a named logger with its own handlers. |
| `trace(...)` returns a no-op object | Tracing is still disabled, or the provider never saw an active root trace. | Set `ADALFLOW_DISABLE_TRACING=false`, call `set_tracing_disabled(False)`, and start a root `trace(...)` first. |
| Spans are created but nothing is exported | No processors are registered. | Use `set_trace_processors([processor])` or `add_trace_processor(processor)` before the workflow runs. |
| Trace artifacts appear in an unexpected folder | A default path was used. | Pass explicit `save_dir`, `project_name`, and `filename` values for every logger. |
| `GeneratorStateLogger` does not append a new record | The prompt state is identical to the last saved state, or you reused a preexisting file. | Change the prompt state, use a fresh project name, or start from a clean directory. |
| `GeneratorCallLogger` says the generator is unregistered | The generator name was never registered. | Call `register_generator(name)` before logging. |
| Generator call records seem to leak across runs | The logger keeps shared class-level state in the same interpreter session. | Use a fresh process, a fresh save directory, or call `reset()` and re-register. |
| `trace_generator_states` misses a generator | The attribute was attached after `__init__`, or it is not a `Generator` instance. | Attach the generator before the decorator finishes initialization, or register it manually. |
| `trace_generator_call` misses async-only work | The current decorator wraps the synchronous `call` path. | Trace the async branch separately or log the call manually. |
| `on_success` never runs | The output has an error, so the generator went down the failure branch. | Remember that `on_complete` always runs first, then either `on_success` or `on_failure`. |
| `on_failure` never runs | The output does not have an error. | Check the output object before assuming the failure branch should fire. |
| MLflow import warning appears | MLflow is optional and not installed. | Ignore it if you do not need MLflow, or install the optional extra before enabling MLflow tracing. |
| MLflow enabled but no UI data appears | The tracking URI is wrong or the local backend/server is not ready. | Verify the URI, use the local server helper, or fall back to a local file backend for debugging. |
| Permission denied when writing traces or logs | The target directory is not writable. | Switch to a user-owned temp or project-local directory. |
| Shared artifacts expose private paths | Absolute home or checkout paths were printed into the logs. | Redact paths in reports, use temp directories, and keep shared notes relative. |

## Recommended recovery pattern

- Start with a fresh writable artifact directory.
- Load env vars explicitly.
- Enable tracing before the first trace/span is created.
- Use one root trace per workflow.
- Register callbacks and loggers before the generator or workflow executes.
- Skip MLflow unless the optional package and backend are ready.

## When to stop and inspect

If a workflow still produces no trace or log output after the checks above, inspect:

- the trace processor list
- the active disabled flag
- the generator registration name
- the chosen save directory and filename
- whether a stale file is being reused
