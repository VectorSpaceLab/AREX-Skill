---
name: durable-execution
description: "Convert mcp-agent workflows into durable Temporal-backed workers
  with pause/resume, signals, retries, activity registration, and operational
  guardrails."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# durable-execution

Use this sub-skill when an mcp-agent app must run workflows durably with the Temporal executor: production workers, long-running tools, pause/resume, human approval signals, activity/task retries, task registration, workflow handles, and Temporal service constraints.

## Route First

- Use `../workflow-patterns/SKILL.md` first when the task is choosing between router, orchestrator, parallel, evaluator, swarm, or other workflow shapes.
- Use `../core-sdk/SKILL.md` first when the task is basic `MCPApp`, `Agent`, provider, secrets, or local asyncio setup.
- Use `../cli-cloud-operations/SKILL.md` when the user specifically asks for hosted cloud deployment or cloud workflow CLI commands.
- Stay here when the workflow shape already exists and the work is making it durable, observable, retry-safe, signalable, or worker-backed.

## Durable Conversion Checklist

1. Confirm the Temporal extra is available before importing Temporal-specific modules: install with `mcp-agent[temporal]`, which brings in `temporalio[opentelemetry]`.
2. Set `execution_engine: temporal` and configure `temporal.host`, `temporal.namespace`, and `temporal.task_queue`; in current settings, `host` includes the port such as `localhost:7233`.
3. Keep the same `@app.workflow`, `@app.workflow_run`, `@app.workflow_task`, `@app.async_tool`, and `Agent` APIs where possible. The decorators adapt to asyncio or Temporal based on configuration.
4. Create a worker process that imports the app and any modules that register workflows/tasks, then runs `create_temporal_worker_for_app(app)`.
5. Put custom reusable activities in importable modules and list them under `workflow_task_modules` when they are registered with the static `workflow_task` decorator or otherwise need preloading.
6. Configure task retry behavior with local `@app.workflow_task(retry_policy=...)` metadata or top-level `workflow_task_retry_policies` for exact, suffix, prefix wildcard, and `*` matching.
7. Design pause/resume with `executor.wait_for_signal(...)` inside the workflow and `executor.signal(...)`, workflow registry resume, or MCP server resume tools outside it.
8. Keep workflow code deterministic. Move external API calls, file I/O, MCP tool calls, database writes, and provider calls into workflow tasks/activities or existing mcp-agent abstractions.
9. Validate static config with `scripts/check_temporal_config.py`; generate a safe starter worker/app skeleton with `scripts/worker_skeleton.py`.

## Reference Map

- Temporal worker and activity design: `references/temporal-workflows.md`
- Pause/resume, signals, and human approvals: `references/pause-resume-and-signals.md`
- Operational troubleshooting: `references/troubleshooting.md`
- Static config validator: `scripts/check_temporal_config.py`
- Worker/app skeleton generator: `scripts/worker_skeleton.py`

## Safety Notes

- A Temporal worker is a long-running service process. The bundled scripts do not start a Temporal worker, connect to a cluster, or call providers unless the user edits and runs the generated application code.
- Temporal is optional. Base mcp-agent installs may import core SDK APIs but fail on `mcp_agent.executor.temporal` until the Temporal extra is installed.
- Temporal server examples are skip-service unless the user already has a local or remote Temporal cluster and explicitly wants to run them.
- Do not put secrets in config examples. Use environment placeholders, secrets files, or a deployment secret manager.
