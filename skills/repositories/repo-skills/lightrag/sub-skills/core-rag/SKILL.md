---
name: core-rag
description: "Use LightRAG as an embedded Python library: construct LightRAG,
  initialize/finalize storages, insert text or custom KGs, query with
  QueryParam, configure embeddings/cache/rerank knobs, and avoid async lifecycle
  misuse."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Core LightRAG Embedded Usage

Use this sub-skill when writing or reviewing Python code that imports `lightrag` directly and drives `LightRAG` from an application, notebook, script, or test harness.

## Route By Task

- Start with [API reference](references/api-reference.md) for constructor defaults, `QueryParam`, embedding wrappers, object relationships, and lifecycle method signatures.
- Use [workflows](references/workflows.md) for minimal async recipes, insert/query patterns, custom IDs/file paths, custom KG ingestion, cache/rerank toggles, and addon params.
- Use [troubleshooting](references/troubleshooting.md) for install/import failures, missing initialization, sync-wrapper misuse in async apps, embedding switches, cache/rerank warnings, and ID/file-path validation issues.
- Run [scripts/check_core_api.py](scripts/check_core_api.py) when you need a safe local import/signature sanity check that does not call models, services, credentials, or persistent storages.

## Boundaries

- This sub-skill owns embedded Python usage of `LightRAG`, `QueryParam`, `EmbeddingFunc`, `wrap_embedding_func_with_attrs`, `ainsert`, `aquery`, `ainsert_custom_kg`, initialization/finalization, cache/rerank knobs, custom IDs, file paths, and `addon_params`.
- For document parser engines, filename/process options, multimodal parsing, and advanced chunker strategy selection, route to `../document-pipeline/SKILL.md`.
- For storage backend class choices, service configuration, migrations, workspace isolation details, and destructive storage tools, route to `../storage-backends/SKILL.md`.
- For provider modules, credentials, role-specific LLM settings, reranker provider bindings, and VLM provider behavior, route to `../llm-providers/SKILL.md`.
- For `lightrag-server`, REST routes, WebUI, auth, deployment, and environment-file orchestration, route to `../api-server/SKILL.md`.

## Non-Negotiables

- Always call `await rag.initialize_storages()` after constructing `LightRAG` and before `ainsert`, `aquery`, `ainsert_custom_kg`, delete, cache, or graph operations.
- Always call `await rag.finalize_storages()` during cleanup, preferably in `finally` after successful construction.
- In async applications, call coroutine APIs such as `await rag.ainsert(...)` and `await rag.aquery(...)`; do not call sync wrappers from a running event loop.
- Keep the embedding function and vector data consistent; changing embedding model or dimension requires rebuilding/clearing vector storage data.
- Do not bake secrets, service URLs, or machine-specific file locations into reusable embedded examples.
