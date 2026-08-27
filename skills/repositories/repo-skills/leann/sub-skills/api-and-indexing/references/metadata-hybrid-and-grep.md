# Metadata filters, hybrid BM25/vector, and grep

## Metadata model

Each result has top-level `id`, `score`, and `text` plus a passage `metadata`
dictionary. Filters first look for a top-level result field and then for an
immediate key in metadata.

```python
results = searcher.search(
    "release notes",
    top_k=20,
    metadata_filters={
        "year": {">=": 2024, "<=": 2025},
        "status": {"in": ["published", "reviewed"]},
    },
)
```

Different fields are ANDed. Multiple operators on one field are also ANDed.
Filtering occurs **after** vector/BM25 retrieval, result enrichment, and hybrid
fusion, so `top_k=20` means “filter these at most 20 candidates,” not “return 20
matching records.” Increase candidate retrieval when selectivity is high, then
measure latency and recall.

### Operators

| Operator | Behavior |
| --- | --- |
| `==`, `!=` | Python equality or inequality. |
| `<`, `<=`, `>`, `>=` | If both values are strings, lexical comparison; otherwise numeric conversion is attempted, then string comparison is the fallback. |
| `in`, `not_in` | Requires the expected value to be a list, tuple, or set and tests whether the **entire field value** is a member. |
| `contains` | Case-sensitive substring test after converting both values to strings. |
| `starts_with`, `ends_with` | Case-sensitive string test after conversion to strings. |
| `is_true`, `is_false` | Tests `bool(field_value)`; the supplied expected value is ignored. |

Important limitations:

- A missing field fails the filter.
- An unsupported operator logs a warning and fails the filter; it does not
  raise to the caller.
- Nested metadata traversal is unsupported. A filter key such as
  `"attrs.tier"` does not reach `metadata["attrs"]["tier"]`. Flatten values at
  ingestion, for example `"attrs_tier": "gold"`.
- `{"tags": {"in": ["ml", "rag"]}}` does **not** test overlap when `tags` is a
  list; it asks whether that complete list is an element of the expected list.
  Store a scalar category, flatten booleans such as `tag_ml=True`, or post-filter
  application-side for list intersection.
- Metadata types should be consistent. String dates compare lexically only
  when both sides are strings, so use sortable ISO 8601 form or numeric epochs.
- `use_grep=True` returns before metadata filtering, so combine grep and filters
  in application code if both are required.

Filters can also target top-level fields:

```python
metadata_filters={"text": {"contains": "LEANN"}, "score": {">": 0.2}}
```

Because scores are retrieval-path-specific, score filters are fragile across
backend or mode changes.

## Pure BM25 keyword search

```python
with LeannSearcher(
    str(base_path),
    enable_warmup=False,
    recompute_embeddings=False,
    use_daemon=False,
) as searcher:
    results = searcher.search("SQLite passage", top_k=10, vector_weight=0.0)
```

BM25 uses a persisted SQLite FTS5 table. Query punctuation is stripped, terms
are lowercased, and terms are joined with `OR`. A query containing no word
characters returns no results. SQLite FTS5 reports lower scores as better;
LEANN negates them so its result path ranks larger scores first.

An ordinary `build_index` records and prebuilds the FTS5 database in 0.3.8
because the active backend is always `fts5`. The precomputed array/pickle build
methods do not prebuild it. On first BM25 request, a missing or unrecorded
artifact is rebuilt from passage JSONL in the index directory. That directory
must be writable. An empty/malformed passage corpus can leave BM25 unavailable.

## Hybrid vector plus BM25

```python
results = searcher.search(
    "SQLite passage",
    top_k=10,
    vector_weight=0.6,
    metadata_filters={"kind": {"==": "manual"}},
)
```

Mode selection is exact:

| `vector_weight` | Path |
| --- | --- |
| `1.0` | Pure vector search (default). |
| `0.0` | Pure BM25; no query embedding. |
| `0.0 < value < 1.0` | Vector search plus BM25 linear fusion. |

Use values only in `[0, 1]`; version 0.3.8 does not validate the range. The
fusion computes:

```text
fused[id] = vector_weight * vector_score
          + (1 - vector_weight) * bm25_score
```

Each side contributes at most its own `top_k` candidates. Scores are not
normalized before addition, so the numeric scale of a backend can dominate the
nominal weight. Tune the weight on representative labeled queries rather than
assuming `0.5` is balanced. Metadata filters run after fusion.

If an ID appears on only one side, it receives only that side's weighted score.
The fused candidates are sorted descending and truncated to `top_k`.

## Grep retrieval

Grep is a separate early-return path for case-insensitive regular-expression
matching over raw JSONL lines:

```python
with LeannSearcher(
    str(base_path),
    enable_warmup=False,
    recompute_embeddings=False,
    use_daemon=False,
) as searcher:
    results = searcher.search("FileNotFoundError", top_k=5, use_grep=True)
```

Verified 0.3.8 behavior:

1. It looks only for a file named `documents.leann.passages.jsonl` in the
   metadata directory or its parent. A custom Python base name can therefore
   build a valid index that grep cannot locate. For a grep-capable custom build,
   use the base name `documents.leann` inside its dedicated directory.
2. It runs system `grep -i -n QUERY FILE`. `grep` must be installed.
3. The query is a grep regular expression, not a fixed literal. Avoid untrusted
   patterns, leading-dash queries, and expressions with pathological behavior.
4. A match can occur anywhere in the serialized JSON line, including metadata.
5. Matching lines are parsed as JSON. Malformed rows are silently skipped.
6. Score is the case-insensitive literal occurrence count in the passage
   `text`, even though selection used regex over the whole JSON row. A
   metadata-only match can therefore have score `0`.
7. Results are sorted by descending occurrence count and truncated to `top_k`.
8. Grep bypasses vectors, BM25, metadata filters, daemon startup, and query
   logging.

No matches is a normal empty list. A missing expected JSONL raises
`FileNotFoundError`; a missing `grep` executable becomes `RuntimeError`.

## Choosing a mode

| Need | Use | Watch for |
| --- | --- | --- |
| Semantic paraphrases | `vector_weight=1.0` | Query model compatibility and recomputation cost. |
| Exact keywords without a query model | `vector_weight=0.0` | FTS5 artifact/writability and OR-term semantics. |
| Both semantic and lexical recall | `0 < vector_weight < 1` | Unnormalized score scales and small candidate pools. |
| Regex-like raw occurrence search | `use_grep=True` | Hard-coded JSONL name, system grep, and ignored metadata filters. |
| Strict field restriction | `metadata_filters=...` | Post-search selectivity and flat metadata only. |
