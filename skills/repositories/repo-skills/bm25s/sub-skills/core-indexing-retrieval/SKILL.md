---
name: core-indexing-retrieval
description: "Build a BM25S sparse index and retrieve ranked document IDs,
  scores, or position-aligned application records with the low-level BM25 API."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---
# Core indexing and retrieval

Use this route when the downstream task needs direct control of `bm25s.BM25`: construct an eager sparse BM25 index, score tokenized queries, select top-k results, or map result positions back to metadata. This route owns the low-level index/retrieval contract and the scoring variants. Route text splitting, stopwords, stemming, and tokenizer-vocabulary persistence to `tokenization-and-stopwords`; route index save/load, mmap, and JSONL corpus files to `persistence-and-corpus-io`. Optional Numba retrieval and JAX top-k selection are acceleration choices, not prerequisites for the CPU workflow.

## Minimal safe recipe

```python
import bm25s

texts = ["red cat likes purr", "blue dog likes play", "fish swim in water"]
corpus_tokens = bm25s.tokenize(texts, stopwords=None, show_progress=False)
retriever = bm25s.BM25()  # k1=1.5, b=0.75, delta=0.5, method="lucene"
retriever.index(corpus_tokens, show_progress=False)
query_tokens = bm25s.tokenize(["cat purr"], stopwords=None, show_progress=False)
result = retriever.retrieve(query_tokens, k=2, show_progress=False)
print(result.documents.shape, result.scores.shape)  # (1, 2), (1, 2)
```

`result` is a `bm25s.Results` named tuple with `.documents` and `.scores`. Without a display corpus, documents are integer positions. For a ready-to-run metadata fixture, use [scripts/metadata_retrieval.py](scripts/metadata_retrieval.py).

## Choose the index input

- **Token strings:** pass `list[list[str]]` when you already have a stable token representation. `index` builds a vocabulary from these tokens.
- **Token IDs:** pass `list[list[int]]` for a numeric corpus. The index creates a mapping from the supplied external IDs to dense internal columns; retrieve integer queries from that same ID space.
- **Vocabulary-carrying IDs:** pass a `bm25s.tokenization.Tokenized` object, a `(ids, vocab_dict)` pair, or an object exposing `.ids` and `.vocab`. The first member is the per-document ID lists and the mapping must be the corpus/query vocabulary.
- **Empty documents:** keep `create_empty_token=True` unless the application deliberately handles documents or queries with no surviving tokens. With numeric corpora the sentinel is incorporated before scoring; without a usable sentinel, an all-unknown integer query raises.

Do not tokenize corpus and query independently into integer IDs and assume the IDs match. Either pass string tokens to both retrieval calls or reuse the tokenizer state/vocabulary described by the sibling route.

## Retrieval contract

`retrieve` accepts batches (`list[list[str]]`, `list[list[int]]`, or `Tokenized`) and returns two-dimensional arrays of shape `(number_of_queries, k)`. Use `return_as="tuple"` (default) for `Results`, or `return_as="documents"` for only the document array. `corpus=` is display data, not the indexed text: position `i` must describe indexed document `i`; if omitted, the retriever's `BM25(corpus=...)` value is used. See [references/api-reference.md](references/api-reference.md) for exact signatures, shapes, and parameter semantics.

Start with `k <= number_of_indexed_documents`, a nonnegative integer, and `sorted=True`. `n_threads=0` is the deterministic simple CPU path; `n_threads=-1` uses all reported CPUs, and positive values use a thread pool. `chunksize` matters only to the threaded NumPy path. `backend_selection="auto"` may use JAX when available; select `"numpy"` for the explicit minimal dependency path.

A `weight_mask` must be a one-dimensional NumPy array with exactly one value per indexed document. It multiplies document scores by position; zeroed documents can still appear when ties or insufficient positive candidates make that unavoidable. It is not a replacement for a filter that guarantees exclusion.

## Output and reproducibility

- Keep `sorted=True` when a ranked list is part of the user-facing contract; use `sorted=False` only when order does not matter.
- Treat document IDs as row positions, not stable external IDs, unless `corpus` supplies those external records.
- Record the model method, IDF method, `k1`, `b`, `delta`, dtypes, and selected backends with benchmark results.
- For smoke checks, use a tiny local fixture, `show_progress=False`, and the explicit NumPy/CPU choices.
- Compare scores as well as IDs when validating a variant or a changed vocabulary.

## Scoring decisions

The constructor defaults to Lucene-style BM25. `method` selects the term-frequency variant: `"robertson"`, `"lucene"`, `"atire"`, `"bm25l"`, or `"bm25+"`. `idf_method=None` follows `method`, and can be set independently to one of those supported scoring methods. `delta` affects BM25L/BM25+; it is ignored by the first three variants. Keep `k1` and `b` explicit when reproducing a benchmark. Invalid methods fail during index construction, so validate them before expensive indexing. Formula and variant details are in [references/api-reference.md](references/api-reference.md).

## Index state and low-level hooks

Indexing is eager: the model computes document-token contributions into CSC arrays. Confirm `retriever.scores["num_docs"]` after `index` and keep `retriever.vocab_dict` with the query producer. `get_tokens_ids` and `get_scores` are useful for a one-query diagnostic; `get_scores_from_ids` is an unchecked lower-level primitive. `build_index_from_tokens` and `build_index_from_ids` are extension hooks for specialized pipelines, not substitutes for a normal `index` call. Do not mutate `scores`, `vocab_dict`, or `unique_token_ids_set` between indexing and retrieval unless rebuilding the complete compatible state.

## Boundary cases to handle explicitly

- `retrieve([[]], k=...)` is supported and returns top-k zero scores; ties are not meaningful rankings. Prefer this over calling the lower-level `get_scores([])` directly.
- Unknown string tokens are omitted from a query and can produce all-zero scores. Unknown integer IDs are filtered by `retrieve`; if all are unknown and no empty-token sentinel is available, it raises a `ValueError`.
- `get_scores_from_ids` is lower-level and does not filter; a too-large ID raises a `ValueError` about the index vocabulary. Use nonnegative IDs from the same vocabulary.
- An invalid `return_as` raises a `ValueError`; a negative `k` reaches top-k validation and fails, while `k=0` produces empty result columns. `k > num_docs` is rejected early.
- The current retrieval implementation does not validate a supplied display corpus length. Validate `len(corpus) == retriever.scores["num_docs"]` yourself; a short corpus can raise `IndexError`, and a long or reordered corpus can silently return misleading records.
- A mask must be an actual `numpy.ndarray`, one-dimensional, and length `num_docs`; wrong type, rank, or length raises a `ValueError`.

See [references/troubleshooting.md](references/troubleshooting.md) for install/import, optional-backend, data alignment, method, and workflow failures. Use [references/workflows.md](references/workflows.md) for metadata, numeric-ID, variant comparison, masking, and arbitrary-cwd recipes.

## Handoff checklist

At minimum, a downstream handoff should include the query count, result shape, and whether returned documents are IDs or application records. This makes an empty result row and a positional metadata mismatch distinguishable.

1. Record the token representation and the exact corpus/query vocabulary strategy.
2. Record `num_docs`, `k`, `return_as`, sorting, and whether display metadata is attached or supplied at retrieval.
3. Validate display corpus alignment and masks before calling `retrieve`.
4. Keep the required backend CPU/NumPy unless an optional accelerator was deliberately selected and checked.
5. If an index must be written or reopened, hand off to `persistence-and-corpus-io` rather than reproducing its file contract here.
