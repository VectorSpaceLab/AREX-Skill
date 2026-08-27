# API Reference

## Public names

| Name | What it does |
|---|---|
| `Similarity` | Model-backed pair similarity with cosine or WMD scoring. |
| `SimilarityType` | Enum for `COSINE` and `WMD`. |
| `EmbeddingType` | Enum for `BERT` and `WORD2VEC`. |
| `get_score` | Score one text pair. |
| `get_scores` | Score two sentence lists and return a matrix. |
| `similarity` | Alias of `get_scores`. |
| `cos_sim` | Cosine similarity utility for tensors or NumPy inputs. |
| `semantic_search` | Dense top-k retrieval over query and corpus embeddings. |
| `BM25` | Raw-text BM25 retrieval with Jieba segmentation. |

## Similarity

### Constructor

```python
Similarity(
    model_name_or_path="shibing624/text2vec-base-chinese",
    similarity_type=SimilarityType.COSINE,
    embedding_type=EmbeddingType.BERT,
    encoder_type=EncoderType.MEAN,
    max_seq_length=256,
)
```

### Behavior

- `SimilarityType.COSINE` is the common sentence-similarity path.
- `SimilarityType.WMD` only makes sense with `EmbeddingType.WORD2VEC`.
- `EmbeddingType.BERT` uses `SentenceModel` under the hood.
- `EmbeddingType.WORD2VEC` uses the word-vector model and cosine or WMD logic.
- Empty or blank input returns `0.0` from `get_score`.
- The default model name is a downloadable public model; use a local or cached model path when you want to avoid network access.

### `get_score(sentence1, sentence2) -> float`

- Returns one similarity score for one pair.
- For BERT cosine, each sentence is encoded once and then compared with cosine similarity.
- For Word2Vec cosine, it compares the sentence embeddings with cosine distance/similarity semantics.
- For WMD, it tokenizes with Jieba and converts distance to `1 / (1 + distance)`.

### `get_scores(sentences1, sentences2, only_aligned=False) -> numpy.ndarray`

- Returns a matrix with shape `(len(sentences1), len(sentences2))`.
- For BERT, the full cross-product matrix is always computed.
- For Word2Vec, `only_aligned=True` fills only the diagonal positions but still returns a matrix.
- If the sentence list lengths do not match and `only_aligned=True`, the method falls back to the full matrix.
- `similarity(...)` is the same call as `get_scores(...)`.

### Matrix-vs-aligned rule

- Use `get_score` when you need one row to map to one pair.
- Use `get_scores` when you intentionally want a similarity matrix.
- Do not assume `only_aligned=True` avoids a full matrix for BERT; it does not.

## `cos_sim`

```python
cos_sim(a, b)
```

- Accepts torch tensors, NumPy arrays, or simple numeric lists.
- Promotes 1-D vectors to shape `(1, dim)`.
- Normalizes each row before the dot product.
- Returns a torch tensor with shape `(len(a), len(b))`.
- Inspection confirmed the basic shape/value pattern:
  - `[[1.0, 0.7071], [0.0, 0.7071]]` for a tiny orthogonal/diagonal example.

## `semantic_search`

```python
semantic_search(
    query_embeddings,
    corpus_embeddings,
    query_chunk_size=100,
    corpus_chunk_size=500000,
    top_k=10,
    score_function=cos_sim,
)
```

- Takes query embeddings and corpus embeddings as tensors or NumPy arrays.
- Returns a list with one result list per query.
- Each result item is a dictionary with keys:
  - `corpus_id`: index into the corpus embeddings
  - `score`: cosine score
- Results are sorted by decreasing score and trimmed to `top_k`.
- If `top_k` is larger than the corpus, the function effectively returns the available corpus items.

## BM25

### High-level wrapper

```python
BM25(corpus)
```

- Accepts one string or a list of raw corpus strings.
- Segments each corpus string with Jieba before building the index.
- `get_scores(query, top_k=None)` tokenizes the query with Jieba and returns a list of `(corpus_text, score)` tuples.
- `top_k=None` returns the full ranking.
- Empty corpora raise a `ValueError`.

### Low-level tokenized scorer

If you already have token lists, use `text2vec.utils.rank_bm25.BM25Okapi` directly.

- Input is a tokenized corpus, not raw strings.
- `get_scores(tokenized_query)` returns one score per corpus item.
- `get_top_n(tokenized_query, documents, n=5)` returns the top-ranked documents.

## Score interpretation

| API | Score range | Notes |
|---|---|---|
| `Similarity(...).get_score(...)` with cosine | `[-1, 1]` | Higher means more similar. |
| `cos_sim` | `[-1, 1]` | Normalized cosine. |
| `semantic_search` | `[-1, 1]` | Same cosine semantics as `cos_sim`. |
| BM25 | Unbounded, usually non-negative | Compare within one corpus/query setup, not across unrelated corpora. |

## Practical guidance

- Use cosine-based APIs for semantic similarity.
- Use BM25 when lexical matching is enough or when you need a no-network fallback.
- Use dense search when you already have embeddings or a cached model.
- When you need aligned pair scores from a file, keep one pair per row and score row by row rather than building a matrix first.