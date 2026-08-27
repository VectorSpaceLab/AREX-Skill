# High-level API reference

This reference describes the public convenience layer in the `bm25s` package.
It is deliberately separate from the lower-level `bm25s.BM25` API.

## Imports and signatures

```python
import bm25s.high_level as bm25

bm25.load(path, document_column=None)
bm25.index(documents, language="english")
bm25.BM25Search(
    corpus,
    language="english",
    bm25_kwargs=None,
    tokenizer_kwargs=None,
    tokenizer_cls=Tokenizer,
)
BM25Search.search(queries, k=10, n_jobs=1)
```

`load` returns the selected document values. `index` returns a
`BM25Search`; it does not return the lower-level `BM25` instance. The wrapper
keeps these useful attributes:

- `searcher.corpus`: the original list passed to the wrapper;
- `searcher.retriever`: the underlying `bm25s.BM25` instance;
- `searcher.tokenizer`: the stateful tokenizer used for corpus and query text.

For direct persistence, the CLI calls `searcher.retriever.save(...)` and saves
`searcher.tokenizer` vocabulary/stopwords separately. A `BM25Search` has no
high-level `save` or `load` method of its own.

## `BM25Search` defaults

The constructor only supports `language="english"` in this revision. Its
built-in tokenizer settings are equivalent to:

```python
{
    "stemmer": Stemmer.Stemmer("english"),
    "stopwords": "english",
    "lower": True,
}
```

Its built-in BM25 settings are equivalent to:

```python
{
    "backend": "numba",
    "csc_backend": "numpy",
    "auto_compile": False,
}
```

The wrapper then compiles the retriever with Numba activated and `warmup=False`
before indexing. This makes PyStemmer and Numba required for the default
high-level route, even though the base package itself has a NumPy-only install
path. If the optional packages are intentionally absent, use the lower-level
route with explicit compatible settings rather than assuming this wrapper will
fallback.

Overrides are merged into those defaults:

```python
searcher = bm25.BM25Search(
    documents,
    bm25_kwargs={"method": "bm25+"},
    tokenizer_kwargs={"stopwords": [], "lower": False},
)
```

`bm25_kwargs` and `tokenizer_kwargs` must be dictionaries or `None`. The
`corpus` key is reserved by the wrapper and raises `ValueError` if supplied in
`bm25_kwargs`. A non-English `language` raises `NotImplementedError`.

## `load` format matrix

| Suffix | Accepted shape | Selection when `document_column` is omitted | Failure behavior |
|---|---|---|---|
| `.txt` | UTF-8 text, one document per line | Every nonblank line | File errors propagate |
| `.csv` | Headered CSV read by `csv.DictReader` | First header field | Missing selected column raises `ValueError` |
| `.json` | List of strings or list of dictionaries | Strings are used directly; dictionaries use first key of first item | Non-list top level raises `ValueError`; absent dict key raises `KeyError` |
| `.jsonl` | One JSON object per nonblank line | First key in first record | Missing key in any record raises `ValueError` |

The suffix check is literal and lowercase. `DOCS.TXT` is not accepted as
`.txt`. `document_column` means a CSV column for CSV input and a dictionary key
for JSON/JSONL input; it has no effect on TXT.

### Text files

Lines are stripped with `line.strip()` and empty results are dropped. A file
containing only blank lines therefore loads as an empty list. Encoding is
UTF-8. Newline normalization is handled by Python's text reader.

### CSV files

`csv.DictReader` treats the first row as headers. The default is the first
header in file order, not the column with a conventional name such as `text`.
Explicitly pass `document_column="text"` whenever a metadata column precedes
the text column. The selected values are strings as parsed by the CSV reader.
A headerless/empty CSV has no field names; this revision returns an empty
`BM25Search` object from that branch instead of a list. Treat that as an
implementation quirk and validate the fixture before indexing.

### JSON and JSONL files

A JSON list of strings is the simplest portable format:

```json
["red fox", "blue whale"]
```

For records, pass a key explicitly:

```json
[{"id": "r1", "text": "red fox"}, {"id": "b1", "text": "blue whale"}]
```

Without a key, the first key of the first dictionary is selected. This is
order-dependent and may choose metadata such as `id` or `title`; do not rely on
key order when the intended field is known. JSONL applies the inferred or
explicit key to every nonblank record. A malformed JSON line propagates the
standard JSON decoding exception. A JSONL record missing the selected key is a
hard `ValueError`, not a skipped document.

The loader does not coerce numbers, nested objects, or nulls to strings. Use a
preprocessing step if document text is not already a string.

## `search` outputs and edge behavior

The return shape is a Python list with one entry for each query:

```python
[
    [
        {"id": 0, "score": 0.42, "document": "a matching document"},
        {"id": 1, "score": 0.00, "document": "another document"},
    ],
    [],
]
```

`id` is converted to a Python `int`; `score` is converted to a Python
`float`; `document` is the original positional value. Results are sorted by
score through the underlying retriever. Since `k` is first clamped to
`len(corpus)`, `k=10` on a three-document corpus returns at most three hits.
`k=0` returns `[[]]` for a one-query batch. Negative `k` reaches an invalid
array shape and raises a `ValueError`; reject it in caller-facing code.

The wrapper tokenizes every query with `update_vocab=False`. Empty-token
queries are explicitly filtered and return an empty hit list. A batch such as
`["known term", "   "]` therefore returns one normal list and one empty list
without losing query order. Unknown terms can also produce an empty list.
Pass a list of strings: a bare string is iterable and is treated as a sequence
of individual query strings rather than one query.

`n_jobs` is passed through to retrieval as `n_threads`; choose a positive value
for predictable parallel behavior. The wrapper enables progress display during
construction and search and does not expose a high-level progress flag.

## Minimal contract check

```python
from pathlib import Path
import tempfile
import bm25s.high_level as bm25

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "docs.txt"
    path.write_text("red fox\nblue whale\n", encoding="utf-8")
    docs = bm25.load(path)
    hits = bm25.index(docs).search(["fox", ""], k=5)
    assert hits[0][0]["document"] == "red fox"
    assert hits[1] == []
```

Use a local fixture for this check. Do not download a corpus to validate the
high-level API.
