---
name: retrieval-and-indexing
description: "Build and diagnose FlashRAG corpora, BM25/dense/multimodal/web
  retrievers, indexes, rerankers, and multi-retriever configurations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Retrieval and Indexing

Use this sub-skill when the task is about FlashRAG corpus preparation, index construction, retriever configuration, reranking, multi-retriever fusion, multimodal retrieval, or web retrieval. Do not use it for generator/refiner internals, full pipeline/method selection, or base dataset/config conventions outside retrieval-specific fields.

## Route by Task

- **Prepare corpus JSONL**: validate `id` and `contents`, check title/text formatting, estimate chunking readiness, then see [data preparation](references/data-preparation.md).
- **Build indexes**: choose BM25 (`bm25s` or `pyserini`), dense Faiss, CLIP multimodal, or SPLADE/Seismic commands; see [indexing workflows](references/indexing-workflows.md).
- **Configure retrieval**: map `retrieval_method`, `retrieval_model_path`, `index_path`, `corpus_path`, pooling, Faiss GPU, cache, and batch settings; see [retriever API](references/retriever-api.md).
- **Add reranking or fusion**: configure `use_reranker` or `use_multi_retriever` with `concat`, `rrf`, or `rerank`; see [retriever API](references/retriever-api.md).
- **Debug failures**: missing optional dependencies, Java/Pyserini, Faiss CPU/GPU mismatch, malformed JSONL, model/index mismatches, or Serper credentials; see [troubleshooting](references/troubleshooting.md).

## Bundled Helpers

- `scripts/validate_corpus_jsonl.py` checks FlashRAG corpus JSONL shape and reports chunking/indexing risks without rewriting the corpus.
- `scripts/inspect_index_builder_args.py` validates and prints `python -m flashrag.retriever.index_builder` commands without importing heavy optional retrieval dependencies.

## Quick Commands

```bash
python skills/flashrag/sub-skills/retrieval-and-indexing/scripts/validate_corpus_jsonl.py corpus.jsonl --sample 20
python skills/flashrag/sub-skills/retrieval-and-indexing/scripts/inspect_index_builder_args.py --retrieval_method bm25 --corpus_path corpus.jsonl --save_dir indexes --bm25_backend bm25s
```

## FlashRAG Retrieval Mental Model

Each usable retriever needs a corpus and either an index or an external search service. BM25 indexes are directories, dense and CLIP indexes are Faiss `.index` files, multimodal CLIP may use separate `text` and `image` index paths, and Serper uses web API credentials instead of local index files.
