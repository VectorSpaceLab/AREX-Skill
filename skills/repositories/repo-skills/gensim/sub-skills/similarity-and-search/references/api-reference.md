# Similarity API Reference

## Exact indexes

### MatrixSimilarity

`MatrixSimilarity(corpus, num_best=None, dtype=numpy.float32, num_features=None,
chunksize=256, corpus_len=None)` stores a dense matrix in memory. Use it only
when the entire indexed corpus fits comfortably in RAM.

### SparseMatrixSimilarity

`SparseMatrixSimilarity(corpus, num_features=None, num_terms=None, num_docs=None,
num_nnz=None, num_best=None, chunksize=500, dtype=numpy.float32,
maintain_sparsity=False, normalize_queries=True, normalize_documents=True)` stores
sparse vectors in memory. It can be better for high-dimensional sparse BoW/TF-IDF
vectors.

### Similarity

`Similarity(output_prefix, corpus, num_features, num_best=None, chunksize=256,
shardsize=32768, norm='l2')` creates a sharded index on disk. It supports dynamic
querying and adding documents. Use a dedicated output prefix in a temporary or
explicit artifact directory, and keep generated shard files together.

## Soft cosine and term similarity

`SoftCosineSimilarity(corpus, similarity_matrix, num_best=None, chunksize=256,
normalized=None, normalize_queries=True, normalize_documents=True)` compares
vectors while allowing related terms to contribute.

`SparseTermSimilarityMatrix(source, dictionary=None, tfidf=None, symmetric=True,
dominant=False, nonzero_limit=100, dtype=numpy.float32)` builds a sparse term
similarity matrix from a term similarity source.

`WordEmbeddingSimilarityIndex(keyedvectors, threshold=0.0, exponent=2.0,
kwargs=None)` uses word embeddings as the source of term similarity.

`LevenshteinSimilarityIndex(dictionary, alpha=1.8, beta=5.0, max_distance=2)`
uses edit distance over dictionary terms.

## Optional approximate neighbors

- `AnnoyIndexer` requires optional `annoy`.
- `NmslibIndexer` requires optional `nmslib` and may have Python/platform wheel
  constraints.

When optional dependencies are missing, exact Gensim indexes remain available.
Do not fail the whole workflow unless the user specifically requires the optional
indexer.

## Query result shape

Similarity indexes usually return a vector of scores, or the top `num_best`
`(doc_id, score)` pairs when `num_best` is set. Sort descending for ranking:

```python
sims = index[query_vector]
ranked = sorted(enumerate(sims), key=lambda pair: -pair[1])
```

Keep a document-id/title mapping outside the index if results must be mapped back
to original documents.
