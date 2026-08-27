# Search and Embeddings

## Search APIs

### `search_facts(...)`

```python
search_facts(
    entity_fact_driver=None,
    entity_id=None,
    query_embedding=None,
    limit=5,
    embeddings_limit=1000,
    *,
    query_text=None,
    candidates=None,
)
```

- Pass `candidates=` for offline candidate ranking without a database.
- Pass `entity_fact_driver`, `entity_id`, and `query_embedding` for DB-backed
  search.
- `query_text` improves hybrid ranking when it is available.

### Candidate model

- `FactCandidate(id, content, score, date_created, summaries=[])`
- `FactSearchResult(id, content, similarity, rank_score, date_created, summaries=[])`

## Embedding APIs

### `embed_texts(...)`

- Accepts a single string or a list of strings.
- Supports `async_=` for threadpool-backed async execution.
- Can use a TEI endpoint when `tei=` is supplied.
- Uses the native Rust embedding path when TEI is not supplied.

### `TEI(...)`

- `TEI(url, timeout=30, headers=None)` is the public helper used for hosted
  text-embedding-inference endpoints.

## Practical usage pattern

Use candidate-mode search when you already have pre-ranked results or when you
want to validate the reranking logic without setting up a database or model
download. Use DB-backed search when you have a storage backend and want the
full recall path.
