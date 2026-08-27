# Durable Execution Troubleshooting

Use this when a Temporal-backed mcp-agent workflow does not start, does not resume, retries incorrectly, or behaves differently from local asyncio.

## Quick Diagnosis Table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `No module named temporalio` or `mcp_agent.executor.temporal` import failure | Temporal is optional | Install `mcp-agent[temporal]`; do not import Temporal modules in base-only environments. |
| Worker raises `App executor is not a TemporalExecutor` | Config did not select Temporal | Set `execution_engine: temporal` in the config used by the worker. |
| Client starts a run but nothing executes | No worker polling the matching task queue | Start a worker with `create_temporal_worker_for_app(app)` and matching `temporal.task_queue`. |
| Connection refused or timeout to Temporal | Server/service is unavailable or host is wrong | Start a local dev server or configure the remote `temporal.host`, TLS, API key, namespace, and metadata. |
| Workflow starts but custom activity is missing | Module defining the task was not imported before worker startup | Add the module to `workflow_task_modules`, or import it in the worker/app entrypoint. |
| Activity retries forever on bad credentials | Provider errors are retryable by default | Add `non_retryable_error_types` and cap `maximum_attempts` for provider tasks. |
| Signal resume returns false or no effect | Wrong signal name, workflow id, run id, namespace, or completed run | Use the ids from workflow start/list/status and match the exact signal name. |
| Replay or nondeterminism errors | Workflow body performs I/O, random, wall-clock, or external state reads | Move side effects into `@app.workflow_task` activities and use executor helpers for IDs/randomness. |
| Token metrics differ from local asyncio | Provider/MCP calls execute as activities | Compare aggregate usage, not exact local token tree shape. |

## Optional Dependency Boundary

Temporal support is provided by the optional `temporal` extra, which installs `temporalio[opentelemetry]`. Base installs may still run local asyncio workflows, but Temporal imports and workers fail until the extra is installed.

Safe checks:

```bash
python scripts/check_temporal_config.py mcp_agent.config.yaml
python scripts/check_temporal_config.py mcp_agent.config.yaml --check-imports
```

`--check-imports` imports mcp-agent Temporal modules and reports missing optional dependencies. It does not connect to a Temporal server.

## Service Readiness

For local development, a common setup is:

```bash
temporal server start-dev
```

The app config should then point at the dev server:

```yaml
execution_engine: temporal

temporal:
  host: "localhost:7233"
  namespace: "default"
  task_queue: "mcp-agent"
```

For remote or production clusters:

- Set `tls: true` when the cluster requires TLS.
- Set `api_key` or `rpc_metadata` through environment or secrets placeholders, not literal secrets.
- Confirm the namespace exists before starting workers.
- Keep caller and worker config aligned on host, namespace, and task queue.

## Namespace and Task Queue Mismatch

Temporal queues are namespaced. A workflow started in namespace `A` on task queue `x` will not be picked up by a worker polling namespace `B` or task queue `y`.

Check all three places:

1. The config used by the process that calls `executor.start_workflow`.
2. The config used by the worker process.
3. Any explicit `task_queue` passed to `start_workflow` or `__mcp_agent_task_queue` passed to `Workflow.run_async`.

Prefer constants or shared config for task queue names in production. Use `id_reuse_policy: reject_duplicate` when duplicate workflow ids would be dangerous.

## Workflow Module Import Missing

`create_temporal_worker_for_app(app)` only knows about workflows and activities registered on that app. Failures commonly happen when:

- The worker imports `app` but not the module that declares workflow classes.
- Custom tasks use the static `workflow_task` decorator but the module is not listed in `workflow_task_modules`.
- The caller and worker run different code versions.
- Activity names were overridden with `name=...` but retry policies or calls use the default fully qualified name.

Repair pattern:

```yaml
workflow_task_modules:
  - my_project.workflows
  - my_project.temporal_tasks
```

Also make the worker import an app module that imports or defines all `@app.workflow` classes before entering `create_temporal_worker_for_app(app)`.

## Retry Policy Problems

mcp-agent supports retry policies from two places:

- Inline: `@app.workflow_task(retry_policy={...})`
- Config: top-level `workflow_task_retry_policies`

Config matching precedence is exact full activity name, dotted suffix/plain function name, prefix wildcard, then `*` fallback. If a policy does not apply, inspect the activity name from `func.execution_metadata["activity_name"]` or Temporal history.

Provider failures that should usually be non-retryable include:

- OpenAI or Azure OpenAI: `AuthenticationError`, `PermissionDeniedError`, `BadRequestError`, `NotFoundError`, `UnprocessableEntityError`.
- Anthropic: `AuthenticationError`, `PermissionDeniedError`, `BadRequestError`, `NotFoundError`, `UnprocessableEntityError`.
- Azure AI Inference: `HttpResponseError` for 400, 401, 403, 404, and 422 responses.
- Google GenAI: `InvalidArgument`, `FailedPrecondition`, `PermissionDenied`, `NotFound`, `Unauthenticated`.

Use narrow error names. A global `NotFoundError` can be too broad if some tasks intentionally retry after a missing resource appears.

## Non-Deterministic Workflow Code

Temporal replays workflow code. Keep workflow bodies as orchestration only.

Do not put these directly in `@app.workflow_run` code:

- Direct provider SDK calls.
- Direct MCP client calls.
- Filesystem or database I/O.
- HTTP requests.
- Unseeded random values.
- `datetime.now()` or wall-clock branching.
- Global mutable counters that affect branching.

Put them in `@app.workflow_task` activities, or use mcp-agent abstractions that the Temporal executor already schedules as activities. For IDs/randomness, prefer executor helpers because the Temporal executor can supply deterministic versions in workflow context.

## Signals and Timeouts

If pause/resume fails:

1. Confirm the workflow is still open and waiting.
2. Confirm the exact signal name used by `wait_for_signal` or `@app.workflow_signal`.
3. Confirm both `workflow_id` and `run_id` target the intended run.
4. Confirm caller and worker use the same namespace.
5. Confirm the signal payload is serializable.
6. Review timeout handling; a workflow that already raised `SignalTimeout` cannot be resumed.

Use `WorkflowApplicationError(..., non_retryable=True)` for timeout failures that should not be retried. Return a normal `WorkflowResult` for expected human rejection.

## Temporal vs Local Context Differences

The same decorators are intended to work under asyncio and Temporal, but operational behavior changes:

- Activities may run in worker context instead of the caller process.
- Logs may appear in worker logs and Temporal history rather than the initiating process.
- Token counters may be attached to workflow/activity nodes differently.
- In-memory global state is not durable and may not be shared between caller and worker.
- Secrets and config must be available to the worker process, not just the launcher.

If code works locally but fails under Temporal, first check what must be available in the worker: imports, config, secrets, MCP server commands, provider packages, network access, and task queue.

## Safe Escalation Path

1. Run the static config validator.
2. Check optional Temporal imports.
3. Start a local Temporal dev server only if the user wants a service-backed run.
4. Start the worker and verify it polls the expected task queue.
5. Start one tiny workflow with no provider calls.
6. Add one activity, then one provider/MCP call, then signals.
7. Only after the skeleton works, port the full workflow pattern.
