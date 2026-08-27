---
name: indexing-and-querying
description: "Build and query LlamaIndex indexes, persist and reload storage,
  configure retrievers/query engines/response synthesizers, and choose advanced
  retrieval patterns."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Indexing and Querying

Use this sub-skill when a user needs practical LlamaIndex RAG mechanics after data has already been loaded or chunked into `Document` or `BaseNode` objects.

## Owns

- Build `VectorStoreIndex` and `SummaryIndex` from documents or nodes.
- Persist and reload indexes with `StorageContext` and `load_index_from_storage`.
- Configure `as_retriever`, `as_query_engine`, `VectorIndexRetriever`, `RetrieverQueryEngine`, and response synthesizers.
- Compose advanced retrieval with `QueryFusionRetriever`, `RouterRetriever`, `RecursiveRetriever`, `RouterQueryEngine`, and `SubQuestionQueryEngine`.
- Diagnose indexing/query failures such as missing models, empty retrieval, persistence path mistakes, filters, tool metadata, and async/synthesis mode issues.

## Route Elsewhere

- Use `../ingestion-and-loading/` for file readers, loaders, chunking, `SentenceSplitter`, `IngestionPipeline`, metadata extraction, and node creation.
- Use `../integrations-and-storage/` for provider-specific vector stores, database/cloud installs, and integration-specific credentials.
- Use `../customization-and-structured-outputs/` for prompt templates, structured outputs, Pydantic output classes, and output formatting.

## Quick Start

```python
from llama_index.core import Document, Settings, VectorStoreIndex
from llama_index.core.embeddings.mock_embed_model import MockEmbedding
from llama_index.core.llms.mock import MockLLM

Settings.embed_model = MockEmbedding(embed_dim=8)
Settings.llm = MockLLM(max_tokens=64)

index = VectorStoreIndex.from_documents([
    Document(text="LlamaIndex builds indexes over nodes."),
    Document(text="Retrievers fetch relevant nodes for a query engine."),
])
query_engine = index.as_query_engine(similarity_top_k=2)
print(query_engine.query("What do retrievers do?"))
```

For a no-network smoke test, run the bundled script:

```bash
python sub-skills/indexing-and-querying/scripts/build_tiny_mock_index.py
```

## Workflow

1. Confirm the user already has `Document` or node objects; if not, route loading/chunking to `ingestion-and-loading`.
2. Choose index type: `VectorStoreIndex` for semantic similarity retrieval; `SummaryIndex` for small ordered corpora, summaries, or query-all behavior.
3. Set explicit `Settings.embed_model` and `Settings.llm` or pass models directly to constructors/query engines; avoid accidental remote defaults when the environment has no API keys.
4. Build with `VectorStoreIndex.from_documents(documents)` or `VectorStoreIndex(nodes=nodes)`; constructors accept nodes, not raw `Document` objects.
5. Query simply with `index.as_query_engine(...)`, or split retrieval/synthesis with `index.as_retriever(...)`, `get_response_synthesizer(...)`, and `RetrieverQueryEngine(...)`.
6. Persist using `index.storage_context.persist(persist_dir=...)`; reload with `StorageContext.from_defaults(persist_dir=...)` and `load_index_from_storage(...)`.
7. For multi-index systems, wrap engines/retrievers as tools with clear metadata before using routers or sub-question engines.

## References

- `references/index-query-recipes.md`: practical recipes for indexes, persistence, retrieval, routers, fusion, and synthesis.
- `references/api-reference.md`: verified constructor signatures and import paths for indexing/query APIs.
- `references/troubleshooting.md`: failure-mode diagnosis for embeddings, LLMs, storage, filters, routing, async, and optional integrations.
