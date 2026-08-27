# Core indexing and retrieval troubleshooting

## Install and import

- The minimal BM25 path needs the `bm25s` package and NumPy. Install the package in the environment that will run the retriever, then verify with `python -c 'import bm25s; print(bm25s.BM25)'`.
- A source checkout that has no release tag can report a fallback distribution version such as `0.0.0`; do not infer API compatibility from that fallback version. Record the commit or package build used by the application separately.
- If `import bm25s` fails, check that the interpreter and `pip` target the same environment and that a shadowing file named `bm25s.py` is not ahead of the package on `sys.path`.
- Core indexing does not require SciPy, Numba, JAX, PyStemmer, Rich, or MCP. Keep optional packages opt-in and CPU-compatible.
- The inspected MCP server import requires `mcp.server.fastmcp`; the compatible dependency finding for this revision is `mcp<2`. Do not claim that the newest `mcp` release is always compatible. MCP is not needed for `BM25.index` or `BM25.retrieve`.

## Optional dependency failures

| Symptom | Cause and repair |
|---|---|
| `ImportError` selecting `backend="numba"` | Install the package's Numba extra, or use `backend="numpy"`. Do not make Numba a hidden core requirement. |
| `ImportError` selecting `csc_backend="scipy"` | Install SciPy, or use the default NumPy CSC builder. |
| `ImportError` selecting `backend_selection="jax"` | Install a CPU JAX build and verify it in the target environment, or select `backend_selection="numpy"`. No CUDA setup is required for the core route. |
| PyStemmer import failure in a copied example | Stemming belongs to tokenization; use no stemmer or install the explicit PyStemmer extra. |
| MCP server import failure | Keep the MCP extra separate and pin `mcp<2` for this source revision; core BM25 retrieval remains usable without it. |

`backend="auto"` and `csc_backend="auto"` are convenience choices. For reproducible CPU checks, explicitly choose `backend="numpy"`, `csc_backend="numpy"`, and `backend_selection="numpy"`.

## Data and configuration failures

### Corpus and metadata alignment

The model indexes by position. If the tokenized corpus has `N` documents, every display corpus supplied to `BM25(corpus=...)` or `retrieve(corpus=...)` must have exactly `N` entries in exactly the same order. This revision does not proactively compare lengths:

- a short display corpus can raise `IndexError` only when a missing position is selected;
- a longer display corpus is accepted but extra entries are never indexed;
- a reordered corpus returns valid-looking records for the wrong documents.

Validate before retrieval:

```python
expected = retriever.scores["num_docs"]
if len(display_corpus) != expected:
    raise ValueError(f"display corpus has {len(display_corpus)} entries; expected {expected}")
```

An attached `BM25(corpus=...)` value is not used to build the index and does not repair a mismatch.

### Token and vocabulary mismatch

- Text queries use `vocab_dict` lookup; unknown strings are dropped and can result in all-zero scores. Use the same tokenizer vocabulary for corpus and queries rather than independently generated IDs.
- Integer query batches are filtered by `retrieve` to `unique_token_ids_set`. If filtering removes every ID and the model has no usable empty-token sentinel, `ValueError` explains that no query token is in the vocabulary.
- `get_scores_from_ids` is not the filtering API. A too-large integer ID raises a `ValueError` naming the maximum token ID; never pass arbitrary external IDs directly to it.
- A `Tokenized`/tuple vocabulary mapping must use dense IDs in the per-document ID lists. For a bare integer corpus, preserve the model's `vocab_dict` mapping from external key to dense internal column.
- If a query is unexpectedly empty, inspect stopword/stemmer settings in the tokenization route before changing BM25 parameters.

### Empty input

Use `retrieve([[]], k=...)` for an intentional empty query. It returns zero scores and top-k tie-dependent IDs. An all-unknown string query has similar zero-score behavior. Direct `get_scores([])` is not a safe equivalent because this implementation inspects the first element of the list. Avoid an empty corpus in production: average document length and the sparse index have no useful ranking semantics there.

## API and CLI failures

- `k > retriever.scores["num_docs"]` raises a `ValueError` with the available document count. Use `0 <= k <= num_docs`; `k=0` is allowed but returns empty columns, while negative values fail in the top-k selector.
- `return_as` accepts only `"tuple"` and `"documents"`. The tuple is a `Results` object, not an ordinary two-element list, but it can be unpacked as `documents, scores = result`.
- `weight_mask` must be a NumPy array, rank 1, and length `num_docs`. A Python list, two-dimensional array, or wrong-length array raises `ValueError`. A zero mask changes scores to zero; it is not a guaranteed exclusion filter.
- `backend_selection` is about top-k selection (`auto`, `numpy`, `jax`); `backend` is the retrieval computation backend (`numpy`, `numba`, `auto`). Do not pass `jax` as `backend` or `numba` as `backend_selection`.
- `method` spelling is exact: `robertson`, `lucene`, `atire`, `bm25l`, or `bm25+`. `idf_method` has the same supported names and defaults to `method`. Invalid values may not fail until `index` calls the scorer selector.
- The `bm25` command-line interface is a separate file-ingestion/search route. It still needs an index directory and its own optional CLI extra; do not use it to diagnose a direct Python vocabulary mismatch.

## Workflow-specific failures

### Scores look all zero

Check for an empty query, all unknown strings, a stopword configuration that removed every term, or a mask of zeros. Run one known-token query with `weight_mask=None`, `sorted=True`, and the NumPy path. Compare both `result.documents` and `result.scores`, not just the record display.

### Correct scores but wrong records

The score index is position-based. Check the display corpus order and length, whether a filtered/removed source document changed positions, and whether a saved/reloaded JSONL corpus was truncated by a non-serializable record. Repair the data alignment; do not compensate by changing `k`.

### Variant scores differ unexpectedly

Confirm the exact `method`, `idf_method`, `k1`, `b`, `delta`, and `dtype` on every model. BM25L and BM25+ use non-occurrence corrections, and Robertson clamps negative IDF, so equal document IDs do not imply equal score scales.

### Parallel retrieval behaves differently

First reproduce with `n_threads=0`, `backend="numpy"`, and `backend_selection="numpy"`. Then increase `n_threads` deliberately. `chunksize` is a batching knob, not a scoring parameter, and does not apply to the Numba retrieval implementation.

### Index construction fails after a configuration edit

Run a tiny two- or three-document fixture with `show_progress=False` and the exact constructor values. Invalid scorer names, unavailable explicit optional backends, malformed tuple/object corpora, and non-dense Tokenized IDs are configuration/data errors. Fix those before trying a larger corpus.
