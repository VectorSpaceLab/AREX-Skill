# Pause, Resume, Signals, and Human Approvals

mcp-agent exposes signal APIs that work locally and with Temporal. Temporal adds durability: a workflow can wait for a signal across worker restarts, deploys, or long human review windows.

## Core Model

- A workflow pauses by awaiting `app.context.executor.wait_for_signal(...)` or `self.executor.wait_for_signal(...)` from inside workflow execution.
- An external actor resumes it by emitting the same signal name with the target `workflow_id` and `run_id`.
- The MCP app server exposes resume/cancel/status tools over its workflow registry when workflows are served as MCP tools.
- Temporal signals require both `workflow_id` and `run_id`; local asyncio can often resolve from in-memory registry state, but durable control should keep both ids.

## Pause/Resume Workflow Skeleton

```python
from mcp_agent.app import MCPApp
from mcp_agent.executor.errors import WorkflowApplicationError
from mcp_agent.executor.workflow import Workflow, WorkflowResult

app = MCPApp(name="approval_app")

@app.workflow
class ApprovalWorkflow(Workflow[dict]):
    @app.workflow_run
    async def run(self, request: dict) -> WorkflowResult[dict]:
        draft = await self.prepare_draft(request)

        try:
            approval = await app.context.executor.wait_for_signal(
                signal_name="resume",
                workflow_id=self.id,
                run_id=self.run_id,
                signal_description="Waiting for human approval.",
                timeout_seconds=3600,
                signal_type=dict,
            )
        except TimeoutError as exc:
            raise WorkflowApplicationError(
                "Timed out waiting for resume signal.",
                type="SignalTimeout",
                non_retryable=True,
            ) from exc

        if not approval or approval.get("decision") != "approved":
            return WorkflowResult(
                value={"status": "rejected", "draft": draft, "approval": approval},
            )

        final = await self.finalize_draft(draft, approval)
        return WorkflowResult(value={"status": "approved", "result": final})

    @app.workflow_task(retry_policy={"maximum_attempts": 2})
    async def prepare_draft(self, request: dict) -> str:
        return f"Draft for {request.get('topic', 'untitled')}"

    @app.workflow_task(retry_policy={"maximum_attempts": 1})
    async def finalize_draft(self, draft: str, approval: dict) -> str:
        reviewer = approval.get("reviewer", "unknown")
        return f"{draft}\nApproved by: {reviewer}"
```

Design notes:

- Use a non-retryable workflow/application error for signal timeouts when retrying would only repeat the wait and confuse operators.
- Return a normal workflow result for explicit rejection when rejection is a business outcome, not an infrastructure failure.
- Use structured payloads for approvals so later versions can add fields without changing the signal name.
- Keep signal names stable; changing them can orphan running workflows that are waiting for the old name.

## External Resume Skeleton

```python
async with app.run() as running_app:
    await running_app.executor.signal(
        signal_name="resume",
        payload={"decision": "approved", "reviewer": "ops", "notes": "Proceed."},
        workflow_id="approval-workflow-123",
        run_id="temporal-run-id",
    )
```

When using an MCP app server, the workflow registry resume path accepts the same idea:

```python
await running_app.context.workflow_registry.resume_workflow(
    workflow_id="approval-workflow-123",
    run_id="temporal-run-id",
    signal_name="resume",
    payload={"decision": "approved"},
)
```

If the app is exposed as an MCP server, the server's `workflows-resume` tool sends a signal through the registry. Cloud workflow CLI commands are outside this sub-skill; route those tasks to `../cli-cloud-operations/SKILL.md`.

## Signals That Also Work Locally

Use the executor abstraction rather than importing Temporal signal helpers directly:

```python
payload = await app.context.executor.wait_for_signal(
    signal_name="resume",
    workflow_id=self.id,
    run_id=self.run_id,
    timeout_seconds=300,
    signal_type=dict,
)
```

For local asyncio prototyping, an in-memory signal bus handles the same call shape. For Temporal, the workflow initializes a `TemporalSignalHandler` and attaches a mailbox to the running workflow. The Temporal signal handler validates that `workflow_id` and `run_id` are present.

## `@app.workflow_signal` Handlers

Use `@app.workflow_signal` when inbound signals should update workflow state instead of directly unblocking a generic wait:

```python
@app.workflow
class ReviewWorkflow(Workflow[str]):
    @app.workflow_signal(name="editor_feedback")
    async def editor_feedback(self, notes: str) -> None:
        self.state.feedback = notes or ""

    @app.workflow_run
    async def run(self, topic: str) -> WorkflowResult[str]:
        await self.create_outline(topic)
        feedback = getattr(self.state, "feedback", "Awaiting review.")
        return WorkflowResult(value=feedback)
```

Use `wait_for_signal` when the workflow should block until a signal arrives. Use `@app.workflow_signal` when the workflow can continue polling or coordinating while state is asynchronously updated.

## Human Input Pattern

For human-in-the-loop workflows:

1. Generate or gather the candidate output inside workflow tasks.
2. Emit progress/logging that includes workflow id and run id so a UI or operator can identify the run.
3. Await a `resume`, `approve`, `reject`, or domain-specific signal with a timeout aligned to business expectations.
4. Treat rejection as a normal result if it is expected; treat timeout or malformed approval as non-retryable when retrying cannot fix it.
5. Keep the approval payload serializable and version-tolerant.

Example payload schema:

```json
{
  "decision": "approved",
  "reviewer": "ops",
  "notes": "Allowed for this customer.",
  "version": 1
}
```

## Query and Control

Temporal workflow handles can be used for direct Temporal control when the caller owns a handle:

```python
handle = await running_app.executor.start_workflow("ApprovalWorkflow", {"topic": "policy"})
run_id = handle.result_run_id or handle.run_id
workflow_id = handle.id
```

Keep these identifiers in user-facing or operator-facing state. Without them, later resume/cancel/status requests may be ambiguous or impossible after process restart.

The workflow registry supports:

- `resume_workflow(run_id=..., workflow_id=..., signal_name=..., payload=...)`
- `cancel_workflow(run_id=..., workflow_id=...)`
- `get_workflow_status(run_id=..., workflow_id=...)`
- `list_workflow_statuses(...)` with Temporal visibility queries where available.

## Designing a Local-to-Temporal Pause/Resume Flow

For a workflow that must run on both asyncio and Temporal:

- Write workflow code against `app.context.executor.wait_for_signal` and `executor.signal` rather than Temporal SDK functions.
- Use deterministic workflow ids in tests and demos.
- Store both `workflow_id` and `run_id` when a run is started.
- Keep signal payloads plain JSON-compatible objects.
- Avoid Temporal-only APIs in the workflow body unless guarded and isolated.
- Use `WorkflowApplicationError` from `mcp_agent.executor.errors` for non-retryable failures that should also work when Temporal is not installed.

## Common Signal Failure Modes

- Waiting with one signal name and resuming with another.
- Losing the `run_id` and trying to signal only a workflow id when multiple runs exist.
- Running caller code with `execution_engine: asyncio` while the worker and workflow are on Temporal, causing control calls to hit the wrong backend.
- Timing out a workflow and then sending a resume signal to a completed/failed run.
- Sending payload types that cannot be serialized by the Temporal data converter.
- Using very short timeouts for human approval flows that require minutes or hours.
