# Retrieval and RAG API Reference

This reference uses public Haystack imports and is intended to be usable without reopening the source repository.

## Core data and store APIs

- `from haystack import Document, Pipeline, AsyncPipeline`: documents and pipeline orchestration are public root exports.
- `from haystack.document_stores.in_memory import InMemoryDocumentStore`: local ephemeral store for smoke tests, examples, and small applications.
- `InMemoryDocumentStore(...)` accepts BM25 controls (`bm25_tokenization_regex`, `bm25_algorithm`, `bm25_parameters`), embedding similarity (`embedding_similarity_function="dot_product"|"cosine"`), optional shared `index`, async executor, and `return_embedding` default behavior.
- The in-memory store keeps documents in process memory; same `index` lets multiple instances share storage in the same process. Use a unique index for isolated tests.
- Store methods commonly used here: `write_documents`, `write_documents_async`, `count_documents`, `filter_documents`, `filter_documents_async`, `bm25_retrieval`, `bm25_retrieval_async`, `embedding_retrieval`, and `embedding_retrieval_async`.

## Duplicate and filter policies

```python
from haystack.document_stores.types import DuplicatePolicy, FilterPolicy
```

- `DuplicatePolicy.NONE`: let the store decide duplicate behavior.
- `DuplicatePolicy.SKIP`: skip existing document IDs.
- `DuplicatePolicy.OVERWRITE`: replace existing document IDs.
- `DuplicatePolicy.FAIL`: raise on duplicate IDs.
- `FilterPolicy.REPLACE`: runtime filters replace constructor filters on retrievers.
- `FilterPolicy.MERGE`: runtime filters are shallow-merged into constructor filters to narrow retrieval.

Prefer explicit policies in repeatable indexing code so retries are predictable.

## Filter syntax

Haystack filters are dictionaries. The portable explicit form is:

```python
{"field": "meta.category", "operator": "==", "value": "docs"}
```

Use metadata filters to constrain retrieval by fields such as language, source, tenant, date, or document type. For compound filtering, use the documented logical operators supported by the selected document store. When debugging, first run `store.filter_documents(filters)` before adding retrieval scoring.

## Writers

```python
from haystack.components.writers import DocumentWriter
```

- Constructor: `DocumentWriter(document_store, policy=DuplicatePolicy.NONE)`.
- `run(documents, policy=None)` returns `{"documents_written": int}`.
- `run_async(documents, policy=None)` requires the store to implement async writing.
- Use `DocumentWriter` inside indexing pipelines; direct `store.write_documents` is fine for tests and scripts.

## Text and embedding retrievers

```python
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever, InMemoryEmbeddingRetriever
from haystack.components.retrievers import FilterRetriever
```

- `InMemoryBM25Retriever(document_store, filters=None, top_k=10, scale_score=False, filter_policy=FilterPolicy.REPLACE)` runs with `query`, optional `filters`, `top_k`, and `scale_score`; it returns `{"documents": list[Document]}`.
- `InMemoryEmbeddingRetriever(document_store, filters=None, top_k=10, scale_score=False, return_embedding=False, filter_policy=FilterPolicy.REPLACE)` runs with `query_embedding`, optional `filters`, `top_k`, `scale_score`, and `return_embedding`.
- `FilterRetriever(document_store, filters=None)` returns all documents matching filters without relevance scoring.
- `top_k` must be greater than zero for in-memory retrievers.
- BM25 works with plain text documents. Embedding retrieval requires document embeddings and query embeddings with the same dimensionality and model family.

## Multi-query and wrapper retrievers

```python
from haystack.components.retrievers import MultiQueryTextRetriever, MultiQueryEmbeddingRetriever, TextEmbeddingRetriever
```

- `MultiQueryTextRetriever(retriever, max_workers=3)` runs a text retriever for each query, deduplicates documents, and sorts by score.
- `MultiQueryEmbeddingRetriever(retriever, query_embedder, max_workers=3)` expands embedding retrieval across multiple queries/embeddings.
- `TextEmbeddingRetriever(retriever, query_embedder)` wraps a query embedder and an embedding retriever so pipeline input can be text rather than an embedding vector.
- Call `warm_up()` explicitly for embedders/rankers/readers/generators that load models, or rely on pipeline warm-up where appropriate.

## Context expansion retrievers

```python
from haystack.components.retrievers import SentenceWindowRetriever
from haystack.components.retrievers.auto_merging_retriever import AutoMergingRetriever
```

- `SentenceWindowRetriever(document_store, window_size=3, source_id_meta_field="source_id", split_id_meta_field="split_id", raise_on_missing_meta_fields=True)` expects retrieved chunks to include source and split metadata. It returns `context_windows` and `context_documents`.
- `AutoMergingRetriever(document_store, threshold=0.5)` expects hierarchical metadata on matched leaf documents: `__parent_id`, `__level`, `__block_size`; parent documents in the store need `__children_ids`. Threshold must be between 0 and 1.
- These components are usually placed after a base retriever and before prompt building, reading, or final ranking.

## Joiners

```python
from haystack.components.joiners import DocumentJoiner
```

`DocumentJoiner(join_mode="concatenate", weights=None, top_k=None, sort_by_score=True)` joins multiple document lists. Supported join modes:

- `concatenate`: deduplicate by document ID and keep the highest-scored duplicate.
- `merge`: weighted sum of duplicate scores; `weights` must match input list count and not sum to zero.
- `reciprocal_rank_fusion`: rank-fusion merge useful for hybrid retrieval.
- `distribution_based_rank_fusion`: rescales score distributions before merging.

Connect multiple retriever outputs to a joiner, then optionally rank and slice with `top_k`.

## Rankers and readers

```python
from haystack.components.rankers import MetaFieldRanker, LostInTheMiddleRanker
from haystack.components.readers import ExtractiveReader
```

- `MetaFieldRanker(meta_field, weight=1.0, top_k=None, ranking_mode="reciprocal_rank_fusion", sort_order="descending", missing_meta="bottom", meta_value_type=None)` combines retrieval score and metadata order.
- `LostInTheMiddleRanker(word_count_threshold=None, top_k=None)` reorders already-ranked text documents to place high-relevance documents at context edges.
- Similarity rankers such as sentence-transformers/transformers variants may require optional model dependencies and warm-up.
- `ExtractiveReader(model="deepset/roberta-base-squad2-distilled", top_k=20, score_threshold=None, ...)` returns extracted answers from documents but requires transformer/torch dependencies and is deprecated for Haystack 3 in favor of the transformers integration package.

## Retrieval metric selection

This route does not implement evaluators, but it should pick retrieval metrics for validation plans:

- Use recall when the question is “did any relevant document appear in the retrieved set?”
- Use MRR when first relevant rank matters, especially for single-answer lookup tasks.
- Use NDCG when there are graded relevance labels or multiple relevant documents with different quality.
- Track retrieved document count, empty-result rate, filter hit rate, duplicate rate after joiners, and latency separately from answer quality.

## Common imports

```python
from haystack import Document, Pipeline
from haystack.components.joiners import DocumentJoiner
from haystack.components.rankers import LostInTheMiddleRanker, MetaFieldRanker
from haystack.components.retrievers import FilterRetriever, MultiQueryTextRetriever, SentenceWindowRetriever
from haystack.components.retrievers.auto_merging_retriever import AutoMergingRetriever
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever, InMemoryEmbeddingRetriever
from haystack.components.writers import DocumentWriter
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.document_stores.types import DuplicatePolicy, FilterPolicy
```
