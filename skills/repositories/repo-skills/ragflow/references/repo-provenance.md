# Repo Provenance

## Source Snapshot

- Repository: RAGFlow
- Source state type: Git checkout
- Commit: `dd46ece3bc31ab5d8bc21d991d8b25c6767297ba`
- Branch: `main`
- Exact tag: none detected
- Remote URL: `https://github.com/infiniflow/ragflow.git`
- Working tree state during skill generation: dirty because this skill was created under `skills/`
- Package version from metadata: `ragflow` 0.26.1
- Python requirement from metadata: `>=3.13,<3.14`

## Evidence Paths

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `pyproject.toml`
- `uv.lock`
- `api/`
- `rag/`
- `deepdoc/`
- `agent/`
- `common/`
- `memory/`
- `mcp/`
- `sdk/python/`
- `web/`
- `docs/`
- `docker/`
- `helm/`
- `example/http/`
- `example/sdk/`
- `test/`
- `.agents/skills/go-naming/SKILL.md`

## Evidence Scope

Included evidence emphasized user-facing and maintainer-facing workflows: deployment, backend API services, public SDK/HTTP usage, dataset ingestion/retrieval, document parsing, agent workflows, MCP/memory, and frontend integration.

Excluded or de-prioritized evidence included generated/cache/build output, dependency directories, review artifacts, full benchmark/e2e runs, credential-bound integrations, and maintainer-only release automation unless needed for deployment or troubleshooting context.

## Inspection Notes

- Top-level source modules for `api`, `rag`, `agent`, `common`, and `memory` were import-checked through a private source-inspection environment.
- Key source symbols were verified by static source inspection, including backend response/validation helpers, agent `Graph`/`Canvas`, ingestion `Pipeline`, retrieval `Dealer`, and SDK `RAGFlow`.
- A plain editable install can fail because package metadata names a top-level `graphrag` package while the actual GraphRAG code is under `rag/graphrag`. This skill records that as troubleshooting evidence and avoids claiming a full installed-package verification.
- No public skill content depends on private environment paths or the original checkout remaining available.
