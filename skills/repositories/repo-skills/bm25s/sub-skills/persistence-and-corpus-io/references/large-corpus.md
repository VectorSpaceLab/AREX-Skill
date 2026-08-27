# Large-index and corpus planning

`mmap` reduces the cost of reopening a saved index; it does not turn BM25
index construction into an out-of-core algorithm. Plan indexing, saving, query
batches, and result storage separately.

## What is and is not memory-mapped

With `BM25.load(..., mmap=True)`:

- `data.csc.index.npy`, `indices.csc.index.npy`, and `indptr.csc.index.npy`
  are opened with NumPy `mmap_mode="r"`.
- The parameter JSON and vocabulary JSON are still read normally.
- The BM25L/BM25+ `nonoccurrence_array` is loaded normally in this revision;
  `mmap=True` does not map it.
- `load_corpus=True` selects `JsonlCorpus`, which memory-maps the JSONL file and
  fetches only requested lines. With `mmap=False`, the loader parses every
  corpus line into a Python list.
- Retrieval still allocates per-query score accumulators and result arrays.
  Mapping the index is not a promise that peak RSS equals the metadata size.
  Accessed pages may be cached by the operating system.

Use `mmap=True` when the saved numeric arrays are large relative to available
RAM or when multiple processes should share file-backed pages. Use normal
loading when repeated random access and maximum simplicity matter more than
startup memory. Do not attempt to write through the mapped arrays.

## Corpus sizing and alignment

The index's `scores["num_docs"]` is the authoritative indexed document count.
A saved corpus is only a positional presentation layer: result document ID
`i` is looked up as corpus entry `i`. It is not joined by the corpus's `id`
field. Before a document-returning run, check:

```python
expected = retriever.scores["num_docs"]
actual = len(retriever.corpus)  # list or JsonlCorpus
if actual != expected:
    raise ValueError(f"corpus/index mismatch: {actual} != {expected}")
```

A JSONL file can contain valid but reordered documents and still pass a length
check, so retain a manifest, stable IDs, or a separate checksum when identity
matters. Do not repair a mismatch by padding with placeholders; rebuild or
restore the exact corpus used for indexing.

The line-offset companion is an optimization, not a source of truth. It stores
one offset per JSONL line and is reused if present. Replacing, truncating, or
editing a corpus without replacing its `.mmindex.json` companion can produce
wrong lines or JSON decode errors. Delete the companion and let `JsonlCorpus`
rebuild it after any such change.

## Save and load costs

Indexing eagerly computes sparse BM25 scores and normally needs working memory
for token IDs, score construction, and the CSC arrays. Saving then writes the
arrays and scans the corpus once more to serialize JSONL and calculate line
offsets. `save` has no download step and no built-in shard or batch writer for
the index arrays.

For a large corpus:

1. Keep tokenized documents and the display corpus in separate representations
   when possible; avoid retaining duplicate full-text and token lists longer
   than needed.
2. Select numeric `dtype` and `int_dtype` deliberately before indexing. Changing
   dtypes at reload time is not a safe way to reduce an existing file.
3. Save to local durable storage, then test a small `mmap=True` load before
   deleting the in-memory builder.
4. Load without a corpus when only document IDs are needed. Load the JSONL
   lazily only for document-returning retrieval.
5. Keep `allow_pickle=False` and avoid object arrays. Pickle does not solve
   corpus-scale memory pressure and introduces an unsafe deserialization path.

## Query batching and reload

Large result matrices and per-query accumulators can dominate memory even when
the index is mapped. Process queries in bounded batches and persist only the
results needed by the application. A conservative pattern is:

```python
import bm25s

retriever = bm25s.BM25.load(
    "large-index", mmap=True, load_corpus=True,
    show_progress=False,
)
num_docs = retriever.scores["num_docs"]
all_batches = []
for start in range(0, len(query_ids), 20):
    all_batches.append(retriever.retrieve(query_ids[start : start + 20], k=10))
    # Refresh file-backed state between batches when peak memory is critical.
    retriever.load_scores("large-index", mmap=True, num_docs=num_docs)
    if isinstance(retriever.corpus, bm25s.utils.corpus.JsonlCorpus):
        retriever.corpus.load()
results = bm25s.Results.merge(all_batches)
```

The batch size is workload-dependent: lower it when result documents or score
arrays are large, and measure peak memory. `Results.merge` itself allocates the
combined result arrays, so streaming results to disk or a consumer may be
needed when all batches cannot fit in memory. Reloading scores does not reload
parameters or vocabulary and does not repair a corpus mismatch.

## Empty and very large JSONL files

A normal saved corpus has at least one line. An empty JSONL file cannot be
memory-mapped by the standard file reader on common Python platforms; use
`mmap=False`, supply a non-empty corpus, or keep an empty corpus outside the
`JsonlCorpus` path. A malformed line, truncated final line, or stale offset
companion is a data artifact problem, not a reason to enable pickle.

The public NQ examples demonstrate mmap and query batching with downloaded
benchmark data. They are reference patterns only: local persistence checks
should use a tiny fixture and must not download NQ, BEIR, or another large
corpus as part of a routine smoke test.
