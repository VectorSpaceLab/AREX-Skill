# Retrieval Workflow Reference

## Dense semantic search pattern

1. Prepare a corpus list and keep its order stable.
2. Encode corpus texts once with `convert_to_tensor=True` or `convert_to_numpy=True` depending on downstream search.
3. Encode queries with the matching retrieval prompt or method.
4. Call `semantic_search(query_embeddings, corpus_embeddings, top_k=...)`.
5. Map every hit's `corpus_id` back to `corpus[corpus_id]` or to a parallel metadata table.

Preserve this invariant: `corpus_id` is an index into the exact corpus embedding matrix used for search. If the corpus is filtered, chunked, sharded, or de-duplicated, store an explicit external ID next to each embedding and map it after retrieval.

## Retrieve then rerank

Dense retrieval is fast and approximate at the semantic level; a CrossEncoder reranker is slower but scores query-document pairs jointly. Use the dense stage to retrieve a manageable candidate set, then rerank candidates while preserving IDs.

```python
from sentence_transformers.util import semantic_search

hits = semantic_search(query_emb, corpus_emb, top_k=100)[0]
candidates = [corpus[hit["corpus_id"]] for hit in hits]
reranked = cross_encoder.rank(query, candidates, top_k=10, return_documents=True)

final = []
for row in reranked:
    original_hit = hits[row["corpus_id"]]
    final.append({
        "corpus_id": original_hit["corpus_id"],
        "text": candidates[row["corpus_id"]],
        "retriever_score": original_hit["score"],
        "reranker_score": row["score"],
    })
```

Why this mapping matters: `CrossEncoder.rank` returns `corpus_id` relative to the `documents` list it received, not necessarily the original corpus. Convert it back through the dense hit list before returning final IDs.

Routing notes:

- Use this sub-skill for orchestration and ID preservation.
- Use `../reranking-cross-encoder/SKILL.md` for CrossEncoder model loading, activation, `predict`, and `rank` details.
- Use a larger dense `top_k` such as 50-200 before reranking when recall matters; use a smaller value for latency-sensitive tasks.

## Corpus chunking and memory tradeoffs

`semantic_search` builds similarity blocks of approximately `query_chunk_size * corpus_chunk_size` scores.

- Increase chunk sizes for throughput if memory is available.
- Decrease `query_chunk_size` when many queries cause large intermediate score matrices.
- Decrease `corpus_chunk_size` when corpus embeddings are large or GPU/CPU memory is tight.
- Keep `top_k` at the presentation or reranker candidate count; inflated `top_k` increases heap and post-processing cost.
- For very large corpora, prefer approximate/vector indexes rather than scanning all embeddings per query.

Practical progression:

- Small corpus: exact `semantic_search` in memory.
- Medium corpus: exact search with tuned chunks and precomputed embeddings.
- Large corpus: FAISS/USearch, a vector database, or a search service; keep `corpus_id`/external ID mapping explicit.
- Production QA/search: dense retrieval top-k plus CrossEncoder reranking.

## Quantized retrieval

Use embedding quantization when the bottleneck is embedding memory, disk, transfer, or vector index latency.

- `precision="binary"` or `"ubinary"` gives the largest storage reduction; retrieve extra candidates and rescore when quality matters.
- `precision="int8"` or `"uint8"` is a scalar compression choice that typically preserves more information than binary but needs calibration.
- Keep queries in float32 when using quantized corpus rescoring with FAISS/USearch utilities.
- Use `rescore_multiplier` to retrieve extra quantized candidates before rescoring back to `top_k`.
- Use the precision expected by the external system: some libraries expect unsigned binary (`ubinary`/`uint8`), others signed packed bytes.

Do not confuse embedding quantization with model quantization. Model export and backend optimization belong in `../backend-export-optimization/SKILL.md`.

## Vector DB and external service cautions

The repository examples include FAISS, USearch, Annoy, hnswlib, Elasticsearch, OpenSearch, and Qdrant-style patterns. Treat those as integration patterns, not mandatory runtime dependencies.

- Install optional packages explicitly (`faiss-cpu`, `faiss-gpu`, `usearch`, vector DB clients, search service clients) only for the chosen backend.
- Confirm the metric expected by the backend: cosine, inner product, L2, Hamming, or service-specific aliases.
- Normalize embeddings before dot-product/IP search when you want cosine-equivalent ranking.
- Store external document IDs and metadata outside the vector order if the backend can compact, shard, or reassign internal IDs.
- Batch indexing and querying; single-vector calls often dominate latency.
- Record whether returned scores are similarity, distance, or transformed distance; higher-is-better is not universal outside `semantic_search`.
- Avoid hardcoding hosted-service credentials, endpoints, or collection names in reusable scripts.

## Hard-negative mining workflow

Use hard-negative mining when building training/evaluation datasets from known query-positive pairs.

1. Inspect dataset columns and set `anchor_column_name`/`positive_column_name` explicitly.
2. Decide whether candidate negatives come from positives only or from a separate `corpus`.
3. Pick filters: `range_min`, `range_max`, `max_score`, `min_score`, `absolute_margin`, and/or `relative_margin`.
4. Choose `output_format` based on the training/evaluation consumer.
5. Add `output_scores=True` if later losses, analysis, or teacher distillation need scores.
6. Consider `cross_encoder` only when the extra reranking cost is justified.
7. Review skip statistics; too many skipped negatives usually means filters are too strict or `range_max` is too small.

Format routing:

- Use `triplet` for simple anchor-positive-negative examples.
- Use `n-tuple` for one anchor with multiple negatives and ranking-preserving workflows.
- Use `labeled-pair` for binary relevance pair classifiers.
- Use `labeled-list` for listwise reranking losses or evaluators.

## Paraphrase and community workflows

- Use `paraphrase_mining` to find globally highest-scoring near-duplicate sentence pairs.
- Use `paraphrase_mining_embeddings` when embeddings are already computed or expensive to recompute.
- Use `community_detection` when the user asks for clusters/groups of similar texts above a threshold.
- Tune thresholds and minimum sizes empirically; a high threshold favors duplicates, a lower threshold finds broader topical groups.

## Difficult usability cases

- Dense retrieval plus CrossEncoder handoff: retrieve top 100 dense hits, rerank 10, and return original `corpus_id`, retriever score, reranker score, and text without mixing candidate-relative IDs with corpus-relative IDs.
- Hard-negative mining from columns `query` and `answer`: produce `labeled-list` with scores, `relative_margin=0.05`, `range_min` to skip likely positives, and enough `range_max` to avoid starving negatives.
