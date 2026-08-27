# Example Workflow Adaptation Notes

## How to pick an example

1. Decide whether the task is about a basic agent, memory, tools, search, multimodal content, MCP, or a full application.
2. Match that intent to the corresponding row in `example-index.md`.
3. Read the example README only after the example family is identified.
4. Copy the *idea* of the example into the new project; do not depend on the original checkout at runtime.

## Common adaptation patterns

### Quickstart to custom app

Use the quickstart examples when you need to:

- change the response schema
- switch providers
- add streaming or async streaming
- adjust system-role behavior for reasoning models

### Multimodal examples

Use the multimodal examples when the task is about:

- images + text analysis
- PDFs with structured extraction
- multimodal content nested inside a schema

### Memory examples

Use `persistent-memory` or `fastapi-memory` when the user needs:

- cross-session recall
- a custom backend
- a service that stores conversation state per user or session

### Search, RAG, and research examples

Use `web-search-agent`, `rag-chatbot`, or `deep-research` when the task needs:

- current web information
- retrieval-backed answers
- multi-step research and synthesis

### Orchestration and hooks

Use `orchestration-agent` or `hooks-example` when the task is about:

- tool routing
- union-based tool choice
- hooks for monitoring, retries, or error handling

### MCP examples

Use `mcp-agent` or `progressive-disclosure` when the task is about:

- multiple MCP transports
- client/server separation
- large tool catalogs that should be loaded lazily

### Video transcript examples

Use the YouTube examples when the task is about:

- transcript extraction
- summarization
- structured recipe extraction from a video

## What not to do

- Do not tell future agents to run the original example paths as a runtime dependency.
- Do not assume an example is safe offline just because it is short.
- Do not copy example-specific environment files or keys into generated runtime instructions.
