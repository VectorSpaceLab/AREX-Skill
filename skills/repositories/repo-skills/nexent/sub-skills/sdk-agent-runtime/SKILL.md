---
name: sdk-agent-runtime
description: "Operate Nexent SDK agent runtime, streaming execution, models,
  tools, MCP/A2A, sandbox, monitoring, scheduler, and skill-manager workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SDK Agent Runtime

Use this sub-skill for Nexent tasks centered on the Python SDK runtime: direct `CoreAgent`/`NexentAgent` execution, streaming `agent_run`, `ModelConfig`/`AgentConfig`/`AgentRunInfo`, local/builtin/MCP tools, external A2A agents, sandbox execution, layered verification, monitoring spans, scheduler primitives, and SDK skill-manager usage.

## Route here when

- Building or testing an SDK agent, model, tool, MCP host, A2A wrapper, sandbox policy, or streaming event consumer.
- Creating or diagnosing `AgentRunInfo` payloads, `MessageObserver` streams, `ProcessType` chunks, graceful stop behavior, planning flags, capacity snapshots, or context items.
- Adding or adapting SDK-local tools or validating that a tool is exposed through `ToolConfig` and `NexentAgent.create_tool`.
- Working with SDK observability, `AgentRunMetadata`, OpenInference/OTLP spans, context metrics, prompt-cache metrics, or retrieval/tool span classification.
- Using scheduler primitives or the SDK skill manager outside backend route/service/database edits.

## Route elsewhere

- FastAPI apps, services, database models, exceptions, route contracts, env-var source-of-truth, NL2Agent/NL2Skill service edits: [`../backend-services-api/SKILL.md`](../backend-services-api/SKILL.md).
- Document ingestion, file conversion, vector database, storage, knowledge-base retrieval internals, or memory deep workflows: [`../knowledge-data-memory/SKILL.md`](../knowledge-data-memory/SKILL.md).
- Next.js UI, TypeScript service clients, streaming chat components, stores, i18n, or frontend builds: [`../frontend-integration/SKILL.md`](../frontend-integration/SKILL.md).
- Docker/Kubernetes/offline deployment, SQL migration/init synchronization, image/build/uninstall operations: [`../deployment-operations/SKILL.md`](../deployment-operations/SKILL.md).

## Operating procedure

1. Start with [`references/api-reference.md`](references/api-reference.md) for verified signatures, field meanings, event types, and runtime ownership boundaries.
2. Use [`references/workflows.md`](references/workflows.md) for task recipes: streaming examples, MCP transport diagnosis, A2A setup, tools, sandbox, verification, monitoring, scheduler, and skill manager workflows.
3. Use [`references/troubleshooting.md`](references/troubleshooting.md) when imports, model aliases, MCP URLs, stop events, code-block parsing, optional dependencies, sandbox backends, telemetry, or scheduler rules fail.
4. For safe local inspection, run [`scripts/inspect_sdk_runtime.py`](scripts/inspect_sdk_runtime.py). It imports or statically inspects SDK runtime APIs, prints signatures, and never starts services, calls models, opens network connections, or runs agents.

## Non-negotiable runtime rules

- Do not make external model, MCP, A2A, search, database, object-storage, Docker, or Kubernetes calls in unit tests unless the test explicitly provides mocks or live credentials/services.
- For tests around streaming `agent_run`, inject or monkeypatch a fake async generator and construct `AgentRunInfo` without iterating the real runner.
- `AgentConfig.model_name` must match a `ModelConfig.cite_name`; `NexentAgent.create_model` raises if the alias is absent.
- Executable agent code uses `<code>...</code>` or legacy ```<RUN>...</RUN>``` blocks; ordinary ```python blocks are intentionally not execution input.
- SDK modules receive configuration through Python objects. Backend service code owns environment-variable reads and passes resolved config into SDK models such as `SandboxConfig`.
- Keep SDK runtime changes separate from backend API/service/database changes; when a task crosses that boundary, use this sub-skill for SDK object behavior and the backend sub-skill for request/service wiring.
