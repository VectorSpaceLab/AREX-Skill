---
name: lightrag
description: "Use LightRAG as a graph-based RAG framework: embedded Python APIs,
  document ingestion, storage backends, LLM/provider wiring, FastAPI/WebUI
  operation, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LightRAG Repo Skill

Use this skill for tasks involving LightRAG, the `lightrag-hku` Python package, its graph-based RAG APIs, document parsing pipeline, storage backends, model/provider bindings, REST API server, or WebUI.

## Start Here

- Install the base package for embedded Python work: `pip install lightrag-hku`.
- Install API/upload/parser support for server work: `pip install "lightrag-hku[api]"`.
- Use the offline/storage/provider extras only when the task needs those optional backends: `offline-storage`, `offline-llm`, `offline`, `evaluation`, or `observability`.
- Verify the installed package without model calls or services: `python scripts/check_lightrag_install.py` from this skill directory.
- Read [repo provenance](references/repo-provenance.md) before deciding whether this skill is stale for a current checkout.
- Read [troubleshooting](references/troubleshooting.md) for cross-cutting install/import, initialization, optional dependency, credential, storage, parser, and server failures.

## Route By Task

- Embedded Python `LightRAG` construction, `QueryParam`, async lifecycle, text/custom-KG insertion, querying, embeddings, cache, and rerank knobs: use [core-rag](sub-skills/core-rag/SKILL.md).
- File/text ingestion internals, parser routing, filename hints, process options, chunk strategies, sidecars, doc status, and pipeline concurrency/refusal semantics: use [document-pipeline](sub-skills/document-pipeline/SKILL.md).
- KV/vector/graph/doc-status storage class selection, external storage services, workspace isolation, migrations, vector rebuilds, cache cleanup, and destructive storage preconditions: use [storage-backends](sub-skills/storage-backends/SKILL.md).
- LLM, embedding, VLM, role-specific model routing, provider bindings, asymmetric embeddings, rerank provider setup, credentials, service URLs, and model-cache behavior: use [llm-providers](sub-skills/llm-providers/SKILL.md).
- `lightrag-server`, `lightrag-gunicorn`, REST/Ollama-compatible routes, auth/JWT, `.env` configuration, setup wizard outputs, Docker/offline deployment, and React WebUI operations: use [api-server](sub-skills/api-server/SKILL.md).

## Core Decision Points

- Choose embedded Python when integrating LightRAG inside an application, notebook, worker, or test harness.
- Choose the API server/WebUI route when the user needs uploads, REST routes, browser UI, auth, or Ollama-compatible endpoints.
- Choose document-pipeline guidance when the problem names parser engines, `LIGHTRAG_PARSER`, `process_options`, chunking selectors `F/R/V/P`, parsed sidecars, scan/upload/delete conflicts, or doc-status rows.
- Choose storage-backends guidance when the problem names `JsonKVStorage`, `PGVectorStorage`, `Neo4JStorage`, Qdrant, Redis, MongoDB, OpenSearch, workspace isolation, vector dimensions, or rebuild/cache tools.
- Choose llm-providers guidance when the problem names OpenAI, Ollama, Azure OpenAI, Gemini, Bedrock, Anthropic, VoyageAI, Zhipu, VLM, rerank, role-specific LLMs, or embedding prefixes.

## Minimal Embedded Pattern

```python
import asyncio
from lightrag import LightRAG, QueryParam

async def main():
    rag = LightRAG(
        working_dir="./rag_storage",
        llm_model_func=your_llm_func,
        embedding_func=your_embedding_func,
    )
    await rag.initialize_storages()
    try:
        await rag.ainsert("LightRAG builds a graph from documents.")
        result = await rag.aquery("What does LightRAG build?", param=QueryParam(mode="mix"))
        print(result)
    finally:
        await rag.finalize_storages()

asyncio.run(main())
```

## Non-Negotiables

- Always initialize storages before `ainsert`, `aquery`, graph, delete, or cache operations; always finalize storages during cleanup.
- Do not call synchronous wrappers from an already running event loop; use async methods in async apps.
- Keep embedding model, embedding dimension, and existing vector storage aligned; changing embeddings requires rebuilding or clearing vector data.
- Treat optional provider/storage/parser services as explicit dependencies; do not assume API keys, databases, parser services, or local model servers exist.
- Do not run destructive storage tools, document clear/delete operations, or graph mutations while ingestion or another writer is active for the same workspace.
- Keep public examples free of secrets, machine-specific paths, local environment names, and original source-checkout dependencies.
