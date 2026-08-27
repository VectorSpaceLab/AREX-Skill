---
name: sdk-http-integration
description: "Use RAGFlow public HTTP APIs, the Python SDK, OpenAI-compatible
  chat completions, API keys, streaming, references, and client error handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SDK and HTTP Integration

Use this sub-skill when a task needs to call RAGFlow through its public REST API, Python SDK, OpenAI-compatible chat completions, retrieval endpoint, API keys, or client-side troubleshooting.

## Start here

- For endpoint families, SDK objects, request shapes, and migration notes, read `references/api-sdk-reference.md`.
- For authentication, status codes, RAGFlow response codes, and safe error handling, read `references/auth-and-errors.md`.
- For common failures such as wrong `base_url`, API key errors, stream parsing, ID confusion, DELETE bodies, and server availability, read `references/troubleshooting.md`.
- To prepare or optionally run a harmless health check request, use `scripts/ragflow_api_smoke.py --help`.

## Public integration boundaries

- Prefer the Python package `ragflow-sdk` for Python clients and `RAGFlow(api_key, base_url, version="v1")` for SDK entrypoints.
- Use HTTP paths under `/api/v1` for public REST calls; do not depend on backend module internals or frontend hooks.
- For OpenAI-compatible chat calls, configure OpenAI clients with `base_url="<server>/api/v1/openai/<chat_id>/chat"` and call `client.chat.completions.create(...)`.
- Treat dataset, document, chunk, chat, agent, session, and memory IDs as distinct resource identifiers; do not substitute one ID type for another.
- Use the public examples in these references as distilled patterns; do not require future agents to open repository examples or tests.

## Typical workflows

- Dataset/document/chunk flow: create or list a dataset, upload or create documents, parse documents, list or update chunks, then retrieve chunks through `/api/v1/retrieval` or `RAGFlow.retrieve(...)`.
- Chat flow: create or list a chat assistant, create or list sessions, ask through `Session.ask(...)` or `/api/v1/chat/completions`, and preserve `reference` metadata when citations matter.
- Agent flow: list or get agents, create sessions when needed, call `/api/v1/agents/chat/completions`, and request traces only when debugging component behavior.
- Memory flow: create/list/update/delete memories and add/search/retrieve messages through the SDK methods summarized in `references/api-sdk-reference.md`.

## Safety defaults

- Never print real API keys in generated curl commands or logs.
- Do not run destructive deletes unless the user explicitly provides target IDs or asks for `delete_all` semantics.
- Prefer non-stream requests while debugging request shape; add streaming only after auth, URL, and payload validation pass.
- Run `scripts/ragflow_api_smoke.py` without `--execute` first; it only prints a redacted prepared request by default.
