# Core API reference

This reference describes the low-level public API observed in the `bm25s` package at the selected repository revision. It intentionally omits tokenizer, persistence, and accelerator implementation details owned by sibling routes.

## `BM25` constructor

```python
bm25s.BM25(
    k1=1.5, b=0.75, delta=0.5,
    method="lucene", idf_method=None,
    dtype="float32", int_dtype="int32",
    corpus=None, backend="numpy", csc_backend="numpy",
    auto_compile=True,
)
```

| Argument | Observed contract | Safe choice |
|---|---|---|
| `k1` | BM25 term-frequency saturation parameter | Keep `1.5` unless reproducing another setting |
| `b` | Document-length normalization parameter | Keep `0.75` unless reproducing another setting |
| `delta` | Additive variant parameter used by `bm25l` and `bm25+` | `0.5`; ignored by Robertson/Lucene/ATIRE |
| `method` | Term-frequency scorer: `robertson`, `lucene`, `atire`, `bm25l`, `bm25+` | `lucene` |
| `idf_method` | Independent IDF scorer with the same five names; `None` copies `method` | `None` |
| `dtype` | NumPy dtype for score and non-occurrence arrays | `float32` |
| `int_dtype` | NumPy dtype for stored index/query integer arrays | `int32` |
| `corpus` | Optional position-aligned display records retained on the retriever | only when alignment is controlled |
| `backend` | Retrieval computation backend: `numpy`, `numba`, or `auto` | `numpy` for required CPU path |
| `csc_backend` | Index CSC construction: `numpy`, `scipy`, or `auto` | `numpy`; `scipy` is optional |
| `auto_compile` | Warm/compile Numba functions when `backend="numba"` | leave `True` only for deliberate Numba use |

`backend="auto"` chooses Numba when importable and otherwise NumPy. `csc_backend="auto"` chooses SciPy when importable and otherwise NumPy. Selecting an unavailable explicit backend raises `ImportError` during construction. The core route does not require CUDA.

## `index`

```python
retriever.index(
    corpus,
    create_empty_token=True,
    show_progress=True,
    leave_progress=False,
)
```

Accepted corpus forms are inferred as follows:

| Form | Meaning | Query requirement |
|---|---|---|
| `list[list[str]]` | Already-tokenized string documents; `index` builds `vocab_dict` | use the same token strings or a matching tokenizer vocabulary |
| `list[list[int]]` | Numeric documents; `index` creates an external-ID-to-dense-column mapping | integer queries must use the supplied external IDs |
| `Tokenized(ids, vocab)` | IDs plus a vocabulary mapping; mapping values must be the dense IDs used in `ids` | use compatible IDs and vocabulary; do not silently rebuild it |
| `(ids, vocab_dict)` | The tuple form of the previous row (`ids` is per-document ID lists) | same as `Tokenized` |
| object with `.ids` and `.vocab` | Tokenized-like corpus object | same as `Tokenized` |

The tuple must be exactly two elements, with a list of per-document ID lists first and a dictionary second. A malformed tuple or non-iterable raises `ValueError`. The low-level `build_index_from_tokens` and `build_index_from_ids` methods are override points for specialized index construction; ordinary callers should use `index`.

`create_empty_token=True` adds an empty-token entry when appropriate so an empty document/query can be represented. For a bare integer corpus, the code reserves an integer sentinel (ID `0` if unused, otherwise `max(existing_id)+1`) before building. For string/tokenized inputs, an empty-string vocabulary entry is added when absent, but it is not a substitute for a separately managed query tokenizer. If no sentinel is present, an all-unknown integer batch can fail instead of becoming a valid empty query. Set `False` only when the application explicitly rejects or handles empty token sequences.

After indexing, useful observable state includes:

- `retriever.scores`: dictionary containing CSC `data`, `indices`, `indptr`, and `num_docs`.
- `retriever.vocab_dict`: mapping used for text-to-index query conversion (key type follows the input form).
- `retriever.unique_token_ids_set`: set used to filter integer query IDs.
- `retriever.nonoccurrence_array`: populated for `bm25l` and `bm25+`, otherwise `None`.

The sparse matrix is eager: document-token contributions are computed at index time and query-time scoring sums the relevant CSC columns.

## `retrieve`

```python
retriever.retrieve(
    query_tokens,
    corpus=None,
    k=10,
    sorted=True,
    return_as="tuple",
    show_progress=True,
    leave_progress=False,
    n_threads=0,
    chunksize=50,
    backend_selection="auto",
    weight_mask=None,
)
```

`query_tokens` is normally a batch of `list[list[str]]`, `list[list[int]]`, or `Tokenized`. A `Tokenized` query is decoded through its `vocab` and then matched against the retriever vocabulary; the safest path is to reuse the corpus tokenizer or pass strings. Integer batches are filtered to IDs present in `unique_token_ids_set` before scoring. The returned arrays have shape `(len(query_tokens), k)`.

| Argument | Behavior |
|---|---|
| `corpus` | If supplied, `documents` contains `corpus[result_id]`; otherwise it uses `self.corpus`, or numeric IDs if neither exists. A one-dimensional NumPy array is indexed directly; other iterables are flattened and reshaped. |
| `k` | Number of selected documents per query. `k > num_docs` is rejected; `k=0` yields empty columns; negative values fail in the selector. |
| `sorted` | `True` orders each row by descending score. `False` returns the selected top-k set in selector order, not a ranking. |
| `return_as` | `"tuple"` returns `Results(documents, scores)`; `"documents"` returns only the document array. Other strings raise `ValueError`. |
| `n_threads` | `0` maps queries sequentially; `-1` expands to `os.cpu_count()`; positive values use a `ThreadPoolExecutor` in the NumPy path. |
| `chunksize` | Chunk size passed to the threaded NumPy executor; ignored by the Numba retrieval implementation. |
| `backend_selection` | Top-k selector: `"auto"`, `"numpy"`, or `"jax"` in the NumPy retrieval path. `auto` prefers JAX when importable. |
| `weight_mask` | Must be a NumPy 1-D array of length `num_docs`; scores are multiplied elementwise before selection. |

When `query_tokens` contains an empty query list, retrieval bypasses vocabulary lookup and creates an all-zero score vector for that query. The selected IDs are therefore tie-dependent and should not be interpreted as relevance. A string query whose tokens are all absent also normally produces an all-zero vector. Direct `get_scores` has a stricter implementation assumption and should not be called with an empty list.

## `Results`

`Results` is a `NamedTuple` with two NumPy fields:

```python
Results(documents=np.ndarray, scores=np.ndarray)
```

`len(results)` is the number of query rows, not `k`. `Results.merge([r1, r2, ...])` concatenates the document and score arrays along axis 0 and is useful for merging query batches that used the same `k` and result contract.

## Direct score helpers

- `get_tokens_ids(query_tokens: list[str]) -> list[int]` maps known strings and silently drops unknown strings.
- `get_scores(query_tokens_single: list[str] | list[int], weight_mask=None)` computes a score vector over all indexed documents. It requires a nonempty list so it can inspect the first element; use `retrieve([[]], ...)` for an empty query.
- `get_scores_from_ids(query_tokens_ids, weight_mask=None)` is lower-level and does not filter unknown IDs. An ID at or above the CSC vocabulary range raises `ValueError`; keep IDs nonnegative and from the indexed vocabulary.
- `build_index_from_tokens(...)` returns `(scores, vocab_dict)` and `build_index_from_ids(...)` returns the CSC score dictionary. These are customization hooks, not a normal application entry point.

## Scoring variants

The implementation selects a term-frequency component (`tfc`) and an IDF component separately. Let `N` be document count, `df` document frequency, `l_d` document length, `l_avg` average length, and `c = tf/(1-b+b*l_d/l_avg)`.

| Name | IDF used by the implementation | TFC / behavior |
|---|---|---|
| `robertson` | `log(max(1, (N-df+0.5)/(df+0.5)))` | Original Robertson term frequency; negative IDF is clamped to zero |
| `lucene` | `log(1 + (N-df+0.5)/(df+0.5))` | Robertson term frequency; this is the default Lucene-style combination |
| `atire` | `log(N/df)` | `(tf*(k1+1))/(tf+k1*(1-b+b*l_d/l_avg))` |
| `bm25l` | `log((N+1)/(df+0.5))` | `((k1+1)*(c+delta))/(k1+c+delta)` plus non-occurrence correction |
| `bm25+` | `log((N+1)/df)` | `(k1+1)*tf/(k1*(1-b+b*l_d/l_avg)+tf) + delta` plus non-occurrence correction |

For BM25L/BM25+, `delta` and a per-vocabulary `nonoccurrence_array` account for the baseline contribution of absent terms. `idf_method` can be changed independently, for example `BM25(method="atire", idf_method="lucene")`; record both values when comparing results. The public README describes `robertson`, `atire`, `bm25l`, `bm25+`, and `lucene` as supported variants.

Invalid `method`/`idf_method` values are detected when the index builds and produce a `ValueError` from scorer selection. Validate the exact spelling, including the plus sign in `"bm25+"`.

## Dtypes and optional components

`dtype` controls score arrays and should normally remain `float32`. `int_dtype` controls stored document/token indices and should be wide enough for the index. `csc_backend="numpy"` avoids a SciPy dependency; `csc_backend="scipy"` requires SciPy. `backend="numba"` requires Numba. `backend_selection="jax"` requires a CPU-compatible JAX installation. These optional paths are explicitly covered by the acceleration sibling; the core acceptance path is NumPy on CPU.
