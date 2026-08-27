---
name: r2r
description: "Route R2R tasks to the correct Python, JavaScript, ingestion,
  retrieval, graph, and server workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# R2R

Use this skill when a user asks about the R2R server, the Python or JavaScript SDK, document ingestion, retrieval and RAG, graph workflows, deployment/configuration, or troubleshooting across those surfaces.

Start here:
1. Install the public package with `pip install r2r`.
2. If you need server and config extras, use `pip install 'r2r[core]'`.
3. Verify the public Python surface with `python scripts/check_r2r_environment.py`.
4. Route the task to the nearest sub-skill instead of packing every workflow into the root.

## Routing map

- `sub-skills/python-sdk/` — Python sync/async client setup, auth, method groups, downloads, pagination, streaming, and response wrappers.
- `sub-skills/ingestion-documents/` — document creation, chunking, metadata, filters, exports, and collection/document lifecycle.
- `sub-skills/retrieval-rag/` — search, RAG, streaming citations, agent/research mode, completion, and embedding.
- `sub-skills/graph-workflows/` — extraction, graph build/pull/reset, entities, relationships, communities, and graph lifecycle.
- `sub-skills/server-configuration/` — install, `r2r.serve`, config TOML/env, Docker, providers, and ops troubleshooting.
- `sub-skills/javascript-sdk/` — Node/browser client usage, auto-refresh, stream handling, and JS-specific payload shape.

## Useful bundled files

- `references/package-overview.md`
- `references/troubleshooting.md`
- `references/repo-provenance.md`
- `references/repo-routing-metadata.json`
- `scripts/check_r2r_environment.py`

## Safe first checks

- Prefer `python scripts/check_r2r_environment.py` over `r2r-serve --help` when you only need a safe verification path.
- `r2r-serve` starts server initialization and may need database and provider settings, so it is not a safe help-only probe.
- For any client workflow, decide early whether the request is Python SDK, JS SDK, document ingestion, retrieval/RAG, graph operations, or server configuration.
