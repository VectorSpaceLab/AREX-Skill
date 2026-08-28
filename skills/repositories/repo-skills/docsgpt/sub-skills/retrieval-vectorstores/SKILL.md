---
name: retrieval-vectorstores
description: "Guides DocsGPT embeddings, vector-store selection, per-source retrieval, classic and hybrid RAG, pre-screening, GraphRAG, and retrieval diagnosis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Retrieval and Vector Stores

Use this sub-skill to select embeddings/vector storage, configure per-source retrieval, tune ranking, enable GraphRAG, or diagnose missing/poor context.

## Route by decision

- **Embedding or vector-store selection/migration**: read [embeddings and vector stores](references/embeddings-and-vectorstores.md).
- **Classic, hybrid, exposure, top-k, threshold, rephrase, or pre-screen**: read [retrieval routing](references/retrieval-routing.md).
- **GraphRAG**: read [GraphRAG](references/graphrag.md) before enabling it; it is pgvector-only and performs LLM extraction.
- **Empty/low-quality/slow results**: read [troubleshooting](references/troubleshooting.md).

## Verified registries

At this snapshot, `VectorCreator` accepts:

```text
faiss, elasticsearch, mongodb, qdrant, milvus, pgvector
```

Retriever keys are:

```text
classic, default, hybrid, graphrag
```

`default` maps to classic behavior. A source retriever must also be allowed by `RETRIEVERS_ENABLED`.

A LanceDB implementation/settings surface exists in the codebase but is not registered in `VectorCreator` at this snapshot. Do not claim that `VECTOR_STORE=lancedb` works without verifying a newer checkout or adding/validating registration.

## Plan before changing data

1. Record current embedding model/endpoint and actual vector dimension.
2. Record selected vector store, source count, chunk count and backup/export path.
3. Define target retrieval behavior per source.
4. Validate feature compatibility offline:

   ```bash
   python scripts/validate_retrieval_plan.py \
     --vector-store pgvector \
     --retriever hybrid
   ```

5. Test one tiny source and expected query.
6. Re-ingest when embeddings, vector dimensions, chunking, or GraphRAG extraction inputs changed.
7. Compare retrieval results and citations before removing old data.

## Compatibility rules

- Hybrid keyword search is implemented for pgvector. On other stores it degrades to vector-only behavior, so do not promise keyword recall.
- `score_threshold` is honored by pgvector and MongoDB Atlas; other stores may ignore it.
- GraphRAG requires `VECTOR_STORE=pgvector` and `GRAPHRAG_ENABLED=true`; enable it through the dedicated source action.
- A source with graph extraction pending/failed falls back to classic vector retrieval.
- Remote embeddings avoid loading a local sentence-transformer but still require endpoint/key, dimension consistency, and input limits.
- Approximate pgvector indexes can return too few source-filtered rows when badly sized; exact search is often preferable for smaller corpora.

## Retrieval validation

For a representative query, record:

- resolved source ids and source configs;
- request top-k versus effective source top-k;
- retriever and exposure mode;
- rephrased query, if enabled;
- candidate/survivor counts for pre-screen;
- scores and threshold handling when supported;
- vector/keyword/graph contributions;
- citations passed to the model;
- fallback or warnings.

Do not diagnose answer quality until proving whether the expected chunks reached the model.

## Cross-skill routes

- Parsing, chunking and re-ingestion: [ingest-sources](../ingest-sources/SKILL.md)
- LLM/model catalog and service deployment: [deploy-configure](../deploy-configure/SKILL.md)
- Agent prefetch versus internal-search behavior: [agents-workflows](../agents-workflows/SKILL.md)
