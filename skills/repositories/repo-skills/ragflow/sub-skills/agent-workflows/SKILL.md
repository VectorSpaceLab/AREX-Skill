---
name: agent-workflows
description: "Work with RAGFlow agent canvas DSL, components, tools, templates,
  memory, MCP retrieval, sandbox execution, sessions, traces, and workflow
  debugging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Agent Workflows

Use this sub-skill when a task involves RAGFlow agents, canvas/workflow DSL, agent templates, component wiring, tool/sub-agent orchestration, memory-aware agents, MCP retrieval, sandbox/code execution, webhooks, sessions, traces, or component-level debugging.

## Start Here

- For DSL shape, execution order, variable references, components, loops, sessions, and debug flows, read `references/canvas-components.md`.
- For agent tools, plugin-style tools, memory read/write, MCP retrieval, sandbox/code execution, and security defaults, read `references/tools-memory-mcp.md`.
- For common failures such as broken component references, cycles, async/streaming surprises, credentials, sandbox, webhooks, memory, MCP, and template import/export, read `references/troubleshooting.md`.
- To statically inspect an exported template or DSL JSON without starting RAGFlow, run `python scripts/inspect_agent_template.py --help`.

## Scope Boundaries

- Treat the canvas DSL as the backend contract: `components`, `path`, `globals`, `history`, `retrieval`, `memory`, optional `variables`, and optional visual `graph` metadata.
- Use component IDs exactly as they appear in the DSL; variable references are usually `{component_id@output}`, `{{component_id@output}}`, `sys.*`, or `env.*`.
- Keep frontend canvas UI concerns out of this sub-skill; only use visual `graph` fields to preserve layout or diagnose component IDs.
- For public HTTP/SDK request details, cross-link to `sdk-http-integration`; this sub-skill only summarizes behavior-level agent, session, memory, and MCP surfaces.
- For retrieval ranking, parsing, chunking, and dataset internals, cross-link to `dataset-ingestion-retrieval`; this sub-skill focuses on retrieval as an agent tool.

## Common Workflows

- **Inspect a template:** validate JSON shape, ensure `dsl.components` exists, confirm `begin` or `File` start nodes, list component IDs/classes, and check references before import.
- **Debug a canvas run:** map `path` to component IDs, verify every downstream/upstream target exists, check `{component@output}` references against declared outputs, then inspect trace events when available.
- **Wire tools into an Agent:** put tool definitions under the Agent component parameters, keep tool names/descriptions actionable, provide credentials explicitly, and keep downstream `Message` handling in mind for streaming output.
- **Add memory:** create/configure memory separately, use Retrieval to read memory IDs, and use Message save-to-memory behavior for durable conversation facts.
- **Expose retrieval through MCP:** configure MCP server base URL and API key per environment, use `ragflow_retrieval`, and keep API key transport separate from dataset/document selection.

## Guardrails

- Do not publish real API keys, MCP headers, webhook secrets, database passwords, or sandbox host details in examples or logs.
- Do not assume all component imports are available in a source-only environment; optional dependencies can affect deeper imports.
- Do not run code execution, network tools, webhooks, deletes, or live MCP calls unless the user explicitly asks and provides safe targets.
- Prefer static template checks before live import/export; use the bundled inspector to catch missing keys and obvious graph/reference issues.
- Keep generated runtime guidance self-contained; source files, docs, and tests are evidence only.
