# API Reference

Read this when selecting an algorithm, checking parameter defaults, or using
subset scoring. The signatures below were confirmed from the installed package
and the implementation in `rank_bm25.py`.

## Public classes

All concrete classes inherit the same base operations:

```python
BM25(corpus, tokenizer=None)
BM25.get_scores(query)
BM25.get_batch_scores(query, doc_ids)
BM25.get_top_n(query, documents, n=5)
```

`BM25` itself is an abstract base: its `_calc_idf`, `get_scores`, and
`get_batch_scores` methods raise `NotImplementedError`. Use a concrete class.

| Class | Constructor | Intended use |
|---|---|---|
| `BM25Okapi` | `BM25Okapi(corpus, tokenizer=None, k1=1.5, b=0.75, epsilon=0.25)` | ATIRE/Okapi-style BM25 with an epsilon floor for negative IDF terms |
| `BM25L` | `BM25L(corpus, tokenizer=None, k1=1.5, b=0.75, delta=0.5)` | BM25L scoring with a delta correction for document-length effects |
| `BM25Plus` | `BM25Plus(corpus, tokenizer=None, k1=1.5, b=0.75, delta=1)` | BM25+ scoring with a delta contribution for each query term |

`k1` controls term-frequency saturation and `b` controls document-length
normalization. The `epsilon` and `delta` meanings are algorithm-specific; keep
the defaults until a benchmark or domain validation justifies tuning. These
classes differ in IDF and term-frequency formulas, so score magnitudes are not
interchangeable across variants; compare rankings within a chosen variant.

## Corpus and tokenizer contract

- `corpus` must be an iterable of documents where each document is a sequence
  of hashable token values, normally strings. The documented and tested form is
  `list[list[str]]`.
- With `tokenizer=None`, the constructor immediately indexes the supplied
  token sequences. Passing raw strings here makes each string behave like a
  sequence of characters; split or otherwise tokenize first.
- With a callable `tokenizer`, the constructor applies it to every corpus
  element through a multiprocessing pool. This allows raw strings, but the
  callable must be picklable and should be defined at module scope. In a
  notebook or interactive session, pre-tokenize first if a local function or
  lambda cannot be serialized.
- The index records `corpus_size`, `avgdl`, per-document token lengths, term
  frequencies, and IDF values. The corpus is kept as index statistics rather
  than returned documents; retain the original documents separately for
  `get_top_n`.
- An empty corpus cannot produce a valid average document length. Supply at
  least one non-empty document and validate data before constructing the index.

## Scoring and retrieval methods

### `get_scores(query) -> numpy.ndarray`

`query` must be a token sequence, not a raw query string. The result has one
floating-point score per corpus position and preserves corpus order. Terms not
seen while indexing contribute zero through the package's missing-term lookup.
Use `numpy.argsort(scores)[::-1]` or `get_top_n` to rank positions. Repeated
query tokens are processed repeatedly, so deduplicate them only if that is the
intended retrieval policy.

### `get_top_n(query, documents, n=5) -> list`

This calls `get_scores`, sorts descending, and returns the original items at the
highest-scoring indices. `len(documents)` must equal the indexed corpus size or
an assertion fails. Keep document and tokenized-corpus order identical. `n=0`
returns an empty list; a value larger than the corpus is naturally truncated by
array slicing.

### `get_batch_scores(query, doc_ids) -> list[float]`

This scores only the selected corpus positions and returns a Python list in the
same order as `doc_ids`, unlike `get_scores`, which returns a NumPy array for the
whole corpus. Use integer ids in the safe range `0 <= id < corpus_size` and
preserve the ids-to-documents mapping yourself. The implementation asserts the
upper bound; do not rely on negative Python indexing even though negative ids
are not rejected by that assertion.

## Practical selection guidance

- Start with `BM25Okapi` when reproducing the README or when no variant has
  been validated for the domain.
- Evaluate `BM25L` or `BM25Plus` as separate alternatives on the same
  preprocessed corpus/query fixtures; do not mix their score thresholds.
- Tune `k1`, `b`, `epsilon`, or `delta` only with an evaluation set. They are
  constructor arguments, not per-query settings.
- The package provides ranking math only. Tokenization, stemming, stopword
  removal, persistence, incremental updates, filtering, and large-scale index
  serving must be implemented around it.

## Source-backed non-goals

The repository contains commented sketches for `BM25Adpt` and `BM25T`, but no
usable public implementations. Do not import, instantiate, or promise them.
