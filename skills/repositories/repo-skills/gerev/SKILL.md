---
name: gerev
description: "Route Gerev tasks across connector setup, search/indexing, and
  source or Docker runtime workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Gerev

Gerev is a FastAPI-backed enterprise search service with pluggable data sources, a document indexing pipeline, and a React UI. Use this skill as the router for future Gerev tasks; do not stop at root guidance when a deeper sub-skill owns the workflow.

## Route map

- [`data-source-connectors`](sub-skills/data-source-connectors/SKILL.md) — connector discovery, validation, location selection, add/remove flows, and data-source setup docs.
- [`search-indexing`](sub-skills/search-indexing/SKILL.md) — query ranking, Faiss/BM25 indexing, parser helpers, model loading, queues, search/status routes, and startup-time search failures.
- [`deployment-runtime`](sub-skills/deployment-runtime/SKILL.md) — source startup, Docker/compose, UI build, storage layout, ports, and backend/UI boot troubleshooting.

## Install and first checks

- Backend runtime lives under `app/`. Install runtime dependencies with:

  ```bash
  cd app
  python -m pip install -r requirements.txt
  ```

- If the resolver pulls newer major versions that break imports, keep the compatibility family that matches the current code: `fastapi==0.95.2`, `starlette==0.27.0`, `pydantic<2`, `transformers<5`, and `sentence-transformers<4`.
- Frontend build lives under `ui/`. Use `cd ui && npm install && npm run build` when the UI bundle is needed for Docker or source serving.
- For a read-only connector inventory without importing the heavy app stack, run:

  ```bash
  python sub-skills/data-source-connectors/scripts/inspect_data_sources.py --app-dir app --json
  ```

  The bundled connector helper is [`inspect_data_sources.py`](sub-skills/data-source-connectors/scripts/inspect_data_sources.py).

## Current repo caveat

A full backend import or startup may fail with `ImportError: cannot import name 'split_PDF_into_paragraphs'` from `app/parsers/pdf.py` because `app/indexing/index_documents.py` imports a symbol that no longer exists. Treat that as a troubleshooting item, not an environment success. See `references/troubleshooting.md` and the search-indexing sub-skill before claiming a clean boot.

## When to read shared references

- Read [`repo-provenance.md`](references/repo-provenance.md) when checking whether this skill still matches the current checkout or before a refresh.
- Read [`troubleshooting.md`](references/troubleshooting.md) for cross-cutting install/import, model-cache, tokenizer, storage, and startup failures.
- Read [`frontend-api.md`](references/frontend-api.md) when you need the backend route contracts that the UI calls.
- Read [`deployment-runtime.md`](references/deployment-runtime.md) when you need the source-start, Docker, compose, or storage layout details.
- Read the nearest `sub-skills/<id>/references/` files for workflow-specific depth that the root router intentionally leaves out.

## Minimal read-only checks

- Connector discovery only: `python sub-skills/data-source-connectors/scripts/inspect_data_sources.py --app-dir app --strict`
- Search stack or model-cache check: use `sub-skills/search-indexing/scripts/inspect_search_indexing.py` when you need ranking/runtime details.
- Data-source catalog check: use [`inspect_data_sources.py`](sub-skills/data-source-connectors/scripts/inspect_data_sources.py) when you need connector schema or UI flows.
- Source-start/runtime layout check: use [`inspect_runtime_paths.py`](sub-skills/deployment-runtime/scripts/inspect_runtime_paths.py) when you need Docker/source boot details.

## Use this root skill when...

- The user says Gerev, enterprise search, add a connector, configure a data source, inspect search results, debug indexing, start the backend, or build the UI.
- The task spans more than one sub-skill and you need the router to point to the correct deeper reference instead of guessing from source folders.
