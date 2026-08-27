# LightRAG Cross-Cutting Troubleshooting

Use this reference for failures that span multiple LightRAG workflows. For deeper guidance, route to the nearest owning sub-skill.

## Quick Triage

| Symptom | Likely area | First check | Route |
| --- | --- | --- | --- |
| `ModuleNotFoundError: lightrag` | Install/import | Install `lightrag-hku`; verify with `python scripts/check_lightrag_install.py` | `../SKILL.md` |
| Missing `yaml`, `fastapi`, parser/upload packages | Optional extras | Install `lightrag-hku[api]` for server/upload/parser support | `../sub-skills/api-server/SKILL.md` |
| `AttributeError: __aenter__`, missing `history_messages`, storage object errors | Lifecycle | Ensure `await rag.initialize_storages()` happened before use | `../sub-skills/core-rag/SKILL.md` |
| Runtime-loop or sync-wrapper error | Async misuse | In async apps, call `await rag.ainsert(...)` and `await rag.aquery(...)` | `../sub-skills/core-rag/SKILL.md` |
| Vector dimension mismatch or degraded retrieval after model change | Embedding/storage contract | Rebuild or clear vector stores after changing embedding model/dimension | `../sub-skills/storage-backends/SKILL.md` |
| Parser hint or `process_options` rejected | Ingestion parser | Validate engine names, option letters, and single chunk selector | `../sub-skills/document-pipeline/SKILL.md` |
| Upload/scan/delete returns busy/conflict | Pipeline concurrency | Distinguish normal processing from scan classification/destructive windows | `../sub-skills/document-pipeline/SKILL.md` |
| Provider `401`, timeout, or connection refused | LLM/provider binding | Check provider credentials and service URL without making unrelated storage changes | `../sub-skills/llm-providers/SKILL.md` |
| API warns about default guest JWT secret | Server auth | Set `TOKEN_SECRET` when `AUTH_ACCOUNTS` is configured | `../sub-skills/api-server/SKILL.md` |

## Install and Optional Extras

LightRAG's base package supports embedded Python usage with default local JSON/NetworkX/NanoVectorDB storage. API uploads, document parsing dependencies, FastAPI, and WebUI server entry points require the `api` extra. External databases and provider SDKs are split into optional extras so future agents should install only the extra needed for the task.

Use public install forms such as:

```bash
pip install lightrag-hku
pip install "lightrag-hku[api]"
pip install "lightrag-hku[offline-storage]"
pip install "lightrag-hku[offline-llm]"
```

Do not advise installing all extras unless the task genuinely needs the full offline stack.

## Initialization and Data Lifecycle

The most common embedded-code error is constructing `LightRAG` and immediately calling insert/query without initializing storages. The safe lifecycle is:

1. Construct `LightRAG` with LLM, embedding, storage, workspace, and optional rerank settings.
2. Call `await rag.initialize_storages()`.
3. Run insert/query/delete/cache operations.
4. Call `await rag.finalize_storages()` in cleanup.

For server tasks, the server owns this lifecycle; do not manually initialize a second `LightRAG` instance against the same workspace unless the task is explicitly about embedded code.

## Embeddings, Rerank, and Caches

Embedding model changes are storage changes, not just provider changes. If the embedding dimension, prefix/asymmetric behavior, or provider task mode changes, old vectors no longer represent the same space. Route rebuild/clear decisions to storage-backends and provider semantics to llm-providers.

LLM response cache identity tracks model/binding information, but provider options can still change behavior. When investigating stale answers, verify cache settings before blaming retrieval.

## Parser and Pipeline Conflicts

`process_options` uses short option letters for parser outputs and chunking. Use at most one chunking selector among `F`, `R`, `V`, and `P`. External parser engines such as MinerU or Docling need configured services; native parsing may still need package extras for Office/PDF formats.

Normal enqueue can overlap processing, but scan classification and destructive clear/delete windows intentionally reject conflicting requests. Do not work around these conflicts by writing directly to storage while the pipeline is busy.

## API Server and WebUI

Use `lightrag-server` or `lightrag-gunicorn` for packaged server startup. Use `lightrag-hash-password` for bcrypt hashes when enabling account auth. Treat guest mode as development-only unless another access-control layer is intentionally protecting the server.

The WebUI is a React/Bun/Vite application when developing from source, but deployed package users normally interact with server-packaged assets. Build/test details belong to the API server sub-skill.
