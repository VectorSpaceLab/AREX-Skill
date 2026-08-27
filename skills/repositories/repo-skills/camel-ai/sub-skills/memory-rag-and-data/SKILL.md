---
name: memory-rag-and-data
description: "Build CAMEL memory, retrieval/RAG, embedding, storage, loader,
  datahub, and dataset workflows while keeping data formats, optional extras,
  and backend constraints explicit."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Memory, RAG, And Data

Use this sub-skill when the task is to add memory to CAMEL agents, build a retrieval or RAG pipeline, select embedding/vector/key-value/object/graph storage, ingest files or web data, or validate dataset/datahub flows.

## Route By Task

- **Agent memory:** Read [references/workflows.md](references/workflows.md) for `ChatHistoryMemory`, `VectorDBMemory`, `LongtermAgentMemory`, `MemoryRecord`, `ScoreBasedContextCreator`, and attaching memory to `ChatAgent`.
- **Retrieval/RAG:** Read [references/workflows.md](references/workflows.md) and [references/api-reference.md](references/api-reference.md) for `VectorRetriever`, `AutoRetriever`, `HybridRetriever`, BM25/rerank retrievers, chunking, result schemas, and empty-result debugging.
- **Storage choice:** Read [references/storage-selection.md](references/storage-selection.md) before choosing Qdrant, Chroma, FAISS, Milvus, TiDB, PgVector, Weaviate, Surreal, OceanBase, JSON, Redis, object storage, or graph storage.
- **Loaders/data:** Read [references/data-workflows.md](references/data-workflows.md) for `BaseIO`, `UnstructuredIO`, `MarkItDownLoader`, API-backed loaders, Hugging Face datahubs, and dataset generators.
- **Safe API inspection:** Run [scripts/inspect_rag_components.py](scripts/inspect_rag_components.py) to confirm installed imports, signatures, optional dependencies, and no-network component availability.
- **Failures:** Read [references/troubleshooting.md](references/troubleshooting.md) for extras, Python-version caveats, embedding credentials, vector dimensions, persistence, loader/network keys, graph auth, token budget, and retrieval-empty issues.

## Boundary Notes

- Keep provider/model setup minimal here; use the sibling models sub-skill for `ModelFactory`, `BaseModelBackend`, and provider credentials beyond embedding-specific keys.
- Keep tool execution and MCP patterns in the tools-oriented sibling sub-skill; this sub-skill only covers data ingestion and retrieval surfaces.
- Keep datagen benchmark/evaluation pipelines in the sibling `datagen-evaluation-and-benchmarks` sub-skill; this sub-skill only covers `camel.datasets` and data formats needed by memory/RAG work.

## Quick Start Checklist

1. Pick an embedding first and record `embedding.get_output_dim()`.
2. Create vector storage with the exact same `vector_dim`; decide ephemeral, local persistent path, or remote service.
3. Ingest local fixtures in CI with `VectorRetriever.process(content=...)` or explicit `VectorRecord` objects; avoid network loaders in tests.
4. Query with a positive `top_k`, low-enough `similarity_threshold`, and inspect returned payload keys such as `text`, `metadata`, and `content path`.
5. Attach memory to `ChatAgent(memory=...)` or assign `agent.memory = memory`; validate `memory.get_context()` fits the model token budget.
6. Run the bundled inspection script before depending on optional extras such as `rag`, `storage`, or `document_tools`.
