---
name: agents-craft-and-tools
description: "Router for Onyx chat/LLM, Craft build mode, MCP, skills,
  sandboxes, and agentic workflow troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# agents-craft-and-tools

Use this sub-skill for Onyx backend work that touches chat and agent behavior, Craft build mode, sandboxes, skills, MCP, or agentic workflow troubleshooting.

Read the bundled references when:

- [chat-and-llm-flow.md](references/chat-and-llm-flow.md) — read this before changing chat context assembly, prompt precedence, streaming packets, deep research, or LLM tracing.
- [craft-sandbox-and-skills.md](references/craft-sandbox-and-skills.md) — read this before changing Craft sessions, sandbox provisioning, skill push/sync, user libraries, or sandbox image setup.
- [mcp-tools-and-actions.md](references/mcp-tools-and-actions.md) — read this before changing the MCP server, MCP client/OAuth flows, tool visibility, or external app integrations.
- [troubleshooting.md](references/troubleshooting.md) — read this when diagnosing stuck chat turns, missing providers, bad tool calls, MCP auth failures, sandbox provisioning failures, or stale skills.
- [scripts/README.md](scripts/README.md) — read this if you need the reason no live-cluster helper scripts are bundled here.

Route tasks elsewhere when they are mainly:

- repository-wide FastAPI, DB, or migration mechanics: use backend-platform
- UI rendering, component state, or frontend behavior: use web-frontend or mobile-client
- indexing/connectors work: use rag-indexing-connectors

Primary surface areas:

- chat and deep research: `backend/onyx/chat/**`, `backend/onyx/deep_research/**`
- tooling and action plumbing: `backend/onyx/tools/**`, `backend/onyx/server/features/tool/**`
- MCP: `backend/onyx/mcp_server/**`, `backend/onyx/server/features/mcp/**`
- Craft build mode: `backend/onyx/server/features/build/**`, `docs/craft/**`, `backend/onyx/server/features/persona/**`, `backend/onyx/server/features/skill/**`, `backend/onyx/server/features/projects/**`
- tracing and LLM instrumentation: `backend/onyx/tracing/**`

Open only the smallest bundled reference that covers the task, then keep the rest of the work inside this subtree.