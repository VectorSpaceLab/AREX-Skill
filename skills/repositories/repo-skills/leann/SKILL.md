---
name: leann
description: "Use LEANN to build, search, update, chat over, serve, integrate,
  debug, and maintain compact local vector indexes and RAG applications across
  Python APIs, CLI workflows, backends, data sources, MCP, and HTTP."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LEANN

Use this skill when a task names LEANN, `LeannBuilder`, `LeannSearcher`,
`LeannChat`, `leann`/`leann_mcp`, a LEANN index artifact, a LEANN backend, or a
LEANN RAG application.

## Route by task

- **Python index lifecycle and retrieval**: use
  [API and indexing](sub-skills/api-and-indexing/SKILL.md) for builders,
  searchers, precomputed vectors, updates, metadata filters, hybrid BM25/vector
  search, grep, result handling, and cleanup.
- **CLI and local operations**: use
  [CLI operations](sub-skills/cli-operations/SKILL.md) for build/search/ask,
  rebuild, watch, ID migration, warmup, daemons, source indexers, list/remove,
  command planning, and project registry behavior.
- **Backend and artifact decisions**: use
  [backends and storage](sub-skills/backends-and-storage/SKILL.md) for HNSW,
  IVF, DiskANN, FlashLib, compact/recompute storage, update tradeoffs, tuning,
  native builds, and index integrity.
- **Embeddings, chat, and ReAct**: use
  [embeddings and chat](sub-skills/embeddings-and-chat/SKILL.md) for embedding
  modes, model/device/cache choices, LLM providers, `LeannChat`, prompts,
  ReAct, web tools, credentials, and daemon model mismatches.
- **RAG application composition**: use
  [RAG applications](sub-skills/rag-applications/SKILL.md) for documents, code,
  browser/email/chat exports, Slack/Twitter readers, semantic file search,
  images, visual PDFs, chunking, metadata, and private-data preflight.
- **MCP and HTTP services**: use
  [MCP and services](sub-skills/mcp-and-services/SKILL.md) for MCP JSON-RPC,
  Claude/OpenClaw configuration, tool schemas, service process behavior, and
  the read-only HTTP search API.
- **Repository development**: use
  [development and testing](sub-skills/development-and-testing/SKILL.md) when
  editing the LEANN monorepo, selecting focused tests, building native
  packages, checking versions, maintaining docs, or planning a guarded release.

## Fast start

1. Read [installation](references/installation.md) and choose package-user or
   checkout-development setup. Do not install every optional backend merely
   because the host has an accelerator.
2. Run the bundled non-networking probe:

   ```bash
   python scripts/check_leann_install.py --check-cli
   ```

   Add `--require-backend hnsw` or another selected backend when that backend is
   part of the task.
3. Choose the owning sub-skill above. Keep build-time and query-time embedding
   model, mode, dimensions, normalization, and task templates consistent.
4. Treat an index name as an artifact family, not one file. Back up the complete
   family before migration, risky rebuild work, or irreplaceable removal.
5. Start with tiny public fixtures. Model downloads, API calls, private data,
   live services, CUDA packages, and publication commands require separate
   preflight and authorization.

## Shared references

- [Installation](references/installation.md) covers distributions, Python and
  backend choices, source builds, and a minimal import check.
- [Cross-cutting troubleshooting](references/troubleshooting.md) routes install,
  import, model, index, daemon, credential, and service failures.
- [Repository provenance](references/repo-provenance.md) records the source
  revision, component versions, and evidence baseline. Read it before deciding
  whether this skill is stale or should be refreshed.

## Guardrails

- Do not assume optional backends or provider packages are installed because
  `import leann` succeeds; require the selected registry entry and a matching
  smoke check.
- Do not hand-edit pickle offset maps, backend ID maps, or native index files.
- Do not place API keys in commands, logs, generated MCP JSON, or committed
  index metadata.
- Do not expose private passage text, source paths, or unauthenticated HTTP
  service endpoints to an untrusted client or non-loopback network.
- Do not use release/upload helpers or destructive rebuild/removal commands as
  diagnostics.
