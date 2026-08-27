# Optional Indexes and Metrics

## Annoy and NMSLIB

Annoy and NMSLIB are optional approximate-nearest-neighbor helpers. They are not
installed with the base Gensim runtime.

Use them when:

- exact search is too slow or too memory-heavy,
- approximation is acceptable,
- the optional dependency installs cleanly for the target Python/platform, and
- the task explicitly values query speed over exact ranking.

Fallbacks:

- Use `MatrixSimilarity` for small dense indexes.
- Use `SparseMatrixSimilarity` for sparse in-memory indexes.
- Use `Similarity` for sharded exact indexes.

## Word Mover's Distance

WMD uses optimal transport and requires the optional POT package (`import ot`).
It can be slow for long documents or large query batches. For missing POT or
runtime concerns, consider cosine similarity over TF-IDF/LSI vectors or soft
cosine with a term-similarity matrix.

## Soft cosine

Soft cosine needs a term similarity matrix. A common workflow is:

1. Train or load word embeddings.
2. Build `WordEmbeddingSimilarityIndex(keyedvectors)`.
3. Build `SparseTermSimilarityMatrix(index, dictionary, tfidf=...)`.
4. Query with `SoftCosineSimilarity`.

Validate vocabulary overlap before blaming the index. If the embedding model has
poor coverage of dictionary terms, term similarities will be sparse or unhelpful.

## Levenshtein/FastSS term matching

String-edit similarity can help typo-tolerant term matching over a fixed
vocabulary. It is not a semantic model. Use it for spelling variants, OCR noise,
or short query normalization, not for topic similarity.
