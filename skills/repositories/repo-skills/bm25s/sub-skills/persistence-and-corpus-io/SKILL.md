---
name: persistence-and-corpus-io
description: "Persist and reopen bm25s indexes and JSONL corpora safely,
  including custom filenames, mmap loading, JsonlCorpus access, vocabulary
  loading, and large-index memory planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Persistence and corpus I/O

Use this route when an index already exists or must be written for later
retrieval. It owns the low-level `BM25.save`, `BM25.load`, and
`BM25.load_scores` contracts, the optional saved corpus, and on-disk memory
behavior. It does not replace tokenization, scoring, high-level file ingestion,
Hub transfer, or evaluation workflows.

## Choose the loading mode

- **Normal local reload:** `BM25.load(index_dir, load_corpus=False)` loads the
  numeric arrays and BM25 parameters into memory. Add `load_corpus=True` only
  when result documents should be returned from the saved corpus.
- **Large index:** use `mmap=True` for the three CSC score arrays. If documents
  are also needed, `load_corpus=True, mmap=True` uses `JsonlCorpus` rather than
  reading the whole JSONL file into a list.
- **IDs-only retrieval:** leave `load_corpus=False`; retrieval returns document
  IDs. Keep the separately managed corpus in exactly the same index order if it
  will be applied later.
- **Scores-only inspection:** create a BM25 object and call `load_scores` with
  the saved array names and the known `num_docs`. This does not load parameters,
  vocabulary, or corpus metadata; use `load` for a usable retriever.

Read [file-format-and-api.md](references/file-format-and-api.md) for exact
signatures, filenames, serialization rules, and custom-name examples. Read
[large-corpus.md](references/large-corpus.md) before loading a large index or
batching retrieval. Use [troubleshooting.md](references/troubleshooting.md) for
failure diagnosis. Run the bounded local check in
[scripts/save_reload_smoke.py](scripts/save_reload_smoke.py) after changing a
persistence workflow.

## Safe save/reload recipe

1. Tokenize and index the documents with one stable vocabulary. The corpus used
   for result display is not the tokenized index: it is a positional document
   store, so keep its order and length aligned with the indexed documents.
2. Save the index directory. `save` creates parent directories and writes the
   three numeric CSC arrays, BM25 parameters, and BM25 vocabulary. Pass
   `corpus=...` (or set `BM25(corpus=...)`) to write a JSONL corpus as well.
3. If a `Tokenizer` will be reconstructed independently, save its tokenizer
   vocabulary under its default `vocab.tokenizer.json` or another distinct
   name. Do not overwrite the BM25 model's default `vocab.index.json`.
4. Reload using the same custom filenames used during save. For textual query
   tokenization, also restore the matching tokenizer vocabulary; for integer
   token IDs, ensure the IDs came from the saved BM25 vocabulary.
5. Verify one small query and, when `load_corpus=True`, verify that the returned
   document at each result ID is the expected positional entry.

```python
import bm25s

index = bm25s.BM25(method="bm25+")
index.index(bm25s.tokenize(["red fox", "blue whale"], stopwords=[]))
index.save(
    "local-index",
    corpus=[{"id": "r", "text": "red fox"}, {"id": "b", "text": "blue whale"}],
    data_name="scores.npy", indices_name="rows.npy", indptr_name="columns.npy",
    vocab_name="model-vocab.json", params_name="model-params.json",
    nnoc_name="nonoccurrence.npy", corpus_name="documents.jsonl",
)
reloaded = bm25s.BM25.load(
    "local-index", load_corpus=True, mmap=True,
    data_name="scores.npy", indices_name="rows.npy", indptr_name="columns.npy",
    vocab_name="model-vocab.json", params_name="model-params.json",
    nnoc_name="nonoccurrence.npy", corpus_name="documents.jsonl",
)
```

The `mmap` flag is a loading choice, not a save format. It maps `data`,
`indices`, and `indptr` with NumPy read mode; it does not make indexing or
serialization incremental. The BM25L/BM25+ non-occurrence array is loaded
separately and is required for those methods.

## Corpus and file invariants

- The default files are `data.csc.index.npy`, `indices.csc.index.npy`,
  `indptr.csc.index.npy`, `vocab.index.json`, `params.index.json`,
  `nonoccurrence_array.index.npy`, and `corpus.jsonl`.
- `params.index.json` is required to reconstruct the model. The three CSC
  arrays and the vocabulary are required for a normal usable load. Missing
  files should be repaired or the correct custom names supplied; do not create
  empty placeholders.
- `load_vocab=False` deliberately skips the BM25 vocabulary. In this version
  the resulting `vocab_dict` and `unique_token_ids_set` are empty, so the
  object is suitable for metadata/array inspection but not normal retrieval.
  Use `load_vocab=True` for retrieval, or explicitly restore a verified matching
  vocabulary before issuing queries.
- `load_corpus=True` is best effort: if the named corpus file is absent, load
  still returns the index with no loaded corpus. It does not validate that the
  corpus length or order equals the indexed document count.
- Strings are written as `{"id": <position>, "text": <string>}`. Top-level
  dictionaries, lists, and tuples are accepted and are written as JSON. Nested
  values must be JSON-serializable (null, booleans, numbers, strings, arrays,
  and objects); sets, bytes, arbitrary Python objects, and most NumPy objects
  are not portable JSON values.
- A document that cannot be serialized is warned about and skipped, which can
  make the saved corpus shorter than the index. Treat that warning as a data
  integrity failure, not as a harmless partial save. A non-iterable corpus is
  not a valid `save` input.
- A JSONL companion index is written beside the corpus. For `documents.jsonl`
  the companion is `documents.mmindex.json`; `JsonlCorpus` uses an existing
  companion without checking that it is fresh. Regenerate it after editing the
  JSONL file.

## Security and compatibility

Keep `allow_pickle=False` unless a trusted legacy index explicitly requires
object-array loading. Setting it to `True` permits NumPy pickle handling and
must never be used to load an untrusted index directory. Numeric arrays written
by the normal save path should work with the default `False` setting. The
stdlib JSON fallback and the optional `orjson` implementation both produce the
same documented JSON-shaped corpus contract; `orjson` is not a reason to enable
pickle.

Install the base package for NumPy-backed local persistence. The `core` extra
adds optional helpers such as `orjson`, progress reporting, stemming, and
Numba; it is not required for the save/load file contract. Keep optional
backends explicit and CPU-safe. Do not download a benchmark corpus merely to
validate a local index.

## Operational handoff

Report the index directory, exact filenames, whether `mmap` and
`load_corpus` were used, the model method, corpus count versus
`scores["num_docs"]`, vocabulary strategy, and any skipped-document warnings.
Close a loaded `JsonlCorpus` when a long-lived process no longer needs it. For a
missing BM25L/BM25+ non-occurrence file or a corpus/index order mismatch, stop
retrieval and repair the artifacts rather than silently returning plausible but
wrong scores or documents.
