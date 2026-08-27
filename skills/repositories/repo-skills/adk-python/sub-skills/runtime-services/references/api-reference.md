# Runtime Services API Reference

This reference summarizes the ADK runtime-service surfaces a coding agent usually needs after `google-adk` is installed. It assumes `google-adk` 2.3.0, import root `google.adk`, and Python 3.10+.

## Import Map

| Need | Preferred imports | Notes |
| --- | --- | --- |
| Public root APIs | `from google.adk import Agent, Runner, Workflow` | `Runner` is exported at the package root; `InMemoryRunner` is in `google.adk.runners`. |
| Application container | `from google.adk.apps.app import App`; `from google.adk.apps import EventsCompactionConfig, ResumabilityConfig` | `App` validates its name and requires a root agent/node. |
| Session services | `from google.adk.sessions import InMemorySessionService, DatabaseSessionService`; `from google.adk.sessions.sqlite_session_service import SqliteSessionService` | `DatabaseSessionService` requires the DB extra/SQLAlchemy; `SqliteSessionService` uses `aiosqlite`. |
| Memory services | `from google.adk.memory import InMemoryMemoryService, BaseMemoryService` | Vertex memory services require cloud setup and credentials. |
| Artifact services | `from google.adk.artifacts import InMemoryArtifactService, BaseArtifactService, FileArtifactService, GcsArtifactService` | GCS requires cloud dependencies and credentials. |
| Plugins | `from google.adk.plugins import BasePlugin, PluginManager, LoggingPlugin, DebugLoggingPlugin` | Plugins are app-wide and run before agent callbacks. |
| Telemetry | `from google.adk.telemetry import TelemetryConfig, ContentCapturingMode, tracer` | OTel setup can also read standard `OTEL_*` environment variables. |
| Code executors | `from google.adk.code_executors import BuiltInCodeExecutor, UnsafeLocalCodeExecutor, ContainerCodeExecutor` | Container/GKE/Vertex/Agent Engine executors require extension/cloud dependencies and infrastructure. |
| Environments | `from google.adk.environment import BaseEnvironment, LocalEnvironment, ExecutionResult` | Environment APIs are experimental. |

## Runner And App

`Runner` is the runtime lifecycle orchestrator: it creates invocation context, resolves sessions, runs plugin callbacks, persists non-partial events through the session service, wires memory/artifact/credential services into contexts, and closes plugins/toolsets. Workflow/node scheduling is separate; do not bypass the runner when persistence or plugins matter.

```python
Runner(
    *,
    app=None,
    app_name=None,
    agent=None,
    node=None,
    plugins=None,
    artifact_service=None,
    session_service,
    memory_service=None,
    credential_service=None,
    plugin_close_timeout=5.0,
    auto_create_session=False,
)
```

Key constructor rules:

- Provide exactly one of `app`, `agent`, or `node`; when passing `agent`, also pass `app_name`.
- Prefer `App(name=..., root_agent=..., plugins=[...])` for app-wide plugin configuration.
- `plugins=` on `Runner` is deprecated when `App` can own plugins; do not pass both `app` and `plugins`.
- `auto_create_session=False` means a missing session raises; set it deliberately or create a session first.

`App` fields:

```python
App(
    name: str,
    root_agent: BaseAgent | BaseNode,
    plugins: list[BasePlugin] = [],
    events_compaction_config: EventsCompactionConfig | None = None,
    context_cache_config: ContextCacheConfig | None = None,
    resumability_config: ResumabilityConfig | None = None,
)
```

`App.name` must start with a letter and contain only letters, digits, underscores, and hyphens; `user` is reserved.

Runner methods to know:

- `Runner.run(user_id=..., session_id=..., new_message=..., state_delta=None, run_config=None)` is a synchronous convenience generator and is mainly for local testing.
- `Runner.run_async(user_id=..., session_id=..., invocation_id=None, new_message=None, state_delta=None, run_config=None, yield_user_message=False)` is the main async event stream.
- `Runner.run_live(user_id=..., session_id=..., live_request_queue=..., run_config=None, session=None)` is experimental live-mode streaming; raw live media inline blobs are not always saved to sessions.
- `Runner.run_debug(user_messages, user_id='debug_user_id', session_id='debug_session_id', quiet=False, verbose=False)` creates/continues a debug session and returns collected events.
- `Runner.rewind_async(user_id=..., session_id=..., rewind_before_invocation_id=...)` appends a rewind event with state/artifact deltas.
- `await Runner.close()` closes toolsets, closes plugins through `PluginManager`, and flushes the session service; `Runner` also supports `async with`.

`InMemoryRunner(agent=None, *, node=None, app_name=None, plugins=None, app=None, plugin_close_timeout=5.0)` supplies `InMemorySessionService`, `InMemoryMemoryService`, and `InMemoryArtifactService`; use it for development and tests, not durable production state.

## Session Services

`BaseSessionService` defines:

- `create_session(app_name, user_id, state=None, session_id=None) -> Session`
- `get_session(app_name, user_id, session_id, config=None) -> Session | None`
- `list_sessions(app_name, user_id=None) -> ListSessionsResponse`
- `delete_session(app_name, user_id, session_id) -> None`
- `get_user_state(app_name, user_id) -> dict[str, Any]` when implemented
- `append_event(session, event) -> Event`
- `flush()` for buffered implementations

`GetSessionConfig(num_recent_events=None, after_timestamp=None)` controls how many historical events are fetched. `num_recent_events=0` returns no events.

State scopes:

- Plain keys are session-scoped.
- `app:` keys are shared across sessions for an app.
- `user:` keys are shared across sessions for one user within one app.
- `temp:` keys are applied to the in-memory session for the current invocation but trimmed before persistence.

Persistence behavior:

- Partial events are not appended by base session services.
- `Runner` appends user/model/tool/control events; manually calling `append_event` can skip plugin callbacks and runner bookkeeping.
- `InMemorySessionService` returns copied sessions, merges app/user state into each fetched session, and is not suitable for multi-threaded production environments.
- `SqliteSessionService(db_path)` stores sessions/events in SQLite through `aiosqlite`, creates its current schema automatically, and raises a migration message if an older SQLite schema is detected.
- `DatabaseSessionService(db_url=...)` or `DatabaseSessionService(db_engine=...)` uses SQLAlchemy async engines, creates/checks tables lazily, detects stale appenders, and should be closed if it owns the engine.

`DatabaseSessionService` optional-extra facts:

- Importing or constructing it without SQLAlchemy raises an error that points to the `db` extra, for example `pip install "google-adk[db]"`.
- It accepts exactly one of `db_url` or `db_engine`.
- For non-SQLite database URLs, required async drivers and network access are caller responsibilities.

## Memory Services

`BaseMemoryService` defines long-term recall APIs:

- `add_session_to_memory(session)` ingests a session and may be called multiple times.
- `add_events_to_memory(app_name=..., user_id=..., events=..., session_id=None, custom_metadata=None)` ingests an event delta when implemented.
- `add_memory(app_name=..., user_id=..., memories=..., custom_metadata=None)` directly writes memory entries when implemented.
- `search_memory(app_name=..., user_id=..., query=...) -> SearchMemoryResponse` returns `MemoryEntry` items.

`InMemoryMemoryService` is thread-safe but intended for testing/development. It keyword-matches text parts from stored events; it is not semantic search and not durable.

## Artifact Services

`BaseArtifactService` stores `google.genai.types.Part` artifacts keyed by app, user, optional session, filename, and version:

- `save_artifact(app_name, user_id, filename, artifact, session_id=None, custom_metadata=None) -> int`
- `load_artifact(app_name, user_id, filename, session_id=None, version=None) -> Part | None`
- `list_artifact_keys(app_name, user_id, session_id=None) -> list[str]`
- `delete_artifact(app_name, user_id, filename, session_id=None) -> None`
- `list_versions(...) -> list[int]`
- `list_artifact_versions(...) -> list[ArtifactVersion]`
- `get_artifact_version(...) -> ArtifactVersion | None`

Artifact scope rules:

- A filename starting with `user:` is user-scoped and does not require `session_id`.
- Other filenames are session-scoped and require `session_id`.
- Versions start at `0` and increment per saved artifact.
- `InMemoryArtifactService` stores `inline_data`, `text`, valid artifact references, or `file_data` metadata in process memory only.

## Plugins

`BasePlugin(name)` is an app-wide callback surface. `PluginManager` registers plugins in order and stops a callback chain early when a plugin returns a non-`None` value.

Core callback names:

- `on_user_message_callback(invocation_context, user_message)`
- `before_run_callback(invocation_context)`
- `on_event_callback(invocation_context, event)`
- `after_run_callback(invocation_context)`
- `before_agent_callback(agent, callback_context)` and `after_agent_callback(...)`
- `before_model_callback(callback_context, llm_request)` and `after_model_callback(...)`
- `on_model_error_callback(callback_context, llm_request, error)`
- `before_tool_callback(tool, tool_args, tool_context)` and `after_tool_callback(...)`
- `on_tool_error_callback(tool, tool_args, tool_context, error)`
- `close()` for plugin cleanup

Operational notes:

- Plugin callbacks run in registration order.
- Plugins take precedence over agent callbacks.
- Returning a value short-circuits later plugins and agent callbacks for that callback point.
- `on_event_callback` runs before the runner persists the output event; this is the correct place to observe or carefully modify persisted events.
- Plugin names must be unique inside a `PluginManager`.
- `PluginManager.close()` calls plugin `close()` methods sequentially with `close_timeout`.

## Telemetry And Logging

- Use the `google_adk` logger namespace for runtime logs.
- ADK tracing uses OpenTelemetry; `google.adk.telemetry.tracer` provides the tracer object used around invocations, model calls, tool calls, and data sending.
- `maybe_set_otel_providers(...)` can configure OTel providers with explicit hooks and also reads standard OTLP variables such as `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`, `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT`, and `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT`.
- The architecture separates Runner, NodeRunner, and Workflow: Runner owns invocation spans and lifecycle; NodeRunner creates child node spans; Workflow owns graph traversal.
- In concurrent asyncio runtimes, prefer explicit span propagation through context objects instead of relying on implicit global current spans.

## Code Executors And Environments

`BaseCodeExecutor` fields include:

- `optimize_data_file=False` for extracting supported data files such as CSV.
- `stateful=False` for retaining execution state when supported.
- `error_retry_attempts=2`.
- `code_block_delimiters=[('```tool_code\n', '\n```'), ('```python\n', '\n```')]`.
- `execution_result_delimiters=('```tool_output\n', '\n```')`.
- `timeout_seconds=None`.
- `execute_code(invocation_context, code_execution_input) -> CodeExecutionResult`.

Executor choices:

- `BuiltInCodeExecutor` is used automatically in some code-execution flows such as CFC support when compatible.
- `UnsafeLocalCodeExecutor` runs Python code in a spawned local process and is explicitly unsafe for untrusted model output. It forbids `stateful=True` and `optimize_data_file=True`.
- `ContainerCodeExecutor(image=... | docker_path=..., base_url=None, timeout_seconds=...)` requires Docker availability and extension dependencies; it starts and later cleans up a container.
- `VertexAiCodeExecutor`, `GkeCodeExecutor`, and `AgentEngineSandboxCodeExecutor` require extension/cloud dependencies plus cloud credentials, project, location, and service prerequisites.

`BaseEnvironment` and `LocalEnvironment` are experimental. Lifecycle is: construct, `await initialize()`, use `execute`/`read_file`/`write_file`, then `await close()`. `LocalEnvironment` runs shell commands in a working directory and can create/remove a temporary workspace; treat it as high-trust local execution.

## Credential And Cloud Service Surfaces

`Runner` can receive `credential_service` and passes it into invocation context. Cloud session, memory, artifact, telemetry, and code-execution services may need credentials, enabled APIs, project/location configuration, and optional extras. Missing credentials or disabled APIs are configuration facts, not base-install bugs.

## Validation Commands

Use the bundled diagnostic for safe local inspection:

```bash
python sub-skills/runtime-services/scripts/check_runtime_services.py
python sub-skills/runtime-services/scripts/check_runtime_services.py --json
```

The diagnostic prints imports, signatures, and optional DB-extra availability. It does not open databases, call network services, read credentials, or start executors.
