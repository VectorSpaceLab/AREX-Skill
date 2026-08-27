# Troubleshooting

Use the symptom first, then apply the smallest recovery. The package is a
small NumPy implementation; most failures are input alignment or packaging
issues rather than backend issues.

## Installation and import

### `ModuleNotFoundError: No module named 'rank_bm25'`

Install the public distribution into the Python that will run the workflow:

```bash
python -m pip install rank_bm25
python -c "from rank_bm25 import BM25Okapi"
```

Using `pip` from a different interpreter is a common cause. Prefer
`python -m pip`, and check `python -c "import sys; print(sys.executable)"` when
multiple environments exist. NumPy is a runtime dependency and must import in
the same environment.

### Editable install fails with `fatal: No names found, cannot describe anything`

This package's source `setup.py` obtains its version from a numeric Git tag.
An untagged source snapshot cannot be packaged directly by that version helper.
Use an official PyPI release, a tagged source checkout, or a release artifact.
Do not silently invent a package version or modify the version helper as part of
a Researcher workflow. This issue is specific to source packaging; it does not
prevent normal installation from a published release.

### `ImportError` involving NumPy

Confirm the dependency and interpreter together:

```bash
python -m pip install numpy
python -c "import numpy; print(numpy.__version__)"
python -c "from rank_bm25 import BM25Okapi"
```

Do not add GPU frameworks: the covered package has no accelerator-specific
backend or optional runtime extra.

## Corpus and query data

### Scores are nonsensical or every score is zero

The package does not tokenize or normalize text. A raw string is a sequence of
characters, so `BM25Okapi(["windy London"])` is not equivalent to
`BM25Okapi([["windy", "London"]])`. Tokenize documents and queries explicitly,
and apply the same case, punctuation, stemming, and stopword policy to both.
Terms absent from the indexed corpus contribute zero by design.

### The expected document is not the top result

Check these in order:

1. The query uses the same token representation and preprocessing as the
   corpus.
2. The `documents` list supplied to `get_top_n` has the same length and order
   as the corpus used to construct the index.
3. The intended class and constructor parameters are used; Okapi, BM25L, and
   BM25Plus can produce different scores and rankings.
4. The query does not contain accidental repeated tokens or punctuation-only
   tokens.
5. Validate the expected behavior on a small labeled set rather than relying
   on one intuitive query.

### `get_top_n` raises `AssertionError: The documents given don't match the index corpus!`

`get_top_n` requires `len(documents) == index.corpus_size`. Keep an immutable
or otherwise synchronized raw-document list, or pass the exact filtered list
that was used to build the index. Rebuilding an index is safer than reusing an
index after inserting, deleting, or reordering documents.

### `get_batch_scores` raises an assertion or returns an unexpected mapping

Use integer document positions satisfying `0 <= doc_id < corpus_size`. The
returned Python list follows the order of `doc_ids`; it is not sorted. Pair
scores back with ids before sorting. Treat negative ids as invalid even though
the implementation's upper-bound assertion does not reject them consistently.

### Empty or degenerate corpus fails during construction/scoring

The index computes an average document length. An empty corpus has no valid
average, and a corpus of only empty documents can create zero-length
normalization problems. Reject empty input and require at least one meaningful
token before construction. If empty documents are legitimate, test the chosen
variant and query policy explicitly rather than assuming every formula remains
well-defined.

## Tokenizer and runtime behavior

### A supplied tokenizer fails in multiprocessing

The constructor maps `tokenizer` through a multiprocessing pool. Use a
module-level named function that can be pickled; avoid lambdas, nested
functions, and closures. The tokenizer must return a token sequence for every
input. If an interactive notebook or process-spawn platform still cannot
serialize it, tokenize the corpus in the caller and construct the index with
`tokenizer=None`.

The tokenizer path can also create worker overhead for a small corpus. Manual
pre-tokenization is simpler and more deterministic when indexing only a few
thousand short documents.

### Query or document tokens are unhashable

The implementation stores token frequencies in dictionaries, so each token must
be hashable. Convert structured token objects to strings or another stable
hashable representation before indexing and querying.

### A batch or full score is the wrong Python type

`get_scores` returns a NumPy array for the full corpus. `get_batch_scores` returns
a Python list. Normalize at the application boundary if JSON serialization or
a framework-specific array type is required; do not assume the two methods have
the same return type.

## Scope limits

There is no built-in persistence, incremental update, preprocessing pipeline,
CLI, distributed index, or production-scale serving layer. The repository's
BM25Adpt and BM25T names are commented out rather than implemented. Add those
capabilities around the package only with separate, validated code and do not
route them as `rank_bm25` APIs.
