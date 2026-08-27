---
name: rag-and-vector-search
description: "Use for Feast RAG, vector search, vector-indexed fields, vector
  online stores, document embedding/chunking, retrieve_online_documents APIs,
  DocEmbedder, FeastVectorStore, and FeastRAGRetriever workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Feast RAG And Vector Search

Use this sub-skill when the user asks to build, configure, debug, or validate Feast-powered vector retrieval or RAG workflows.

## Route Here For

- Vector schema fields using `Field(..., vector_index=True, vector_length=..., vector_search_metric=...)`.
- Vector online store choices and `feature_store.yaml` settings for Milvus, SQLite vector mode, Postgres/pgvector, Elasticsearch, Qdrant, MongoDB, or Faiss.
- SDK retrieval with `FeatureStore.retrieve_online_documents_v2(...)` or legacy `retrieve_online_documents(...)`.
- RAG helper APIs: `DocEmbedder`, `TextChunker`, `MultiModalEmbedder`, `FeastVectorStore`, `FeastIndex`, and `FeastRAGRetriever`.
- Document ingestion: chunk documents, create embeddings, write vectors to the online store, retrieve top-k context, and format context for an LLM.

## Route Elsewhere

- Generic Feast object modeling that is not vector-specific: `../feature-definitions/SKILL.md`.
- Non-vector online/historical retrieval, materialization, or push ingestion: `../retrieval-and-materialization/SKILL.md`.
- Feature server, MCP, auth, TLS, and remote endpoint setup: `../servers-and-remote/SKILL.md`.
- Optional dependency selection across non-vector stores or custom store implementation: `../integrations-and-extensibility/SKILL.md`.

## Start Here

1. Read `references/vector-reference.md` to choose schema, store config, and retrieval API.
2. Read `references/rag-workflows.md` for document ingestion, DocEmbedder, FeastVectorStore, and FeastRAGRetriever patterns.
3. Use `references/troubleshooting.md` for install, optional extra, vector dimension, service, and API failures.
4. Run `scripts/vector_config_lint.py --help` before asking users to connect to a vector database.

## Fast Safety Checks

```bash
python scripts/vector_config_lint.py path/to/feature_repo.py
python scripts/vector_config_lint.py feature_store.yaml --config-only
python scripts/vector_config_lint.py vector_snippet.json
```

Expected success output includes `OK:` lines and a final `Summary:`. Any `ERROR:` should be fixed before `feast apply`, materialization, or remote service debugging.
