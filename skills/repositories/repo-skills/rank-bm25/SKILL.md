---
name: rank-bm25
description: "Guides tokenized lexical document retrieval with the rank_bm25
  Python package, including BM25Okapi, BM25L, BM25Plus, full-corpus scoring,
  top-n retrieval, batch scoring, and input troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# rank_bm25

Use this skill when a task asks for the `rank_bm25` package, Okapi BM25,
BM25L, BM25+, sparse lexical ranking, or a small in-memory search index over
pre-tokenized documents. It teaches the package API; it is not a production
search-service design and it does not cover the commented-out BM25Adpt/BM25T
classes.

## Route the task

- **Install or import**: install the public `rank_bm25` distribution, ensure
  NumPy is available, and run the import check below.
- **Build and rank an index**: read [workflows.md](references/workflows.md)
  for a complete tokenization, indexing, scoring, and top-n recipe.
- **Choose an algorithm or use advanced methods**: read
  [api-reference.md](references/api-reference.md) for verified signatures,
  defaults, return types, parameter meaning, and batch-score semantics.
- **Diagnose a failed ranking workflow**: read
  [troubleshooting.md](references/troubleshooting.md), then use the bundled
  [smoke_rank_bm25.py](scripts/smoke_rank_bm25.py) helper for a deterministic
  tiny-fixture check.
- **Check whether this knowledge matches a checkout**: read
  [repo-provenance.md](references/repo-provenance.md) before deciding whether
  the skill needs refreshing.

## Minimal setup and import check

```bash
python -m pip install rank_bm25
python -c "from rank_bm25 import BM25Okapi, BM25L, BM25Plus; print('rank_bm25 ready')"
```

The package has no console CLI and its runtime dependency is NumPy. CPU
execution is the supported baseline for the covered in-memory workflows.

## Core operating contract

1. Represent every document as a sequence of string tokens, for example
   `document.split()`; pass a list of those token sequences as `corpus`.
2. Apply the same lowercasing, normalization, stopword handling, and
   tokenization policy to documents and queries yourself. The package does no
   text preprocessing.
3. Choose `BM25Okapi`, `BM25L`, or `BM25Plus`, construct it once for a corpus,
   and reuse the index for compatible tokenized queries.
4. Use `get_scores(query)` for one score per indexed document,
   `get_top_n(query, documents, n=5)` when you need the original documents,
   or `get_batch_scores(query, doc_ids)` for a selected index subset.
5. Keep the original `documents` list in exactly the same order as the corpus;
   `get_top_n` checks the lengths and maps score indices back into that list.
6. Validate one known query and expected top document before scaling the corpus.
   Run `python scripts/smoke_rank_bm25.py` from this skill directory or any
   current working directory after installing the package.

The package is intentionally lightweight and in-memory. For full API details,
recipes, and predictable failure recovery, follow the linked references rather
than reopening the source repository.
