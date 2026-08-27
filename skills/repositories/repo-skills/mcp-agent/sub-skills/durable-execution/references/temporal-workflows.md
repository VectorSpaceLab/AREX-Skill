# Temporal Workflows and Workers

This reference distills the mcp-agent Temporal execution path into reusable patterns. It is self-contained; do not depend on repository examples being present at runtime.

## What Changes When `execution_engine` Is Temporal

- `MCPApp` selects a `TemporalExecutor` instead of the asyncio executor.
- `@app.workflow` classes become Temporal workflow definitions.
- `@app.workflow_run` marks the workflow entry point and mcp-agent handles runtime initialization.
- `@app.workflow_task` functions become Temporal activities when executed from inside a Temporal workflow.
- Built-in agent/MCP operations are registered as activities by `create_temporal_worker_for_app(app)`.
- `executor.start_workflow(...)` returns a Temporal workflow handle unless `wait_for_result=True` is used.

The same app code should usually work in local asyncio and Temporal modes. The service boundary is configuration plus a separate worker process.

## Minimal Config

Use this as the starting point for local development with an already-running Temporal server:

```yaml
execution_engine: temporal

temporal:
  host: "localhost:7233"
  namespace: "default"
  task_queue: "mcp-agent"
  max_concurrent_activities: 10
```

Useful optional keys:

```yaml
workflow_task_modules:
  - my_project.temporal_tasks

workflow_task_retry_policies:
  my_project.temporal_tasks.lookup_customer:
    maximum_attempts: 1
  my_project.provider_tasks.*:
    maximum_attempts: 2
    initial_interval: 1.5
    backoff_coefficient: 2.0
    maximum_interval: 30
    non_retryable_error_types:
      - AuthenticationError
      - PermissionDeniedError
      - BadRequestError
      - NotFoundError
      - UnprocessableEntityError
  "*":
    maximum_attempts: 3

temporal:
  host: "${TEMPORAL_HOST}"
  namespace: "production"
  task_queue: "research-agents"
  api_key: "${TEMPORAL_API_KEY}"
  tls: true
  timeout_seconds: 300
  id_reuse_policy: "reject_duplicate"
  rpc_metadata:
    team: "agents"
```

Config facts to preserve:

- `execution_engine` accepts `asyncio` or `temporal`.
- `TemporalSettings.host` is the target host string and commonly includes the port, such as `localhost:7233`.
- `namespace` defaults to `default` but should be explicit in production.
- `task_queue` must match between callers and workers.
- `id_reuse_policy` accepts `allow_duplicate`, `allow_duplicate_failed_only`, `reject_duplicate`, or `terminate_if_running`.
- Top-level `workflow_task_modules` and `temporal.workflow_task_modules` are both imported before the worker begins polling.

## Worker Entrypoint

Create one worker process for each app/task queue pair:

```python
import asyncio
import logging

from my_app import app  # imports workflow classes and decorated tasks
from mcp_agent.executor.temporal import create_temporal_worker_for_app

logging.basicConfig(level=logging.INFO)

async def main() -> None:
    async with create_temporal_worker_for_app(app) as worker:
        await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
```

`create_temporal_worker_for_app(app)` does all of the following:

- Enters `app.run()` and verifies the executor is a `TemporalExecutor`.
- Connects a Temporal client using configured host, namespace, TLS/API key, data converter, interceptors, and RPC metadata.
- Preloads built-in provider workflow task modules and configured custom modules.
- Registers built-in agent tasks such as MCP tool calls, prompts, capabilities, and server lifecycle tasks.
- Registers system activities for log forwarding, human input requests, and relay operations.
- Collects app-registered activities and workflows into a Temporal `Worker` on the configured task queue.

## Workflow Definition

```python
from mcp_agent.app import MCPApp
from mcp_agent.executor.workflow import Workflow, WorkflowResult

app = MCPApp(name="durable_research")

@app.workflow
class DurableSummary(Workflow[str]):
    @app.workflow_run
    async def run(self, topic: str) -> WorkflowResult[str]:
        outline = await self.plan_outline(topic)
        result = await self.write_summary(outline)
        return WorkflowResult(value=result)

    @app.workflow_task(retry_policy={"maximum_attempts": 3})
    async def plan_outline(self, topic: str) -> list[str]:
        return ["Background", "Current state", f"Recommendation for {topic}"]

    @app.workflow_task(schedule_to_close_timeout=None)
    async def write_summary(self, outline: list[str]) -> str:
        return "\n".join(f"- {item}" for item in outline)
```

Prefer `@app.workflow_task` for any operation that may touch a provider, MCP server, HTTP API, database, filesystem, or other side-effect boundary. mcp-agent enforces async workflow tasks; wrap blocking work with `asyncio.to_thread` inside the async task if needed.

## Launching Workflows

```python
async with app.run() as running_app:
    handle = await running_app.executor.start_workflow(
        "DurableSummary",
        "MCP adoption",
        workflow_id="durable-summary-mcp-adoption",
        task_queue="mcp-agent",
    )
    result = await handle.result()
```

`start_workflow` validates the workflow `run` signature and maps positional/keyword arguments into Temporal input. Use `execute_workflow(...)` or `wait_for_result=True` when you want to wait immediately. Use explicit `workflow_id` when later control, resume, cancellation, or duplicate prevention matters.

The `Workflow.run_async(...)` convenience path accepts special keyword arguments that are not passed to the workflow body:

- `__mcp_agent_workflow_id` for a custom workflow id.
- `__mcp_agent_task_queue` for a non-default task queue.
- `__mcp_agent_workflow_memo` for Temporal memo values.

## Custom Workflow Tasks

For tasks inside the same app module, `@app.workflow_task(...)` is enough. For tasks in separate modules, use an importable module and preload it:

```python
# my_project/temporal_tasks.py
from mcp_agent.executor.workflow_task import workflow_task

@workflow_task(name="my_project.lookup_customer")
async def lookup_customer(customer_id: str) -> dict:
    return {"id": customer_id, "tier": "enterprise"}
```

```yaml
workflow_task_modules:
  - my_project.temporal_tasks
```

Then call it from workflow code through the executor:

```python
from my_project.temporal_tasks import lookup_customer

customer = await app.context.executor.execute(lookup_customer, customer_id)
```

`executor.execute`, `execute_many`, and `execute_streaming` must be called from inside a Temporal workflow. They schedule registered workflow tasks as Temporal activities. If a callable is not marked as a workflow task, mcp-agent falls back to executor behavior that is suitable for ordinary async work but does not provide the same activity registration semantics.

## Retry Policy Design

`@app.workflow_task` accepts a `retry_policy` dict that maps to Temporal retry fields:

```python
@app.workflow_task(
    name="provider.request_completion",
    retry_policy={
        "maximum_attempts": 2,
        "initial_interval": 1,
        "backoff_coefficient": 2.0,
        "maximum_interval": 30,
        "non_retryable_error_types": [
            "AuthenticationError",
            "PermissionDeniedError",
            "BadRequestError",
            "NotFoundError",
            "UnprocessableEntityError",
        ],
    },
)
async def request_completion(prompt: str) -> str:
    ...
```

Top-level `workflow_task_retry_policies` override or augment decorator retry policy. Matching precedence is:

1. Exact full activity name.
2. Dotted suffix such as `tasks.lookup_customer` or plain function name.
3. Prefix wildcard such as `my_project.provider_tasks.*`, with the longest prefix winning.
4. Global `*` fallback.

Use narrow non-retryable exception names. Overly broad strings such as `NotFoundError` can suppress legitimate retries if different libraries use the same class name for recoverable failures.

## Determinism Rules

Temporal replays workflow code from event history. Keep orchestration deterministic:

- Do not call network APIs, MCP tools, provider SDKs, filesystems, random generators, or wall-clock time directly in workflow orchestration code.
- Use workflow tasks/activities for side effects and external data.
- Use executor-provided `uuid()` and `random()` helpers where a workflow needs deterministic IDs or random choices.
- Avoid mutating module-level global state from workflow code.
- Do not branch on data that is fetched outside a recorded activity.
- Keep workflow input/output payloads serializable through the configured pydantic Temporal data converter.

## Worker/Service Boundaries

- Starting a workflow requires a running Temporal server and at least one worker polling the matching task queue.
- A worker must import the modules that define all workflow classes and workflow tasks before polling.
- The app process that starts workflows and the worker process must agree on workflow class names, task queue, namespace, and serialization-compatible code.
- `max_concurrent_activities` throttles activity concurrency inside mcp-agent's executor wrapper and is useful for provider or MCP-server rate limits.
- OpenTelemetry integration is available through Temporal's opentelemetry extra; enable mcp-agent tracing separately when needed.

## Token Metrics Under Temporal

mcp-agent pushes workflow token context during workflow execution and may attach workflow/run ids to token nodes. Under Temporal, provider calls often happen as activities, so token trees may be split across workflow/activity context and replay-aware execution. When comparing local asyncio and Temporal runs, expect differences in ordering or context boundaries even when the user-facing result matches.
