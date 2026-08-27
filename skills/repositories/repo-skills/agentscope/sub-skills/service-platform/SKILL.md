---
name: service-platform
description: "AgentScope FastAPI service, storage, hub, channel, MCP, and
  deployment workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# service-platform

Use this sub-skill for the AgentScope service layer: `create_app`, storage, message bus wiring, workspace managers, hub registration, channel integration, and deployment/bootstrap checks.

## Read first

- `references/platform-overview.md` for the `create_app` contract and a bootstrap sketch.
- `references/storage-and-bus.md` for storage, message-bus, workspace-manager, channel, hub, and MCP components.
- `references/troubleshooting.md` for service startup and backend failures.
- `scripts/service_smoke.py` for a safe local bootstrap check.

## Typical triggers

- Start or debug the AgentScope FastAPI service.
- Compare `InMemoryMessageBus` vs `RedisMessageBus`.
- Wire `RedisStorage` or `AsyncSQLAlchemyStorage` into `create_app`.
- Add workspace managers, skill hubs, MCP hubs, or channel backends.
- Diagnose index-worker, knowledge-base, or service startup problems.

## What belongs here

- `agentscope.app.create_app`
- `SubAgentTemplate`
- message bus, storage, workspace manager, knowledge-base manager
- MCP client, channel, and hub integration
- service bootstrap, deployment, and runtime checks

## What does not belong here

- agent/tool/permission basics → `agent-core`
- provider credentials and model classes → `provider-connectors`
- retrieval or memory workflows → `rag-memory`
- workspace backend internals → `workspace-sandboxes`

## Use pattern

1. Decide whether the problem is storage, message bus, workspace, or channel related.
2. Read the component reference that matches that layer.
3. Start with the local smoke script before changing a live deployment.
4. Add external backends only after the in-memory or local bootstrap works.
5. Escalate to `workspace-sandboxes` if the failure is really a sandbox backend issue.

## Cross-links

- If the issue is actually a provider, use `provider-connectors`.
- If the issue is a tool or agent loop problem, use `agent-core`.
- If the issue is retrieval or memory, use `rag-memory`.
