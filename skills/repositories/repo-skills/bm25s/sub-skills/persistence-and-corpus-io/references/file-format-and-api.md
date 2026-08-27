# Index file format and API contract

This reference describes the local format emitted and consumed by the public
`bm25s.BM25` persistence methods. An index directory is a group of files, not
a single portable archive. Keep all files from one save together and pass the
same custom names to `load`.

## Default layout

| Role | Default filename | Format | Notes |
| --- | --- | --- | --- |
| CSC nonzero values | `data.csc.index.npy` | NumPy `.npy` | Score values, normally numeric. |
| CSC row indices | `indices.csc.index.npy` | NumPy `.npy` | Document indices. |
| CSC column pointers | `indptr.csc.index.npy` | NumPy `.npy` | Vocabulary-column boundaries. |
| BM25 vocabulary | `vocab.index.json` | One JSON object | Token-to-integer mapping used by the model. |
| Model parameters | `params.index.json` | Indented JSON object | Method, `k1`, `b`, `delta`, dtypes, count, version, and backends. |
| BM25L/BM25+ correction | `nonoccurrence_array.index.npy` | NumPy `.npy` | Written only for methods that require it. |
| Optional corpus | `corpus.jsonl` | One JSON value per line | Positional result documents. |
| JSONL line index | `corpus.mmindex.json` | JSON array of offsets | Created beside a saved corpus for mmap access. |

The BM25 vocabulary filename is intentionally different from the tokenizer
vocabulary filename (`vocab.tokenizer.json`). If both are stored in one
folder, keep both names; overwriting `vocab.index.json` with tokenizer state
makes BM25 loading fail or reconstruct the wrong mapping.

## `BM25.save`

The relevant call shape is:

```python
retriever.save(
    save_dir,
    corpus=None,
    data_name="data.csc.index.npy",
    indices_name="indices.csc.index.npy",
    indptr_name="indptr.csc.index.npy",
    vocab_name="vocab.index.json",
    params_name="params.index.json",
    nnoc_name="nonoccurrence_array.index.npy",
    corpus_name="corpus.jsonl",
    allow_pickle=False,
    show_progress=True,
    leave_progress=False,
)
```

`save_dir` is created if necessary. The arrays and metadata are always
written. The optional corpus is selected as `corpus` when supplied, otherwise
from `retriever.corpus`; if both are `None`, no corpus JSONL is written.
`show_progress` and `leave_progress` affect the full scan used to build the
JSONL line-offset companion.

Corpus serialization is deliberately narrow:

- A string at position `i` becomes `{"id": i, "text": <string>}`.
- A dictionary, list, or tuple is passed to the JSON encoder unchanged (a tuple
  is represented as a JSON array).
- Every nested value must be representable in JSON. Use plain Python values,
  not bytes, sets, file handles, custom classes, or NumPy scalars/arrays.
- A document that raises during JSON encoding is logged and omitted. Verify the
  number of lines after saving; omission changes positional alignment.
- A corpus must be iterable. Do not pass a generator that can be consumed
  before this call, or a non-iterable scalar. If a generator is used, it is
  consumed while writing and cannot be reused to validate its count unless it
  is recreated.

`allow_pickle` is forwarded to `numpy.save`. It should remain `False` for
normal numeric index arrays. It is a compatibility/security switch, not a
way to serialize arbitrary corpus documents; corpus data always goes through
JSON.

## `BM25.load`

The relevant call shape is:

```python
retriever = bm25s.BM25.load(
    save_dir,
    data_name="data.csc.index.npy",
    indices_name="indices.csc.index.npy",
    indptr_name="indptr.csc.index.npy",
    vocab_name="vocab.index.json",
    params_name="params.index.json",
    nnoc_name="nonoccurrence_array.index.npy",
    corpus_name="corpus.jsonl",
    load_corpus=False,
    mmap=False,
    allow_pickle=False,
    load_vocab=True,
    override_params=None,
    show_progress=True,
    leave_progress=False,
)
```

The loader reads parameters first, constructs a BM25 object, then loads score
arrays. `override_params` is merged into the saved parameter dictionary, and
additional keyword arguments are also treated as constructor-parameter
overrides. Use this only for deliberate, compatible changes; changing method,
dtypes, or corpus assumptions can invalidate the saved arrays.

Behavior that callers should make explicit:

- `mmap=True` is validated as a Boolean and maps the three CSC arrays with
  NumPy mode `"r"`. The mapped arrays are read-only from the caller's point of
  view. It does not map the non-occurrence array in this implementation.
- `load_vocab=True` reads the BM25 vocabulary. `load_vocab=False` skips the
  file and sets `vocab_dict` to `{}` and `unique_token_ids_set` to an empty set
  in the loaded object. Treat this as array/metadata inspection mode; normal
  retrieval needs the saved BM25 vocabulary and matching query preprocessing.
- `load_corpus=False` leaves the corpus unset. With `load_corpus=True`, a
  present corpus is loaded as a list when `mmap=False`, or as
  `bm25s.utils.corpus.JsonlCorpus` when `mmap=True`.
- A missing named corpus does not itself raise when `load_corpus=True`; the
  loaded object simply has no corpus. Missing parameters, arrays, vocabulary
  (when requested), malformed JSON, or malformed NumPy files do raise and must
  be fixed rather than hidden.
- For `method="bm25l"` or `method="bm25+"`, the named non-occurrence array is
  mandatory and a missing file raises `FileNotFoundError`.
- `scores["num_docs"]` comes from the saved parameter JSON. Compare it with the
  number of corpus lines before returning documents.

## `BM25.load_scores`

`load_scores` is an instance method for loading only the three CSC arrays:

```python
holder = bm25s.BM25()
holder.load_scores(
    "local-index",
    data_name="data.csc.index.npy",
    indices_name="indices.csc.index.npy",
    indptr_name="indptr.csc.index.npy",
    num_docs=2,
    mmap=True,
    allow_pickle=False,
)
```

It assigns `holder.scores` with `data`, `indices`, `indptr`, and the supplied
`num_docs`. It does not read `params.index.json`, the vocabulary, the
non-occurrence array, or the corpus. Always supply `num_docs` when using it for
retrieval or memory-bounded reloads; the default `None` is useful only for raw
array inspection.

## JSONL companion and `JsonlCorpus`

The saved corpus receives an offset array whose name is derived by replacing
the final extension with `.mmindex.json`. `documents.jsonl` therefore uses
`documents.mmindex.json`. `bm25s.utils.corpus.JsonlCorpus` loads the companion
when it exists; otherwise it scans the JSONL file and, by default, writes one.
Use `save_index=False` to keep the offsets in memory for a temporary reader.

```python
from bm25s.utils.corpus import JsonlCorpus

corpus = JsonlCorpus("documents.jsonl", show_progress=False)
try:
    first = corpus[0]
    batch = corpus[[0, 2]]
    matrix = corpus[numpy.array([[0, 1], [1, 0]])]
finally:
    corpus.close()
```

Integer, slice, list, tuple, and NumPy-array indexing are supported. NumPy
array indexing preserves the input shape. `close()` releases the file and
memory map; `load()` reopens them. The reader assumes the offset file matches
the current JSONL bytes, so delete/regenerate a stale companion after editing
or replacing the corpus.
