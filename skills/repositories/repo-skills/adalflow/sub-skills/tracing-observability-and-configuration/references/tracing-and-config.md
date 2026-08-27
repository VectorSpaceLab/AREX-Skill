# Tracing and config notes

This reference keeps the runtime guidance for this sub-skill in one place so `SKILL.md` can stay router-like.

## What this sub-skill owns

- `setup_env` for `.env` loading and bootstrap order
- `get_logger` and `printc` for local logging and console output
- `GeneratorStateLogger` and `trace_generator_states` for prompt-state history
- `GeneratorCallLogger` and `trace_generator_call` for call records and failed-call artifacts
- trace provider setup with `trace`, `custom_span`, `generator_span`, `response_span`, and `step_span`
- local callback ordering through `CallbackManager` / `Generator.register_callback`
- optional MLflow setup with `enable_mlflow_local` and `enable_mlflow_local_with_server`
- config-file patterns for save locations, trace naming, and artifact cleanup

## Bootstrap order

1. Load environment variables early with `setup_env`.
2. Choose explicit writable directories for logs and traces.
3. Decide whether tracing should be enabled before any spans are created.
4. Configure loggers before running a workflow if you need deterministic file output.
5. Add generator state or call loggers before the generator is used.
6. Enable MLflow only when the optional package is present and the tracking backend is ready.

## Environment and logging defaults

- `setup_env(dotenv_path=".env")` loads the file you point at and raises if it does not exist.
- Existing environment variables are not overwritten.
- `get_adalflow_default_root_path()` resolves to the user root directory for AdalFlow data and logs.
- `get_logger()` uses the AdalFlow root path for the default library log directory when no `save_dir` is provided.
- Named loggers disable propagation so application logs and library logs can be separated cleanly.

## Generator state and call logs

- `GeneratorStateLogger(save_dir=None, project_name=None, filename=None)` writes prompt-state history and deduplicates identical consecutive states.
- `GeneratorCallLogger(save_dir=None, project_name=None)` writes one metadata file plus one JSONL file per registered generator.
- Register generator names before logging calls.
- Prefer a fresh `save_dir` or filename when you want a clean observation run.
- The `trace_generator_states` decorator is best for generators that already exist when the object finishes initializing.
- The `trace_generator_call` decorator is best for repeatable call capture, but it only instruments the current synchronous `call` path.

## Trace provider and spans

- `ADALFLOW_DISABLE_TRACING` controls whether tracing is active.
- The current implementation treats unset / `true` / `1` as disabled.
- Use `set_tracing_disabled(False)` or set the environment variable before creating the provider if you want real spans.
- Use `trace(...)` as the root context for a workflow.
- Use `custom_span(...)` for generic debugging steps.
- Use `generator_span(...)` when you want generator-level metadata, prompt context, or raw response details.
- Use `response_span(...)` for final workflow output evidence.
- Use `step_span(...)` when you want step-by-step execution breadcrumbs.
- Manage processors with `set_trace_processors(...)`, `add_trace_processor(...)`, and `get_trace_processors()`.
- `set_tracing_export_api_key(...)` stores the export key in `ADALFLOW_TRACING_API_KEY` for compatibility.

## Callback order

`Generator._run_callbacks` follows this order:

1. `on_complete`
2. `on_failure` if `GeneratorOutput.error` is set, otherwise `on_success`

That means:

- cleanup or universal tracing belongs in `on_complete`
- success-only debug hooks belong in `on_success`
- failure-only artifacts belong in `on_failure`

`CallbackManager` supports the same event names and preserves registration order inside each event list.

## Optional MLflow setup

- `enable_mlflow_local(...)` is the lightest optional MLflow entry point.
- It returns `False` when MLflow is missing or misconfigured rather than crashing the workflow.
- `enable_mlflow_local_with_server(...)` can start a local server or fall back to an AdalFlow-backed file store.
- `get_mlflow_server_command(...)` returns a ready-to-run server command for a local store.
- When MLflow is absent, the import warning is informational and the rest of the tracing stack still works.

## YAML config pattern

Use YAML when you want a single, human-editable config file for observability settings.
A minimal pattern looks like this:

```yaml
env:
  dotenv_path: .env
logging:
  name: tracing-smoke
  level: INFO
  enable_console: false
  enable_file: true
  filename: tracing-smoke.log
tracing:
  disabled: false
  trace_name: tracing-smoke
  state_project: tracing-smoke
  call_project: tracing-smoke
mlflow:
  enabled: true
  experiment_name: AdalFlow-Tracing-Smoke
  project_name: AdalFlow-Tracing-Smoke
  tracking_uri: null
```

The runtime code should load the YAML, then pass values into `setup_env`, `get_logger`, the generator loggers, and the tracing helpers.

## Artifact hygiene

- Keep logs and traces under a writable project-local or temporary directory.
- Use explicit filenames when you need stable references across runs.
- Remove stale trace folders when you want a clean rerun.
- Do not share absolute private paths in saved artifacts or handoffs.
