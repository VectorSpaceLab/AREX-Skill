---
name: chat-agents
description: "Build, use, and troubleshoot Khoj chat, conversation sessions,
  agents, commands, model providers, streaming, and chat tools."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Khoj Chat and Agents

Use this sub-skill when working on Khoj chat behavior, `/api/chat`, `/api/agents`, conversation sessions, chat commands, streaming events, agent configuration, model-provider routing, voice/image/code/research/operator features, or conversation sharing/history/file filters.

## Start Here

- Use `references/chat-api.md` for REST and WebSocket chat endpoints, `ChatRequestBody`, stream events, sessions, history, sharing, titles, message deletion, and conversation file filters.
- Use `references/agent-configuration.md` for `/api/agents`, `ModifyAgentBody`, `ModifyHiddenAgentBody`, privacy levels, tool/output options, hidden agents, file knowledge bases, and chat model selection.
- Use `references/tools-and-commands.md` for slash commands, automatic tool selection, command prerequisites, output modes, and tool failure behavior.
- Use `references/troubleshooting.md` for missing chat model/API key, unsafe prompts, rate limits, local provider mismatches, unavailable web/code/image/voice/operator services, and share-domain errors.
- Use `scripts/inspect_chat_schema.py` to print chat/agent Pydantic schemas, agent enum choices, conversation commands, and stream event names without starting the Khoj server.

## Boundaries

- This sub-skill owns chat request/response behavior, conversation and sharing APIs, agents, tools, model-provider checks, voice response, image/diagram output, code/research/operator routing, and chat-specific troubleshooting.
- Route raw content ingestion, parsing, indexing, and `/api/content` behavior to `content-indexing`.
- Route semantic search internals, query filters, embeddings, reranking, and `/api/search` to `search-retrieval`; chat can use file/query filters, but the search implementation lives there.
- Route scheduled automations, reminders, and memory API behavior to `automations-memory`.
- Route server startup, auth, CORS/host configuration, admin setup, Docker, and broad deployment diagnostics to `deployment-api`.

## Safe Workflow

1. Identify whether the task is chat transport, command/tool selection, agent configuration, model-provider setup, conversation metadata, or feature troubleshooting.
2. Inspect the schema with the bundled helper when payload fields or option values are uncertain; do not import `khoj.main` or run `khoj --help` for schema-only checks.
3. For behavior changes, keep tool prerequisites explicit: chat model/API setup is required for all chat, and `/online`, `/code`, `/image`, `/diagram`, `/research`, `/operator`, and voice each have additional service requirements.
4. For agent changes, distinguish user-facing public/private/protected agents from per-conversation hidden agents, and distinguish agent input tools from chat-only slash commands.
5. For verification, prefer small authenticated API calls or focused unit tests around route/helper behavior; avoid starting browsers, sandboxes, external model calls, or long research/operator runs unless the user explicitly requests operational validation.

## Evidence Basis

This guidance is distilled from Khoj chat and agent routes, conversation helpers, tool processors, model-provider docs, operator notes, and focused tests covering online chat, agent updates, and conversation utilities. It is self-contained for future coding agents and does not require reading original repo docs or tests at runtime.
