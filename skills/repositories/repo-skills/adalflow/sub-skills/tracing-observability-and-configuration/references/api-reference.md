# API reference

This page records the runtime facts that matter for tracing, logging, and observability.

## Environment and logging

| API | Verified behavior |
|---|---|
| `setup_env(dotenv_path: str = ".env")` | Loads the pointed `.env` file, raises `FileNotFoundError` if missing, and does not override existing variables. |
| `get_adalflow_default_root_path() -> str` | Returns the AdalFlow root data directory for the current platform. |
| `get_logger(name=None, level="INFO", save_dir=None, filename=None, enable_console=True, enable_file=True)` | Creates root or named loggers with console/file handlers. The default root logger file is `lib.log`; named loggers use `<name>.log`. |
| `printc(text, color="cyan")` | Prints a timestamped colored console message for quick local debugging. |

## Generator state and call loggers

| API | Verified behavior |
|---|---|
| `GeneratorStateLogger(save_dir=None, project_name=None, filename=None)` | Logs generator prompt states to `./traces/` by default, loads an existing file if present, and only appends when the state changes. |
| `GeneratorCallLogger(save_dir=None, project_name=None)` | Logs generator call records to a project folder under `./traces/` and keeps a metadata file mapping generator names to JSONL files. |
| `trace_generator_states(attributes=None, save_dir="./traces/", project_name=None, filename=None)` | Decorator that discovers generator attributes present at init time and logs their prompt state. |
| `trace_generator_call(attributes=None, save_dir="./traces/", error_only=True)` | Decorator that wraps the synchronous `call` method and logs call records, by default only when the output has an error. |

### Generator logger output locations

| Helper | Default output |
|---|---|
| `GeneratorStateLogger` | `./traces/<project_name>/generator_state_trace.json` |
| `GeneratorCallLogger` | `./traces/<project_name>/logger_metadata.json` plus `<generator_name>_call.jsonl` |

## Callback utility

| API | Verified behavior |
|---|---|
| `CallbackManager.register_callback(event_type, callback)` | Supports `on_success`, `on_failure`, and `on_complete`. Registration order is preserved. |
| `CallbackManager.trigger_callbacks(event_type, *args, **kwargs)` | Invokes registered callbacks in order for that event. |

## Trace provider and spans

| API | Verified behavior |
|---|---|
| `trace(workflow_name, trace_id=None, group_id=None, metadata=None, disabled=False)` | Creates a root trace context for a workflow. |
| `custom_span(...)` | Generic debugging span for ad hoc steps. |
| `generator_span(...)` | Generator-focused span that can carry prompt, raw response, final response, and model metadata. |
| `response_span(...)` | Final response span for end-to-end workflow results. |
| `step_span(...)` | Step-level breadcrumb span for multi-step flows. |
| `runner_span(...)` | Runner-level span for workflow execution summaries. |
| `set_trace_processors(processors)` | Replaces the active processor list. |
| `add_trace_processor(processor)` | Appends a processor to the current processor list. |
| `get_trace_processors()` | Returns a copy of the current processor list. |
| `set_tracing_disabled(disabled: bool)` | Globally enables or disables tracing. |
| `is_tracing_disabled()` | Reports the provider disabled state. |
| `set_tracing_export_api_key(api_key)` | Stores the export key in `ADALFLOW_TRACING_API_KEY` or deletes it when unset. |

## Optional MLflow entry points

| API | Verified behavior |
|---|---|
| `enable_mlflow_local(tracking_uri=None, experiment_name="AdalFlow-Agent-Experiment", project_name="AdalFlow-Agent-Project", port=8080)` | Enables MLflow tracing when MLflow is installed; otherwise logs an informational warning and returns `False`. |
| `enable_mlflow_local_with_server(...)` | Starts or reuses a local server when MLflow is available. |
| `get_mlflow_server_command(host="0.0.0.0", port=8080)` | Returns a ready-to-run local server command that points at the AdalFlow MLflow store. |
| `start_mlflow_server(...)` | Launches a local server helper used by the higher-level MLflow setup. |

## Behavior notes to remember

- `ADALFLOW_DISABLE_TRACING` is read when the provider is created.
- The current implementation treats an unset value as disabled.
- `Generator._run_callbacks` always triggers `on_complete` first, then `on_failure` or `on_success`.
- MLflow is optional, so a missing import should be treated as a supported fallback state.
- Trace and logger output locations are user-owned; pass explicit directories when you need deterministic artifacts.
