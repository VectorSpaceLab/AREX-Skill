---
name: rag-document-processing
description: "Guides LazyLLM RAG, document ingestion, readers, transforms,
  retrievers, rerankers, stores, BM25, and parser-service workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LazyLLM RAG and Document Processing

Use this sub-skill for LazyLLM tasks involving `Document`, `DocNode`, document readers, transforms, node groups, retrievers, rerankers, BM25, stores/indexes, document service metadata, parser service, Milvus/OpenSearch, or RAG examples.

## Start here when

- The task mentions `lazyllm.tools.rag`, `Document`, `Retriever`, `Reranker`, `DocNode`, node groups, chunking, embedding, reranking, or BM25.
- An import error says to run `lazyllm install rag`.
- The user wants a local RAG app, parser-service architecture, URL/file retriever, map store, Milvus/OpenSearch index, or RAG with online/local model modules.
- You need to separate local text retrieval from optional embedding/vector database/model backends.

## Files to read

- [rag-workflows.md](references/rag-workflows.md) for local RAG recipes, object relationships, and backend escalation.
- [data-and-service-formats.md](references/data-and-service-formats.md) for document/node/service request shapes and parser-service boundaries.
- [troubleshooting.md](references/troubleshooting.md) for missing dependencies, parser service, vector DB, and retrieval issues.
- [scripts/rag_bm25_smoke.py](scripts/rag_bm25_smoke.py) for a no-network BM25 retrieval check.

## Safe RAG workflow

1. **Install/check the RAG extra** when importing RAG objects:
   ```bash
   lazyllm install rag
   python ../../scripts/check_lazyllm_env.py --require-rag
   ```
2. **Start local and text-only.** Use `DocNode` and BM25 or local readers before adding embeddings, rerankers, vector DBs, or model modules.
3. **Decide ownership of model nodes.** Model modules used for embeddings/reranking/chat belong to [model-deployment](../model-deployment/SKILL.md) for backend checks.
4. **Decide service boundaries.** Parser service, document service, Milvus/OpenSearch/Redis, object storage, and external URLs require service credentials or local fixtures.
5. **Run local smoke.**
   ```bash
   python scripts/rag_bm25_smoke.py
   ```

## Key public surfaces

- `Document(*args, **kw)` is the main RAG container and index manager.
- `Retriever(doc, group_name, similarity=None, similarity_cut_off=-inf, index='default', topk=6, embed_keys=None, target=None, output_format=None, join=False, weight=None, priority=None, **kwargs)` pulls contexts from a document/index.
- `Reranker(name='ModuleReranker', *args, **kwargs)` reranks retrieved contexts and may depend on a model/backend.
- `DocNode` represents text chunks with metadata and relationships.
- BM25 supports local English/Chinese retrieval with no embedding server.

## Backend posture

- **Required for local guidance:** base LazyLLM plus `rag` extra.
- **Safe CPU candidates:** BM25, document/node transforms, reader utilities, retriever logic, local doc-service manager with SQLite/mocked parser client.
- **Optional external services:** Milvus, OpenSearch/Elasticsearch, Redis/RedisVL, parser service workers, object storage, remote URLs.
- **Optional model/GPU:** embedding models, rerankers, local LLM answer generation, multimodal OCR/audio ingestion.

## Handoff checklist

When you complete a RAG task, report:

- document source type and data format,
- node/chunking/grouping plan,
- retrieval method and index/store backend,
- model/embedding/reranker backend status,
- local smoke command or reason it is optional/skipped,
- clear separation between local artifacts and external services.
