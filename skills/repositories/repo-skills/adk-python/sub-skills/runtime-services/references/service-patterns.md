# Runtime Service Patterns

Use these patterns to configure ADK runtime services safely and to reason about service ownership. Keep examples minimal and adapt names, models, and tools in the caller's codebase.

## Minimal In-Memory Runtime

Use this for local experimentation, unit tests, and narrow debugging:

```python
from google.adk import Agent
from google.adk.runners import InMemoryRunner

agent = Agent(name="assistant", model="gemini-2.0-flash")
runner = InMemoryRunner(agent=agent, app_name="demo_app")
session = await runner.session_service.create_session(
    app_name=runner.app_name,
    user_id="alice",
    session_id="debug-session",
)
```

Then stream with `runner.run_async(user_id="alice", session_id=session.id, new_message=...)`. Use `run_debug(...)` for local convenience when detailed session control is not needed.

Why this pattern is safe:

- No databases, cloud services, credentials, or network services are started by the runtime services themselves.
- Session, memory, and artifacts are process-local and vanish with the process.
- It exercises runner/plugin/event wiring before introducing persistence.

## Explicit Runner With Services

Use explicit services when you need to swap in persistence, artifacts, memory, or credentials:

```python
from google.adk.apps.app import App
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService

app = App(name="support_bot", root_agent=root_agent, plugins=[audit_plugin])
runner = Runner(
    app=app,
    session_service=InMemorySessionService(),
    memory_service=InMemoryMemoryService(),
    artifact_service=InMemoryArtifactService(),
    auto_create_session=False,
)
```

Checklist:

- Create or fetch a session before `run_async`, or set `auto_create_session=True` intentionally.
- Let `Runner` append user and model/tool events; do not persist events in parallel from a plugin.
- Use `async with Runner(...) as runner:` or `await runner.close()` for long-lived apps.
- Keep `app.name`, session `app_name`, and CLI app identity aligned; mismatches cause missing-session symptoms.

## In-Memory Versus Persistent Sessions

Choose service by lifecycle:

| Scenario | Service | Trade-offs |
| --- | --- | --- |
| Unit tests, examples, local debugging | `InMemorySessionService` | Fast and dependency-light; not durable or multi-process safe. |
| Local durable SQLite file without SQLAlchemy | `SqliteSessionService(db_path)` | File-backed JSON event persistence; detects old SQLite schema and asks for migration. |
| Async SQLAlchemy database URL/engine | `DatabaseSessionService(db_url=...)` or `DatabaseSessionService(db_engine=...)` | Supports database backends and stale-writer checks; requires `google-adk[db]`, async drivers, and migration discipline. |
| Managed cloud/session service | `VertexAiSessionService` or similar cloud services | Requires optional dependencies, credentials, project/location, service enablement, and quota. |

Non-destructive migration discipline:

1. Identify which service created the existing store (`SqliteSessionService` old schema versus SQLAlchemy `DatabaseSessionService`).
2. Back up the database before any migration.
3. Confirm optional DB dependencies are installed with the diagnostic script or a direct import check.
4. Prefer documented migration modules or one-off migration tooling in a throwaway copy before touching production data.
5. Do not run migration commands from a live app process that may also be appending events.

## State And Event Persistence

`Runner` appends events in a deliberate order:

1. Plugins may modify the user message through `on_user_message_callback`.
2. Runner appends the user event and optional `state_delta` to the session.
3. Agent/workflow execution produces events.
4. `on_event_callback` runs before event persistence.
5. Non-partial output events are appended by the session service and yielded to the caller.
6. `after_run_callback` runs for cleanup; event compaction may run after the invocation when configured.

State key rules:

- Use plain keys for session-local state.
- Use `user:profile` style keys for user-wide state.
- Use `app:feature_flag` style keys for app-wide state.
- Use `temp:intermediate` for same-invocation scratch state that must not persist.

Persistence checks when events are missing:

- Verify the caller fully iterates the `run_async` generator; stopping early cancels the root task and may skip later events.
- Check `event.partial`; partial events are yielded but not persisted by session services.
- Check live mode: raw live media inline data is yielded but not saved as session event data.
- Confirm the event is coming through `Runner`, not a manual call path that bypasses plugin/event persistence logic.
- Confirm `app_name`, `user_id`, and `session_id` match the session used by the service.

## Memory Ingestion Pattern

Memory is not the same as session persistence. Sessions store conversation/event history; memory services make selected history searchable later.

Typical flow:

```python
session = await runner.session_service.get_session(
    app_name=runner.app_name,
    user_id="alice",
    session_id="debug-session",
)
if session and runner.memory_service:
    await runner.memory_service.add_session_to_memory(session)
    response = await runner.memory_service.search_memory(
        app_name=runner.app_name,
        user_id="alice",
        query="billing address",
    )
```

Guidance:

- Ingest after the events you care about have been persisted.
- Prefer `add_events_to_memory(...)` only when the chosen implementation supports event deltas.
- Treat in-memory memory search as keyword matching, not semantic recall.
- For cloud memory services, validate credentials, APIs, project/location, and data retention assumptions before use.

## Artifact Pattern

Artifacts are versioned files associated with app/user/session scope. Use an artifact service when files, blobs, generated data, or live audio references need to survive outside model text.

```python
from google.genai import types

version = await runner.artifact_service.save_artifact(
    app_name=runner.app_name,
    user_id="alice",
    session_id="debug-session",
    filename="report.txt",
    artifact=types.Part(text="summary"),
)
loaded = await runner.artifact_service.load_artifact(
    app_name=runner.app_name,
    user_id="alice",
    session_id="debug-session",
    filename="report.txt",
    version=version,
)
```

Guidance:

- Use `user:filename.ext` for user-scoped artifacts that should be available without a session ID.
- Use ordinary filenames plus `session_id` for session-scoped artifacts.
- Inspect `ArtifactVersion` metadata when debugging MIME type, custom metadata, or canonical URI concerns.
- Do not store secrets in artifact contents unless the backing service and retention policy are approved.

## Plugin Observation Pattern

Use plugins for app-wide observability and policy; use agent callbacks for agent-local behavior.

```python
from google.adk.plugins import BasePlugin

class AuditPlugin(BasePlugin):
    def __init__(self):
        super().__init__(name="audit")

    async def on_event_callback(self, *, invocation_context, event):
        # Observe before persistence. Return None to keep the original event.
        print(event.author, event.id)
        return None

    async def before_tool_callback(self, *, tool, tool_args, tool_context):
        # Return None unless intentionally short-circuiting the tool call.
        return None
```

Rules that prevent event-loss bugs:

- Register plugins on `App(plugins=[...])` when constructing new code.
- Keep plugin names unique.
- Return `None` for pure observation. Returning content/dicts/events short-circuits later callbacks or replaces outputs.
- Avoid calling `session_service.append_event` inside `on_event_callback`; the runner persists the output event after callbacks.
- If modifying an event, preserve semantic fields such as author, invocation, branch/isolation, function call IDs, and actions unless the task explicitly requires changing them.
- Put slow I/O behind async clients and timeouts; a plugin callback runs in the invocation path.

## Telemetry And Logs Pattern

For ordinary logging:

```python
import logging

logger = logging.getLogger("google_adk.my_app.runtime")
logger.info("session started: %s", session_id)
```

For OTel export, configure standard OTel environment variables or explicit OTel hooks before starting invocations. The runtime creates invocation and child spans; future agents should avoid adding global implicit-span assumptions in concurrent tasks.

Checks:

- Confirm `OTEL_EXPORTER_OTLP_ENDPOINT` or specific trace/metric/log endpoints are set before process startup.
- Confirm the application has permission/network access to the collector.
- Use `google_adk` loggers and lazy `%` formatting.
- Do not log raw prompts, tool payloads, credentials, artifacts, or live media unless content-capture policy explicitly allows it.

## Code Executor Pattern

Attach code executors at the agent layer, but troubleshoot them as runtime services because they execute side-effecting work.

Safety choices:

| Need | Executor/environment | Safety notes |
| --- | --- | --- |
| Model-compatible built-in execution | `BuiltInCodeExecutor` | May be configured automatically for supported code execution flows. |
| Quick trusted local Python snippets | `UnsafeLocalCodeExecutor(timeout_seconds=...)` | High trust only; code runs locally in a spawned process and can import/use local resources. |
| Custom isolated local container | `ContainerCodeExecutor(image=...)` | Requires Docker and extension dependencies; container image should be hardened. |
| Cloud execution | Vertex/GKE/Agent Engine executors | Requires optional extras, credentials, projects, APIs, quotas, and network. |
| Shell/file environment | `LocalEnvironment` | Experimental; initialize before use and close after use. Treat shell commands as host-affecting. |

Checklist:

- Set explicit timeouts for untrusted or model-generated code paths.
- Reject `UnsafeLocalCodeExecutor` for multi-tenant or untrusted-user workloads.
- For container execution, verify Docker access and image provenance before runtime.
- For cloud execution, verify credentials and API enablement with safe read-only checks before running model-generated code.
- If a code executor appears unavailable in a base install, check optional extras instead of rewriting application logic.

## Switching From In-Memory To SQL Database Sessions

This pattern supports the hard case where a user hits missing `sqlalchemy` while migrating from in-memory sessions.

1. Confirm the target service: `SqliteSessionService` for a direct SQLite file without SQLAlchemy, or `DatabaseSessionService` for SQLAlchemy-backed URLs/engines.
2. Run the diagnostic: `python sub-skills/runtime-services/scripts/check_runtime_services.py --json`.
3. If DB support is missing, install the DB extra in the user's environment: `pip install "google-adk[db]"`; also install backend async drivers when needed.
4. Create the service with a non-production test URL first, then call `await service.prepare_tables()` for `DatabaseSessionService` to pay setup cost at startup.
5. Back up any existing persistent session store before migration; do not migrate while an app is writing events.
6. Create/fetch sessions with matching `app_name`, `user_id`, and `session_id`; stale session objects can fail append checks after concurrent writes.

## Plugin Plus Event Persistence Pattern

This pattern supports the hard case where a user adds a plugin to observe model/tool callbacks without losing persistence.

1. Put the plugin on `App(plugins=[AuditPlugin()])` and pass the `App` into `Runner`.
2. Implement observation callbacks with `return None` unless the goal is to short-circuit a model/tool/agent response.
3. Use `on_event_callback` for persisted-event observation; it is invoked before the runner appends the event.
4. Do not manually append the observed event from the plugin.
5. Let the caller consume the `run_async` stream to completion.
6. Call `await runner.close()` on shutdown so plugin cleanup runs.

## Runtime Ownership Summary

- `App` owns root agent/node configuration and app-wide plugins/config.
- `Runner` owns invocation context, plugin manager, session/memory/artifact/credential service wiring, event persistence, and lifecycle cleanup.
- `SessionService` owns durable or in-memory event/state storage.
- `MemoryService` owns searchable recall and must be fed selected sessions/events.
- `ArtifactService` owns versioned non-text payloads and artifact metadata.
- `PluginManager` owns plugin ordering, short-circuit behavior, and plugin close timeouts.
- `Telemetry` owns traces/logs/metrics export surfaces, but runtime code should avoid implicit global span assumptions.
- `CodeExecutor` and `Environment` own side-effecting code/shell execution and require explicit safety review.
