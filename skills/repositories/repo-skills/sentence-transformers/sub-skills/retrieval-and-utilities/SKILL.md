---
name: retrieval-and-utilities
description: "Dense semantic search utilities, retrieve-and-rerank
  orchestration, hard-negative mining, embedding quantization, similarity
  helpers, corpus chunking, and vector DB/service cautions for
  sentence-transformers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Retrieval and Utilities

Use this sub-skill when a task asks for dense retrieval, semantic search over precomputed embeddings, a retrieve-then-rerank handoff, hard-negative mining, embedding quantization for retrieval, paraphrase/community utilities, or similarity helper selection.

## Route the task

- For dense top-k search over embeddings, use `sentence_transformers.util.semantic_search`; see `references/api-reference.md`.
- For two-stage retrieval, first preserve `corpus_id` from dense hits, then hand the selected texts and IDs to a `CrossEncoder`; see `references/retrieval-reference.md`.
- For dataset construction, use `sentence_transformers.util.mine_hard_negatives` with explicit dataset column names, output format, and score/margin filters.
- For memory or latency pressure, tune `query_chunk_size`, `corpus_chunk_size`, `top_k`, embedding precision, and optional FAISS/USearch/vector DB integration.
- For cosine/dot/euclidean/manhattan behavior, paraphrase mining, community detection, and quantized embedding search, use the API notes before writing code.

## Boundaries

- Low-level `SentenceTransformer.encode` choices belong in `../embeddings-and-similarity/SKILL.md`.
- CrossEncoder constructor, prediction, ranking, and activation details belong in `../reranking-cross-encoder/SKILL.md`.
- SparseEncoder-specific search belongs in `../sparse-encoder-search/SKILL.md`.
- Training losses and evaluators belong in `../evaluation-and-training/SKILL.md`.

## Fast checks

- Run `python scripts/semantic_search_demo.py --help` to inspect the safe demo CLI.
- Run `python scripts/semantic_search_demo.py --toy-tensors` for a network-free semantic search example.
- Use `python scripts/semantic_search_demo.py --model MODEL_NAME_OR_PATH --local-files-only` only when the model is already available locally.

## References

- API contracts: `references/api-reference.md`
- Retrieval workflows: `references/retrieval-reference.md`
- Failure modes: `references/troubleshooting.md`
- Demo script: `scripts/semantic_search_demo.py`
