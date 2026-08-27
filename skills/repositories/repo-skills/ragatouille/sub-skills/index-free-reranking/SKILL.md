---
name: index-free-reranking
description: "Use RAGatouille for index-free ColBERT reranking, in-memory
  document encoding, transient encoded search, and encoded-state clearing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Index-Free Reranking

Use this sub-skill when a task needs RAGatouille without creating or loading a persisted index: rerank candidate documents from another retriever, encode a small transient document set in memory, search those encoded documents, or clear stale in-memory encodings.

## Route Here For

- Reranking external retriever results with `RAGPretrainedModel.rerank(query, documents, k=..., zero_index_ranks=..., bsize=...)`.
- Encoding small, already-chunked text lists with `RAGPretrainedModel.encode(documents, document_metadatas=..., max_document_length=...)`.
- Querying transient encoded documents with `RAGPretrainedModel.search_encoded_docs(query, k=..., bsize=...)`.
- Clearing expired in-memory encodings with `RAGPretrainedModel.clear_encoded_docs(force=True)`.
- Explaining single-query versus multi-query result shapes, metadata propagation, ranks, and small-dataset limits.

## Route Elsewhere

- Persisted indexes, `index()`, `search()`, `add_to_index()`, `delete_from_index()`, index roots, document IDs, and disk-backed metadata: `../pretrained-indexing-search/SKILL.md`.
- LangChain retriever/compressor wrappers and export helpers: `../integrations-export/SKILL.md`.
- Training, fine-tuning, data processors, and hard negative mining: `../training-data-finetuning/SKILL.md`.

## Fast Decision Guide

- Use `rerank()` when another retriever already produced a short candidate list and you only need ColBERT to rescore those candidate strings.
- Use `encode()` plus `search_encoded_docs()` when the whole working set is small, temporary, and should live only in the current `RAGPretrainedModel` instance.
- Use a persisted index instead when document counts are large, documents must survive process restart, document IDs are important, or repeated searches need optimized latency.

## References

- `references/api-reference.md`: verified signatures, return keys, rank semantics, and source-backed edge cases.
- `references/workflows.md`: rerank, encode/search/append, metadata, and clear-state recipes.
- `references/troubleshooting.md`: common failures and unsafe/expensive operations to avoid during lightweight checks.

## Offline Helper

Run `scripts/check_result_shapes.py --help` to inspect the bundled JSON shape checker. It validates sample `rerank()` and `search_encoded_docs()`-like results without importing RAGatouille, loading models, downloading checkpoints, or using GPUs.
