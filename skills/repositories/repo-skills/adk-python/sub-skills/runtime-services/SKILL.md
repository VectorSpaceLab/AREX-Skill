---
name: runtime-services
description: "Configure and troubleshoot ADK runtime services: Runner, App,
  sessions, memory, artifacts, plugins, telemetry, code executors, environments,
  event persistence, and service lifecycles."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Runtime Services

Use this sub-skill when a task is about ADK execution services rather than agent design: `Runner`, `InMemoryRunner`, `App`, session persistence, memory, artifacts, plugins, telemetry, code executors, execution environments, event storage, lifecycle cleanup, or service migration cautions.

## Route Here

- Create or debug a `Runner`/`InMemoryRunner`, including `run`, `run_async`, `run_live`, `run_debug`, `close`, and `auto_create_session` behavior.
- Choose between `InMemorySessionService`, `SqliteSessionService`, `DatabaseSessionService`, or cloud-backed session/memory/artifact services.
- Explain why events, state, memory, artifacts, or live audio blobs were or were not persisted.
- Add an app-level `BasePlugin` that observes model/tool/user/event callbacks while preserving runner-owned event persistence.
- Configure OpenTelemetry/logging, `TelemetryConfig`, or `google_adk` logger behavior.
- Attach a code executor or execution environment and assess local/container/cloud safety trade-offs.
- Diagnose optional dependency failures such as missing SQLAlchemy for DB sessions or missing extension/cloud packages.

## Route Elsewhere

- Agent, tool, callback, schema, model, or sub-agent construction belongs in [agent-construction](../agent-construction/SKILL.md).
- `Workflow` graph/node/edge/resume design belongs in [workflow-orchestration](../workflow-orchestration/SKILL.md).
- CLI servers, app discovery, YAML config, and deployment commands belong in [cli-configuration-deployment](../cli-configuration-deployment/SKILL.md).
- Evaluation metrics, eval sets, and `adk test`/`adk eval` assertion design belongs in [evaluation-debugging](../evaluation-debugging/SKILL.md).

## Working Path

1. Identify which service owns the symptom: runner lifecycle, session event persistence, memory ingestion/search, artifact storage, plugin callback order, telemetry export, or code execution.
2. Confirm installation assumptions: `google-adk` 2.3.0, import root `google.adk`, Python 3.10+, and optional extras absent unless installed explicitly.
3. Use in-memory services for focused local tests; switch to persistent services only after checking dependencies, URLs/paths, concurrency, migrations, and credential requirements.
4. Keep event persistence runner-owned: stream events through `Runner.run_async`/`run_live` and let the configured session service append non-partial events.
5. Close long-lived services with `await runner.close()` or `async with Runner(...)` when plugins, toolsets, or database engines need cleanup.

## References And Scripts

- [API Reference](references/api-reference.md): constructor signatures, core methods, imports, service contracts, optional extras, and lifecycle notes.
- [Service Patterns](references/service-patterns.md): safe recipes for runner setup, persistence choices, plugins, telemetry, memory/artifacts, and code execution.
- [Troubleshooting](references/troubleshooting.md): symptom-driven fixes for DB extras, event persistence, plugin callback order, blocking tools, code executors, credentials, and migrations.
- [Runtime Services Diagnostic](scripts/check_runtime_services.py): safe local script that prints base runtime imports/signatures and reports optional DB-extra availability without touching databases or credentials.

## Safety Defaults

- Prefer `InMemoryRunner` or explicit `Runner(..., session_service=InMemorySessionService())` for examples and unit tests.
- Treat `InMemorySessionService`, `InMemoryMemoryService`, and `InMemoryArtifactService` as development/test services, not multi-process production stores.
- Do not run destructive migrations or open user databases as a first diagnostic; inspect optional imports and backup plans before migration.
- Treat `UnsafeLocalCodeExecutor` and `LocalEnvironment` as high-trust local-only surfaces because model-generated code or shell commands can affect the host.
- Do not assume base install includes DB, extension, MCP, GCP, or cloud service dependencies.
