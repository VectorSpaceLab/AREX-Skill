# Retriever API and Configuration

FlashRAG exposes retrievers through configuration and helper factories. Most tasks should configure retrieval fields and call `get_retriever(config)` rather than instantiating retriever classes directly.

## Retriever Classes

| Component | Purpose | Required configuration | Optional dependencies |
| --- | --- | --- | --- |
| `BM25Retriever` | Lexical retrieval from BM25 index | `retrieval_method: bm25`, `bm25_backend`, `index_path`, `corpus_path`, `retrieval_topk` | `bm25s` plus stemming support, or `pyserini` plus Java. |
| `DenseRetriever` | Dense bi-encoder retrieval from Faiss index | `retrieval_method`, `retrieval_model_path`, `index_path`, `corpus_path`, pooling/query length/batch fields | `faiss`, `torch`, `transformers`; optionally `sentence-transformers`. |
| `MultiModalRetriever` | CLIP-style text/image retrieval | `retrieval_model_path`, `multimodal_index_path_dict`, `corpus_path`, `retrieval_topk` | `faiss`, `torch`, `transformers`, PIL; `requests` for URL images. |
| `SparseRetriever` | SPLADE/Seismic sparse neural retrieval | SPLADE model path, Seismic index path, corpus path, Seismic query settings | `seismic`, `torch`, `transformers`. |
| `SerperRetriever` | Google Serper web search | `retrieval_method: serper`, `serper_api_key`, `retrieval_topk` | `requests`; valid Serper API key and network access. |
| `MultiRetrieverRouter` | Runs multiple retrievers and merges results | `use_multi_retriever: True`, `multi_retriever_setting` | Dependencies for every child retriever and optional reranker. |
| `CrossReranker` | Cross-encoder reranking | `use_reranker: True`, `rerank_model_name`, `rerank_model_path` | `torch`, `transformers`. |
| `BiReranker` | Embedding-based reranking | Reranker model path plus pooling/max length/batch settings | Same as dense retrieval. |

## Core Retrieval Fields

| Field | Meaning | Common failure if wrong |
| --- | --- | --- |
| `retrieval_method` | Method/model key such as `bm25`, `e5`, `bge`, `contriever`, `clip`, `splade`, or `serper` | Wrong retriever class or wrong index filename assumptions. |
| `retrieval_model_path` | Local path or model id for dense/CLIP/SPLADE retriever | Model load failure or model/index embedding mismatch. |
| `index_path` | BM25 directory, dense `.index`, or Seismic index path | Missing index, wrong corpus order, incompatible Faiss index. |
| `multimodal_index_path_dict` | Dict with `text` and `image` index paths | `None` target index or text/image modality mismatch. |
| `corpus_path` | Corpus used to resolve retrieved ids into documents | Returned docs do not match index vectors if corpus changed. |
| `retrieval_topk` | Number of initial retrieved documents | Reranker may warn if fewer docs are retrieved than `rerank_topk`. |
| `retrieval_batch_size` | Query encoding batch size | GPU/CPU memory errors if too large. |
| `retrieval_query_max_length` | Query truncation length | Long queries silently lose tail content if too small. |
| `retrieval_use_fp16` | Half precision model inference | CPU or unsupported model/device precision issues. |
| `retrieval_pooling_method` | Dense pooling method | Reduced quality or warning when model config implies another pooling. |
| `instruction` | Query/document instruction behavior | Index/query embeddings may be inconsistent if build and retrieval differ. |
| `faiss_gpu` | Load Faiss index on GPU for retrieval | Requires GPU Faiss; CPU Faiss cannot satisfy GPU methods. |
| `use_sentence_transformer` | Use SentenceTransformers encoder | Requires package and should match the indexing command. |
| `save_retrieval_cache`, `use_retrieval_cache`, `retrieval_cache_path` | Retrieval cache behavior | Stale cache can hide index/corpus changes. |
| `silent_retrieval` | Progress-bar verbosity | Does not change retrieval semantics. |

## Calling Search

All local text retrievers support:

```python
results = retriever.search("question", return_score=False)
results, scores = retriever.batch_search(["q1", "q2"], return_score=True)
```

Expected document dictionaries usually include `contents`, and may include `id`, `title`, `text`, `source`, `corpus_path`, `is_multimodal`, or web fields such as `url`. BM25 Pyserini indexes may contain raw documents; if not, FlashRAG resolves doc ids against `corpus_path`.

For multimodal retrievers:

```python
results = retriever.search(query, target_modal="image", return_score=False)
results, scores = retriever.batch_search(queries, target_modal="text", return_score=True)
```

`query` modality is inferred: non-string values are image-like; strings beginning with `http` or ending in `.jpg`/`.png` are treated as images; other strings are treated as text.

## Reranker Settings

Enable reranking after initial retrieval:

```yaml
use_reranker: True
rerank_model_name: bge-reranker
rerank_model_path: BAAI/bge-reranker-base
rerank_topk: 5
rerank_max_length: 512
rerank_batch_size: 256
rerank_use_fp16: True
```

Reranking receives the retrieved document `contents`. Cross rerankers score query-document pairs with a sequence classification model; bi rerankers encode queries and docs and use dot products. Keep `retrieval_topk >= rerank_topk` unless intentionally testing low-recall behavior.

## Multi-Retriever Configuration

Use multi-retriever mode when combining BM25 with dense retrieval, merging separate corpora, or using multimodal plus text retrievers.

```yaml
use_multi_retriever: True
multi_retriever_setting:
  merge_method: rerank
  topk: 5
  rerank_model_name: bge-reranker
  rerank_model_path: BAAI/bge-reranker-base
  retriever_list:
    - retrieval_method: bm25
      corpus_path: corpus.jsonl
      index_path: indexes/bm25
      retrieval_topk: 10
      bm25_backend: bm25s
    - retrieval_method: e5
      corpus_path: corpus.jsonl
      index_path: indexes/e5_Flat.index
      retrieval_model_path: intfloat/e5-base-v2
      retrieval_pooling_method: mean
      retrieval_topk: 10
```

Merge methods:

- `concat`: concatenate results from all retrievers and preserve retriever source annotations.
- `rrf`: apply reciprocal rank fusion and keep `multi_retriever_setting.topk` results.
- `rerank`: rerank all retrieved documents and keep `topk`; requires reranker fields in `multi_retriever_setting`.

FlashRAG fills some child retriever defaults from the global config, but explicit child `corpus_path`, `index_path`, `retrieval_model_path`, and backend fields make debugging easier.

## Web Retrieval with Serper

`SerperRetriever` does not use `index_path` or `corpus_path`; it calls the Google Serper API and returns title/snippet/url-like dictionaries.

```yaml
retrieval_method: serper
retrieval_topk: 10
serper_api_key: ${SERPER_API_KEY}
serper_search_type: search
serper_location: United States
serper_gl: us
serper_hl: en
```

Do not hard-code API keys into committed configs. Pass credentials through environment-variable substitution, secrets management, or runtime config assembly.
