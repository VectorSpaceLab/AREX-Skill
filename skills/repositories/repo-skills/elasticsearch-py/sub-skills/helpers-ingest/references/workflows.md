# Ingestion workflows

## Generator-based bulk indexing

Keep the input lazy and put the target index in each action:

```python
def actions(rows):
    for row in rows:
        yield {
            "_index": "books",
            "_id": row["id"],
            "_source": {"title": row["title"], "year": row["year"]},
        }

successes, errors = helpers.bulk(client, actions(source_rows), stats_only=False)
```

For mixed actions, make the operation explicit:

```python
{
    "_op_type": "update",
    "_index": "books",
    "_id": "42",
    "doc": {"rating": 5},
}
{
    "_op_type": "delete",
    "_index": "books",
    "_id": "old-id",
}
```

Use `streaming_bulk()` when the caller needs per-item outcomes or wants to
write failed actions to a retry file:

```python
for ok, item in helpers.streaming_bulk(
    client, actions(source_rows), chunk_size=250,
    max_retries=3, retry_on_status=(429,), raise_on_error=False,
):
    if not ok:
        record_failure(item)
```

A successful HTTP bulk response is not proof that every item succeeded. Preserve
`item` details and redact sensitive document fields before logging.

## Async ingestion

```python
async for ok, item in helpers.async_streaming_bulk(async_client, async_actions()):
    ...
```

`async_bulk`/`async_streaming_bulk` are the async equivalents. Keep the action
producer async when data arrives asynchronously, and close the async client in
an async context manager. Do not pass `AsyncElasticsearch` to `helpers.bulk`.

## Scan and reindex checklist

1. Confirm source query, target index, mappings, aliases, and privileges.
2. Bound `scroll`, `chunk_size`, `max_chunk_bytes`, and retries.
3. Decide whether document order matters. Default unordered `scan` is faster;
   `preserve_order=True` can be expensive.
4. Run a small sample or isolated target first.
5. Capture item errors and verify source/target counts and mappings after the
   operation.
6. Treat the operation as potentially destructive when aliases or overwrite
   flags are involved; do not copy a cleanup helper into production code.
