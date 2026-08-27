# Helper API reference

The synchronous helpers consume an `Elasticsearch` client; the `async_`
variants consume `AsyncElasticsearch` and are awaited or iterated with
`async for`.

## Bulk functions

```python
helpers.bulk(
    client,
    actions,
    stats_only=False,
    ignore_status=(),
    **kwargs,
) -> tuple[int, int | list[dict]]

helpers.streaming_bulk(
    client,
    actions,
    chunk_size=500,
    max_chunk_bytes=100 * 1024 * 1024,
    flush_after_seconds=None,
    raise_on_error=True,
    raise_on_exception=True,
    max_retries=0,
    initial_backoff=2,
    max_backoff=600,
    yield_ok=True,
    ignore_status=(),
    retry_on_status=(429,),
    **kwargs,
) -> Iterable[tuple[bool, dict]]
```

`bulk()` summarizes the stream. With `stats_only=False` it returns successful
count and a list of errors; with `stats_only=True` it returns successful and
failed counts. `streaming_bulk()` yields each item unless `yield_ok=False`.
The default is to raise `BulkIndexError` after collecting errors in the last
chunk and to retry nothing; opt into bounded retries intentionally.

`parallel_bulk()` has the streaming bulk controls plus worker/thread and queue
settings. Use it only when the service and application can tolerate concurrency
and unordered completion.

## Action normalization

`helpers.expand_action(action)` returns the bulk action header and optional body.
It accepts raw bytes/strings or a mapping. `_op_type` defaults to `index`;
`update` uses `doc`/`_source`, `delete` has no body, and metadata keys such as
`_id`, `_index`, `pipeline`, routing, version, and retry-on-conflict are moved
to the action header.

## Scan and reindex

`scan(client, query=None, scroll="5m", raise_on_error=True,
preserve_order=False, clear_scroll=True, **kwargs)` returns an iterator of hits.
It is a scrolling abstraction, and `preserve_order=True` can remove the
performance benefit of unordered scanning.

`reindex(client, source_index, target_index, query=None, target_client=None,
chunk_size=500, scroll="5m", **kwargs)` performs repeated scan/bulk work. Verify
source/target mappings and permissions before using it on a live cluster.
