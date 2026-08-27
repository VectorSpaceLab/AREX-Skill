---
name: similarity-search
description: "Score text pairs and run dense or BM25 retrieval with text2vec."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Similarity Search

Use this sub-skill when you need sentence similarity, pair scoring, semantic search, or lexical BM25 retrieval in `text2vec`.

## Route here for

- Pairwise similarity with `Similarity`, `SimilarityType`, `EmbeddingType`, `get_score`, `get_scores`, and `similarity`.
- Dense retrieval helpers with `cos_sim` and `semantic_search` for tensor or NumPy embeddings.
- Raw-text BM25 retrieval with Jieba segmentation and top-k ranking.
- Aligned pair scoring from JSONL, CSV, or TSV without accidentally building a full cross-product matrix.
- Query-to-corpus retrieval workflows where you want either no-network BM25 now or dense search from cached embeddings later.

## Do not handle here

- Embedding initialization, batch vector generation, or CLI embedding export: route to `embeddings`.
- Fine-tuning, training data validation, and negative mining: route to `training-finetuning`.
- Benchmark-style model quality evaluation and leaderboard comparison: route to `evaluation-benchmarks`.
- HTTP serving, FastAPI, Jina, or Gradio deployment: route to `serving-deployment`.

## Operating workflow

1. Decide whether the task is pair scoring or retrieval.
2. For pair scoring, choose vector-only scoring or model-backed scoring.
3. For retrieval, choose BM25 when you want a no-network lexical path, or dense search when you already have embeddings or a cached model.
4. Read the API shapes in [references/api-reference.md](references/api-reference.md).
5. Use the bundled helpers in [scripts/](scripts/) for safe JSONL/CSV/TSV workflows.
6. Check [references/troubleshooting.md](references/troubleshooting.md) if scores, shapes, or downloads look wrong.

## Bundled scripts

- [`scripts/score_pairs.py`](scripts/score_pairs.py): score aligned text pairs from JSONL, CSV, or TSV using supplied vectors or `Similarity`.
- [`scripts/search_corpus.py`](scripts/search_corpus.py): search a corpus with BM25 or dense embeddings and return top-k hits.

Start with [references/workflows.md](references/workflows.md) for ready-to-run patterns and [references/api-reference.md](references/api-reference.md) for return shapes.