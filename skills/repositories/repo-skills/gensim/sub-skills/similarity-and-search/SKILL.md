---
name: similarity-and-search
description: "Guides Gensim similarity indexes, soft cosine, WMD, term
  similarity, and approximate-neighbor retrieval."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 2.1
---

# Similarity and Search

Use this sub-skill when the task needs to index transformed vectors or compare
corpus/query vectors with cosine, soft cosine, WMD, or term-similarity methods.

## Read when

- A user asks to build or query `MatrixSimilarity`, `SparseMatrixSimilarity`, or
  `Similarity`.
- The task needs approximate neighbors from `AnnoyIndexer` or `NmslibIndexer`.
- A workflow mentions `SoftCosineSimilarity`, `SparseTermSimilarityMatrix`,
  `WordEmbeddingSimilarityIndex`, or `LevenshteinSimilarityIndex`.
- A model was trained successfully but retrieval or ranking is the remaining
  problem.

## Quick workflow

1. Transform the corpus into the chosen vector space first.
2. Pick an index type that matches corpus size and memory limits.
3. Set `num_features` to the exact transformed vector dimension.
4. Save the index if it must be reused later.
5. Use `Similarity` for large corpora/shards; use `MatrixSimilarity` only when
   the full matrix comfortably fits in memory.

Read [`references/workflows.md`](references/workflows.md) for index-selection
recipes, [`references/api-reference.md`](references/api-reference.md) for verified
signatures, and [`references/optional-indexes-and-metrics.md`](references/optional-indexes-and-metrics.md)
for Annoy/NMSLIB/WMD/soft-cosine caveats.

## API anchors

- `MatrixSimilarity(corpus, num_best=None, dtype=numpy.float32, num_features=None, chunksize=256, corpus_len=None)`.
- `SparseMatrixSimilarity(corpus, num_features=None, num_terms=None, num_docs=None, num_nnz=None, num_best=None, chunksize=500, dtype=numpy.float32, maintain_sparsity=False, normalize_queries=True, normalize_documents=True)`.
- `Similarity(output_prefix, corpus, num_features, num_best=None, chunksize=256, shardsize=32768, norm='l2')`.
- `SoftCosineSimilarity(corpus, similarity_matrix, num_best=None, chunksize=256, normalized=None, normalize_queries=True, normalize_documents=True)`.
- `SparseTermSimilarityMatrix(source, dictionary=None, tfidf=None, symmetric=True, dominant=False, nonzero_limit=100, dtype=numpy.float32)`.
- `WordEmbeddingSimilarityIndex(keyedvectors, threshold=0.0, exponent=2.0, kwargs=None)`.
- `LevenshteinSimilarityIndex(dictionary, alpha=1.8, beta=5.0, max_distance=2)`.

## Bundled helper

Run [`scripts/similarity_query_smoke.py`](scripts/similarity_query_smoke.py) to
check that the environment can transform a tiny corpus and perform similarity
queries with both in-memory and sharded indexes.

## Boundaries and routing

- For corpus construction and BoW vectorization, route to
  [`../corpora-and-vector-spaces/SKILL.md`](../corpora-and-vector-spaces/SKILL.md).
- For topic models and transformations, route to
  [`../topic-modeling-and-transformations/SKILL.md`](../topic-modeling-and-transformations/SKILL.md).
- For embeddings and `KeyedVectors`, route to
  [`../embeddings-and-phrases/SKILL.md`](../embeddings-and-phrases/SKILL.md).
- For downloader and conversion CLIs, route to
  [`../data-and-cli-utilities/SKILL.md`](../data-and-cli-utilities/SKILL.md).

## Common decisions

- Use `MatrixSimilarity` for small corpora where simplicity matters.
- Use `SparseMatrixSimilarity` when the vectors are sparse and you want an in-memory sparse representation.
- Use `Similarity` when the index must be sharded or the corpus may exceed memory.
- Use `SoftCosineSimilarity` when semantically related terms should contribute to similarity.
- Use `WordEmbeddingSimilarityIndex` when you already have learned embeddings and want term similarity.
- Use `LevenshteinSimilarityIndex` for string-edit similarity over a fixed dictionary.
- Treat Annoy/NMSLIB as optional accelerators, not required base dependencies.

## Troubleshooting

Read [`references/troubleshooting.md`](references/troubleshooting.md) for vector
space mismatch, missing `num_features`, dense index memory pressure, output
prefix/shard files, empty queries, optional dependency failures, and WMD cost.
