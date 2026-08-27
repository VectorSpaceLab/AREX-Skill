# Retrieval and Utility API Reference

## `semantic_search`

`sentence_transformers.util.semantic_search(query_embeddings, corpus_embeddings, query_chunk_size=100, corpus_chunk_size=500000, top_k=10, score_function=cos_sim)` performs exact top-k search over query and corpus embeddings.

- Inputs may be PyTorch tensors, NumPy arrays, or lists of tensors; one-dimensional query embeddings are promoted to a single-query batch.
- Query and corpus embeddings must have matching dimensions; the function moves query embeddings to the corpus device when needed.
- Output is `list[list[dict]]`, one result list per query, sorted by descending score.
- Each hit has `corpus_id` and `score`; `corpus_id` is the index into the original corpus embedding matrix.
- Default scoring is cosine similarity via `cos_sim`; pass `dot_score`, `euclidean_sim`, `manhattan_sim`, or a compatible callable when needed.
- It is intended for exact in-memory search over corpora up to roughly the low millions; use chunking, FAISS, USearch, or a vector service beyond that.

Example skeleton:

```python
from sentence_transformers.util import semantic_search, cos_sim

hits_by_query = semantic_search(
    query_embeddings,
    corpus_embeddings,
    top_k=20,
    query_chunk_size=32,
    corpus_chunk_size=100_000,
    score_function=cos_sim,
)
for hit in hits_by_query[0]:
    print(hit["corpus_id"], hit["score"])
```

## Similarity helpers

Import helpers from `sentence_transformers.util`.

- `cos_sim(a, b)` returns all-pairs cosine similarities after normalizing both inputs.
- `dot_score(a, b)` returns all-pairs dot products; use it for already-normalized embeddings when dot product equals cosine and speed matters.
- `euclidean_sim(a, b)` returns negative Euclidean distance, so larger values are better.
- `manhattan_sim(a, b)` returns negative Manhattan distance, so larger values are better.
- Pairwise variants such as `pairwise_cos_sim`, `pairwise_dot_score`, `pairwise_euclidean_sim`, and `pairwise_manhattan_sim` score aligned pairs instead of all pairs.
- Sparse inputs are supported by several helpers, but some paths may convert to dense or use SciPy; confirm memory behavior for large sparse matrices.

## Paraphrase mining and community detection

Use these utilities when the task asks for duplicate discovery, near-duplicate mining, or clustering-like grouping over dense embeddings.

- `paraphrase_mining(model, sentences, ...)` embeds sentences, compares them in chunks, and returns triplets `[score, id1, id2]` sorted by score.
- `paraphrase_mining_embeddings(embeddings, ...)` performs the same mining from precomputed embeddings.
- Key memory knobs are `query_chunk_size`, `corpus_chunk_size`, `max_pairs`, and `top_k`.
- `community_detection(embeddings, threshold=0.75, min_community_size=10, batch_size=1024)` returns lists of embedding indices, largest communities first; each community's first item is the central point.

## Hard-negative mining

`sentence_transformers.util.mine_hard_negatives(dataset, model, ...)` adds hard negatives to a `datasets.Dataset` of anchor/positive pairs.

Important arguments:

- `anchor_column_name` and `positive_column_name`: set them explicitly to avoid accidental first/second-column assumptions.
- `corpus`: optional candidate text pool; positives are still included and de-duplicated into the candidate corpus.
- `cross_encoder`: optional reranker used to rescore candidates after dense retrieval.
- `range_min` and `range_max`: select which retrieval ranks are eligible as negatives; increase `range_min` to avoid near-duplicates or hidden positives.
- `max_score` and `min_score`: filter by similarity score range.
- `absolute_margin` and `relative_margin`: require negatives to be sufficiently below the positive score; `relative_margin=0.05` is a common strong baseline.
- `num_negatives`: target negatives per anchor-positive pair.
- `sampling_strategy`: `"top"` for hardest valid candidates, `"random"` for more diversity among valid candidates.
- `include_positives=True`: useful for reranking datasets; it forces/prefers `output_format="n-tuple"` to preserve ranking order.
- `output_scores=True`: adds model or cross-encoder scores to the chosen output format.
- `use_faiss=True`: faster large-corpus retrieval when FAISS is installed; GPU FAISS can cap retrieval depth around 2048 per query.
- `use_multi_process`: use all available GPUs or explicit devices; verify process cleanup and memory.
- `cache_folder`: caches query/corpus embeddings by hash to avoid recomputation; use a project-controlled cache, not a public skill path.

Output formats when `output_scores=False`:

- `triplet`: columns like anchor, positive, negative.
- `n-tuple`: anchor, positive, `negative_1`, ..., `negative_n`.
- `labeled-pair`: anchor, document, binary label.
- `labeled-list`: anchor, list of documents, list of labels.

With `output_scores=True`, score columns replace or supplement labels depending on the format: triplet/n-tuple add a `scores` column, while labeled formats use `score` or `scores` instead of binary labels.

## Embedding quantization utilities

Embedding quantization reduces embedding storage/search cost; it is different from ONNX/OpenVINO model-weight quantization.

- `quantize_embeddings(embeddings, precision="float32" | "int8" | "uint8" | "binary" | "ubinary", ranges=None, calibration_embeddings=None)` returns NumPy arrays in the selected precision.
- `binary` and `ubinary` pack sign-thresholded dimensions into bytes; shape shrinks by a factor of 8 for common dense dimensions.
- `int8` and `uint8` scalar quantization preserve embedding dimensionality but need stable per-dimension ranges.
- For scalar quantization, prefer a large calibration set or explicit `ranges`; quantizing from only a handful of embeddings is unstable and emits warnings.
- `semantic_search_faiss(...)` and `semantic_search_usearch(...)` support quantized corpus search with optional rescoring when the query is float32 and corpus embeddings are quantized.
- For quantized search, pass exactly one of `corpus_embeddings` or a prebuilt `corpus_index`; passing both or neither raises `ValueError`.

## API migration cautions

- `information_retrieval` is deprecated; use `semantic_search`.
- `as_triplets` and `margin` in `mine_hard_negatives` are deprecated; use `output_format` and `absolute_margin`/`relative_margin`.
- Use `model.encode_query` and `model.encode_document` when available for retrieval models with prompts; otherwise preserve prompt settings consistently in encoding code.
