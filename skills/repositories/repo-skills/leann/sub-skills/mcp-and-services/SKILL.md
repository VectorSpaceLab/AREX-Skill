---
name: mcp-and-services
description: "Configure and troubleshoot LEANN's local MCP stdio server, Claude
  and OpenClaw clients, and read-only HTTP search service."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LEANN MCP and Services

Use this sub-skill when the task is about `leann_mcp`, MCP JSON-RPC tools,
Claude Code/Desktop, OpenClaw integration, or `leann serve`.

## Route the task

1. For MCP lifecycle, exact tool schemas, result/error envelopes, and direct
   protocol probes, read [MCP protocol and tools](references/mcp-protocol-and-tools.md).
2. For Claude or OpenClaw registration, project working directories, and the
   separate `leann-memory` identity, read
   [client and OpenClaw setup](references/client-and-openclaw-setup.md).
3. For HTTP endpoints, request/response models, host/port controls, and exposure
   boundaries, read [HTTP service](references/http-service.md).
4. For startup, protocol, index, manifest, path, or network failures, use the
   decision table in [troubleshooting](references/troubleshooting.md).
5. To generate a parseable MCP client configuration or a reviewed HTTP command
   **without launching anything**, run
   `python scripts/generate_service_config.py --help` from this directory, or
   invoke that script by its path from any working directory.

## Operating rules

- Treat MCP as line-delimited JSON-RPC over stdio. Reserve stdout for one JSON
  response per line; send diagnostics to stderr.
- Run the MCP child and HTTP service from the project root that owns
  `.leann/indexes/`. Index names are project-relative on the build, status, and
  HTTP paths even though `leann_list` can discover registered projects.
- Keep the default HTTP bind at `127.0.0.1`. The service has no built-in
  authentication or TLS; require an explicit deployment control before any
  non-loopback bind.
- Assume tools can read indexed local files and return passage text, metadata,
  and paths. Minimize filesystem permissions and never expose private indexes
  to an untrusted client or network.
- Do not place secrets in generated MCP JSON. Embedding or language-model
  credentials belong to the `embeddings-and-chat` sub-skill.

## Boundaries

- Slack/Twitter content acquisition and reader behavior: `rag-applications`.
- Search quality, filters, and index lifecycle semantics: `api-and-indexing`.
- General CLI build/watch/daemon operations: `cli-operations`.
- Embedding/LLM provider setup and credentials: `embeddings-and-chat`.
