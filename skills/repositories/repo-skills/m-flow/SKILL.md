---
name: m-flow
description: "Operate M-flow memory, graph-routed retrieval, ingestion
  pipelines, service integrations, MCP, and storage backends for the mflow-ai
  package."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# M-flow

Use this repo skill when a task involves M-flow / `mflow-ai`: persistent memory
for agents, graph-routed RAG, episodic/procedural memory, the `m_flow` Python
package, the `mflow` CLI, the FastAPI service, web UI, MCP server, or storage
backend configuration.

## Fast orientation

M-flow stores knowledge as layered memory, then retrieves by graph-routed
Bundle Search. The common in-process workflow is:

1. `await m_flow.add(...)` or `await m_flow.ingest(...)` to register data.
2. `await m_flow.memorize(...)` to build Episode / Facet / FacetPoint / Entity
   graph memory.
3. `await m_flow.query(...)` or `await m_flow.search(...)` to retrieve context
   or an LLM-written answer.

Install the public package with `pip install mflow-ai`, or install a checkout
with `pip install -e .`. Python 3.10-3.13 is supported by project metadata; use
Python 3.11 when choosing a conservative inspection/development runtime.

Minimal checks:

```bash
python -c "import m_flow; print(m_flow.__version__)"
mflow --help
python scripts/check_mflow_env.py
```

## Route by task

| If the user asks about... | Read |
| --- | --- |
| Python APIs, CLI commands, add/memorize/query/ingest, datasets, manual graph insertion, delete/update/prune, config facade | [sub-skills/core-memory-api/SKILL.md](sub-skills/core-memory-api/SKILL.md) |
| Input formats, loader selection, `preferred_loaders`, chunking, `content_type`, content routing, procedural learning, custom pipelines | [sub-skills/ingestion-pipelines/SKILL.md](sub-skills/ingestion-pipelines/SKILL.md) |
| Recall modes, `SearchConfig`, episodic Bundle Search, graph/vector/relational/cache backend tuning, empty/noisy results, Cypher | [sub-skills/retrieval-graph-search/SKILL.md](sub-skills/retrieval-graph-search/SKILL.md) |
| FastAPI, web UI, Docker Compose, auth, settings, MCP, cloud sync, workers, face-aware playground, service status | [sub-skills/service-integrations/SKILL.md](sub-skills/service-integrations/SKILL.md) |
| Cross-cutting environment variables, optional extras, credential/service prerequisites | [references/configuration.md](references/configuration.md) |
| Install/import, credentials, DB locks, optional dependency, logging, or safe-operation recovery | [references/troubleshooting.md](references/troubleshooting.md) |
| Staleness and source snapshot checks | [references/repo-provenance.md](references/repo-provenance.md) |

## Operating guardrails

- M-flow API calls are mostly asynchronous; wrap examples in `asyncio.run()` or
  use an existing event loop.
- `TRIPLET_COMPLETION` and graph construction need LLM/embedding credentials;
  `EPISODIC`, `PROCEDURAL`, `CHUNKS_LEXICAL`, and `CYPHER` retrieve from data
  that must already be memorized.
- Defaults are local file-backed storage: SQLite relational metadata, LanceDB
  vectors, and Kuzu graph storage. External services need matching extras,
  environment variables, and service health checks.
- Do not run destructive operations (`delete`, `prune`, hard deletion, DB
  migrations, service stop/kill) without explicit user scope and confirmation.
- Treat optional browser scraping, face recognition, cloud sync, MCP remote API
  mode, Modal workers, and external DB providers as optional surfaces; verify
  credentials/services before claiming they work.
- Keep generated helper scripts safe by default. Use live workflow flags only
  when the user accepts local storage writes and credential use.
