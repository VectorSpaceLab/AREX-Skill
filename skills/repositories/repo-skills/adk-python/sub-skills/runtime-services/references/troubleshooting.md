# Runtime Services Troubleshooting

Start with the symptom, identify the service owner, then run safe import/signature checks before changing persistence, credentials, or executor settings.

## Safe First Checks

```bash
python sub-skills/runtime-services/scripts/check_runtime_services.py
python sub-skills/runtime-services/scripts/check_runtime_services.py --json
```

The script checks base imports, prints selected signatures, and reports optional DB-extra availability. It does not open databases, start servers, read credentials, call cloud APIs, or run code executors.

## Missing `sqlalchemy` Or DB Extra

Symptoms:

- Importing `DatabaseSessionService` raises a missing-extra error for `sqlalchemy` or `google-adk[db]`.
- Constructing `DatabaseSessionService(db_url=...)` fails before connecting.
- A user switches from in-memory sessions to SQL DB sessions and base install lacks DB dependencies.

Fix path:

1. Confirm the user actually needs SQLAlchemy-backed `DatabaseSessionService`; for a simple local SQLite file, `SqliteSessionService(db_path)` may be enough.
2. Run the bundled diagnostic and inspect the `DatabaseSessionService` optional result.
3. Install the DB extra in the active application environment: `pip install "google-adk[db]"`.
4. Add async database drivers required by the URL, such as async SQLite/PostgreSQL/MySQL drivers, when the DB extra does not include the selected backend driver.
5. Create the service with exactly one of `db_url` or `db_engine`.
6. Run non-production setup first; for `DatabaseSessionService`, `await service.prepare_tables()` is safe to call more than once and helps surface schema setup errors at startup.

Do not:

- Treat missing SQLAlchemy as a bug in agent construction.
- Run migrations against production data without a backup and a write stop.
- Open a user database just to diagnose whether the optional extra exists.

## SQLite Schema Or Migration Warning

Symptoms:

- `SqliteSessionService(db_path)` raises a message that an old schema is detected.
- Existing SQLite event tables lack the current event-data column layout.
- Migration guidance mentions creating a new destination DB and then renaming after backup.

Fix path:

1. Stop writers to the database.
2. Back up the original DB file.
3. Run migration tooling only on a copy or with a separate destination path.
4. Validate row counts and spot-check sessions/events in the migrated copy.
5. Swap the migrated DB into service only after validation.

Do not run a migration script in the runtime process while `Runner` is appending events.

## Events Are Yielded But Not Persisted

Likely causes:

- The event is `partial=True`; session services skip partial events.
- Live mode yielded inline raw audio/video/image data that is intentionally not saved to session events.
- The caller stopped iterating `run_async` before the agent finished; the runner cancels the root task when the generator is closed early.
- The event was manually created or appended outside `Runner`, skipping runner-owned lifecycle logic.
- A plugin returned a replacement event with missing or unexpected fields.
- `app_name`, `user_id`, or `session_id` does not match the stored session.

Fix path:

1. Log or inspect `event.id`, `event.partial`, `event.author`, `event.invocation_id`, and `event.actions` as events stream.
2. Confirm the run uses `Runner.run_async` or `Runner.run_live`, not a direct agent call, when persistence matters.
3. Consume the async generator to completion.
4. Retrieve the session after the run with matching identifiers and `GetSessionConfig` that does not filter the event out.
5. If a plugin modifies events, temporarily return `None` from `on_event_callback` to isolate plugin replacement behavior.
6. For live media, use artifact settings and inspect artifact service storage for saved file references rather than expecting raw inline blobs in session history.

## Session Not Found Or App Name Mismatch

Symptoms:

- `Session not found: ...` even though a session was created.
- Warning mentions runner app name and agent origin mismatch.
- Sessions appear under a different app key in the backing service.

Fix path:

1. Use one app name consistently in `App(name=...)`, `Runner(app_name=...)`, `create_session`, `get_session`, and CLI/app loading.
2. Prefer passing `App` to `Runner` so `Runner.app_name` follows `App.name` unless intentionally overridden.
3. Create a session before the run or use `auto_create_session=True` deliberately.
4. Check that `GetSessionConfig(num_recent_events=0)` is not hiding all events during debugging.

## Stale Session During Persistent Append

Symptoms:

- Append fails with a stale-session message or update-time mismatch.
- Concurrent tasks append to the same persistent session.
- A session object was fetched before another process wrote new events.

Fix path:

1. Re-fetch the session immediately before appending or running the next invocation.
2. Serialize writes per `(app_name, user_id, session_id)` where possible.
3. Prefer runner-managed appends rather than manual `append_event` calls.
4. For SQLAlchemy-backed DB sessions, understand that in-process locks help only within the same process; multi-process writers still need DB-level concurrency discipline.

## Plugin Lifecycle Or Callback Order Confusion

Facts:

- Plugins run in registration order.
- Plugins run before corresponding agent callbacks.
- A non-`None` callback return short-circuits later plugins and agent callbacks for that callback point.
- `on_event_callback` runs before the runner persists/yields the output event.
- `after_run_callback` runs after execution and does not emit an event.
- `PluginManager.close()` runs plugin `close()` methods sequentially with a timeout.

Symptoms:

- Later plugins never run.
- Agent callbacks never run.
- Tool/model calls are skipped and a plugin-provided response appears instead.
- Events lose metadata after a plugin modifies them.

Fix path:

1. For observation-only plugins, return `None` from every callback.
2. Add explicit logging around callback entry/exit with plugin name and callback name.
3. If returning a replacement `Event`, keep author, invocation ID, branch/isolation scope, actions, and content/function-call identifiers unless intentionally changing them.
4. Register policy plugins before passive logging plugins only when early exits are desired.
5. Use unique plugin names to avoid `PluginManager.register_plugin` errors.
6. Ensure `await runner.close()` runs so plugin `close()` cleanup occurs.

## Plugin Observes Events But Persistence Breaks

Most likely cause: the plugin manually appends, replaces, or drops events instead of observing.

Correct pattern:

- Implement `on_event_callback(...): return None` for pure observation.
- Do not call `session_service.append_event` inside the plugin.
- Let the runner persist the event after callback processing.
- If redaction is required, return a modified event and verify that streamed and stored events still align.

Validation:

1. Run once with the plugin disabled.
2. Run once with the plugin enabled but returning `None`.
3. Run once with the intended modification.
4. Compare retrieved session events after each run.

## Blocking Sync Tools Or Callbacks Stall Runtime

Symptoms:

- `run_async` stops yielding for long periods.
- Multiple sessions block each other.
- Plugin/tool callbacks do network or filesystem work synchronously.

Fix path:

1. Move blocking I/O to async libraries or `asyncio.to_thread` where safe.
2. Add explicit timeouts for network calls, tool calls, plugin callbacks, and code execution.
3. Keep plugin callbacks short; they run in the invocation path.
4. Avoid CPU-heavy work inside event-loop callbacks; offload to worker processes/threads.
5. Prefer async `Runner.run_async` in production instead of the sync `Runner.run` convenience wrapper.

## Unsafe Local Code Executor Use

Symptoms:

- User wants model-generated Python to execute on the host.
- `UnsafeLocalCodeExecutor` is attached in a multi-user or untrusted setting.
- Code execution times out or can access local resources.

Facts:

- `UnsafeLocalCodeExecutor` is explicitly unsafe and local-only.
- It runs code in a spawned process but does not sandbox filesystem/network access.
- It forbids `stateful=True` and `optimize_data_file=True`.

Fix path:

1. Reject unsafe local execution for untrusted users or multi-tenant workloads.
2. Set `timeout_seconds` even for trusted local debugging.
3. Prefer a hardened container/cloud executor when code must be isolated.
4. Validate optional extension dependencies for `ContainerCodeExecutor`, `VertexAiCodeExecutor`, `GkeCodeExecutor`, or `AgentEngineSandboxCodeExecutor`.
5. Review output files and artifact handling before exposing generated files to users.

## Container Or Cloud Code Executor Fails

Symptoms:

- `ContainerCodeExecutor` import asks for `google-adk[extensions]`.
- Docker client, image build, or container startup fails.
- Vertex/GKE/Agent Engine executor fails due to credentials, APIs, project, location, or quota.

Fix path:

1. Confirm optional extension/cloud extras are installed in the active environment.
2. For containers, verify Docker is running, the image exists or `docker_path` is valid, and `python3` is installed in the image.
3. For cloud execution, verify credentials with read-only cloud tooling, confirm project/location, enable required APIs, and check IAM/quota.
4. Keep executor initialization separate from request handling so startup failures are visible early.

## Environment Lifecycle Errors

Symptoms:

- `LocalEnvironment.working_dir` raises because it is not initialized.
- Temporary workspace is left behind.
- Shell commands run in the wrong directory.

Fix path:

1. Call `await env.initialize()` before `execute`, `read_file`, or `write_file`.
2. Use an explicit `working_dir` when output location matters.
3. Call `await env.close()` in `finally` blocks.
4. Treat shell command strings as high trust; never pass unsanitized user input directly.

## Telemetry Or Logs Missing

Symptoms:

- No traces arrive at the collector.
- Logs are uncorrelated with invocations.
- Metrics/log exporters never start.

Fix path:

1. Set OTel environment variables before the process starts, or configure OTel hooks before creating/running the app.
2. Check collector endpoint, network, TLS/proxy settings, and exporter dependencies.
3. Use `google_adk` logger names and `%`-style lazy logging.
4. Avoid relying on implicit current spans in concurrent tasks; use explicit context/span propagation when extending runtime internals.
5. Confirm content capture policy before logging prompts, tool payloads, or artifacts.

## Memory Search Returns Nothing

Likely causes:

- Session events were never ingested into memory.
- In-memory memory search only keyword-matches event text.
- The query uses a different `app_name` or `user_id`.
- Events have no text parts.
- A cloud memory service lacks credentials, index setup, or eventual consistency time.

Fix path:

1. Retrieve the session and confirm it contains the expected non-partial events.
2. Call `add_session_to_memory(session)` or supported delta/direct memory APIs.
3. Search with the same app/user identifiers.
4. For in-memory service, test a simple keyword present in event text.
5. For cloud memory, verify configuration and wait/retry according to service behavior.

## Artifact Not Found Or Wrong Version

Likely causes:

- Filename is session-scoped but `session_id` was omitted.
- A user-scoped artifact filename lacks the `user:` prefix.
- Requested version index is out of range.
- Artifact service is in-memory and process state was lost.
- Artifact was saved as a reference and the referenced artifact is unavailable.

Fix path:

1. Call `list_artifact_keys(app_name=..., user_id=..., session_id=...)`.
2. Call `list_versions(...)` or `list_artifact_versions(...)` for the filename.
3. Use `version=None` to load the latest version.
4. Confirm scope: `user:` filenames are user-scoped; other filenames require `session_id`.
5. For persistent/cloud artifact stores, validate credentials, bucket/path, IAM, and retention.

## Cloud Credentials Or Service Prerequisites

Symptoms:

- Vertex/GCS/cloud session or memory service import succeeds but runtime calls fail.
- Errors mention default credentials, project, location, APIs, IAM, quota, or network.

Fix path:

1. Identify the exact cloud-backed service being used.
2. Confirm optional extras and transitive dependencies are installed.
3. Verify application default credentials or service account configuration with safe read-only checks.
4. Confirm project, region/location, enabled APIs, IAM roles, and quota.
5. Keep fallback in-memory or local service paths for tests that should not require credentials.

## Credential Or Session Migration Cautions

When moving between session services or credential stores:

- Treat session data as user data; back it up and preserve access controls.
- Stop writes during migration.
- Migrate into a fresh destination and validate before swapping.
- Check whether event schemas, timestamps, app/user/session keys, and state scopes remain compatible.
- Do not copy credentials into session state, artifacts, logs, or generated skill content.

## When To Escalate To Other Sub-skills

- If the root problem is agent constructor fields, tool binding, model selection, or callback placement, route to [agent-construction](../../agent-construction/SKILL.md).
- If the root problem is graph edges, dynamic nodes, HITL resume, or workflow state routing, route to [workflow-orchestration](../../workflow-orchestration/SKILL.md).
- If the root problem is `adk web`, `adk api_server`, deployment, YAML config, or app discovery, route to [cli-configuration-deployment](../../cli-configuration-deployment/SKILL.md).
- If the root problem is eval JSON, eval sets, test assertions, or trace summarization for failures, route to [evaluation-debugging](../../evaluation-debugging/SKILL.md).
