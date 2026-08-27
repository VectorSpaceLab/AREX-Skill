---
name: retrieval-rag-and-data-pipelines
description: "Document preprocessing, LocalDB persistence, retriever indexing,
  and RAG context assembly."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Retrieval, RAG, and Data Pipelines

Use this sub-skill when the task is to prepare documents, split text, persist local data, build retriever indexes, convert retrieval output into context, or assemble a retrieval-first RAG flow.

## Route here for

- `Document` modeling for text corpora and chunked passages.
- `TextSplitter` chunking rules, separator choices, overlap settings, and invalid chunk-shape troubleshooting.
- `ToEmbeddings` and `RetrieverOutputToContextStr` as retrieval-side data transforms.
- `LocalDB` load/extend/transform/save/load flows for documents and chunked corpora.
- Retriever base contracts and concrete retrieval backends: `BM25Retriever`, `FAISSRetriever`, `LanceDBRetriever`, `QdrantRetriever`, and `PostgresRetriever`.
- Retrieval-oriented RAG assembly patterns: split, embed, persist, retrieve, deduplicate, and pass context downstream.

## Do not handle here

- Provider/client selection, embedding model setup, or generator configuration: route to the model-client-and-generator-workflows sub-skill.
- Metrics, evaluator loops, prompt optimization, or retriever scoring analysis: route to the evaluation-and-optimization sub-skill.
- Agentic RAG, tool use, runner orchestration, or streaming event handling: route to the agents-tools-and-streaming sub-skill.
- Model training or optimization of retriever/generator parameters: route to the evaluation-and-optimization sub-skill.

## Operating workflow

1. Normalize inputs into `Document` objects and keep raw metadata with the corpus.
2. Choose the lightest valid preprocessing path:
   - `TextSplitter` for chunking plain text.
   - `ToEmbeddings` when chunks need vectors.
   - `LocalDB` when you need persistence, transform reuse, or staged filtering.
3. Pick the retrieval backend:
   - `BM25Retriever` for lexical or keyword-first retrieval.
   - `FAISSRetriever` for local vector search.
   - `LanceDBRetriever`, `QdrantRetriever`, or `PostgresRetriever` when the index lives in an optional store.
4. Use `RetrieverOutputToContextStr` to assemble retrieved chunks into a downstream context string.
5. Build the RAG boundary with a retrieval step, a context builder, and a downstream answer component from another sub-skill.
6. When retrieval fails, consult [troubleshooting](references/troubleshooting.md) before changing the corpus or the retrieval contract.

## Bundled scripts

- [`scripts/text_splitter_smoke.py`](scripts/text_splitter_smoke.py): deterministic `TextSplitter` smoke check with a tiny `Document`.
- [`scripts/localdb_smoke.py`](scripts/localdb_smoke.py): `LocalDB` load/transform/save/load smoke using a safe bundled transform.

Start with [data pipelines](references/data-pipelines.md) for document and transform contracts, [retrievers](references/retrievers.md) for backend selection, and [RAG recipes](references/rag-recipes.md) for assembly patterns.
