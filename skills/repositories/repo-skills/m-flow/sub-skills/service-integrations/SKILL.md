---
name: service-integrations
description: "Operate M-flow as a FastAPI service, web UI, MCP server, Docker
  Compose stack, authenticated multi-tenant backend, cloud sync/distributed
  worker, or face-aware playground integration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# service-integrations

Use this sub-skill for M-flow service surfaces: API startup, Docker Compose, the web UI, MCP transport and API mode, auth and settings, cloud sync, distributed workers, and the face-aware playground.

## Route elsewhere

- In-process Python calls such as `m_flow.add()`, `memorize()`, `search()`, `query()`, `ingest()`, or `learn()` → `../core-memory-api/`
- Storage backend and retrieval tuning details → `../retrieval-graph-search/`
- Loaders, chunking, content routing, and pipeline internals → `../ingestion-pipelines/`

## Use this sub-skill when

- starting or checking `m_flow.api.client:app`
- launching `mflow -ui` or `m_flow.api.v1.ui.start_ui()`
- wiring `m_flow-frontend`, `m_flow-mcp`, Docker Compose, or the playground stack
- configuring auth, multi-tenancy, settings, or health checks
- using MCP stdio/SSE/HTTP, remote API mode, or task tracking
- enabling cloud sync or Modal workers
- connecting face-aware playground sessions to `fanjing-face-recognition`

## Bundled files

- [deployment-and-integrations.md](references/deployment-and-integrations.md)
- [api-server-reference.md](references/api-server-reference.md)
- [mcp-reference.md](references/mcp-reference.md)
- [troubleshooting.md](references/troubleshooting.md)
- [service_status_check.py](scripts/service_status_check.py)
- [mcp_tool_summary.py](scripts/mcp_tool_summary.py)

## Guardrails

- Prefer safe status checks over service mutation.
- Treat face-recognition playground setup as distilled guidance only; it downloads models and needs camera access, so do not run automated installers unless the user explicitly asks.
- Do not route core memory operations here; use the core-memory API sub-skill instead.
- Keep all runtime links inside this sub-skill tree or to sibling generated skill files.
