# Helpers troubleshooting

| Symptom | Cause | Recovery |
|---|---|---|
| `BulkIndexError` | One or more items in a completed chunk returned an error | Inspect `.errors`, fix the offending action/mapping/privilege, and retry only idempotent or deduplicated actions. |
| Bulk call raises before item results | Transport/API exception or `raise_on_exception=True` | Verify the cluster/client first; use `raise_on_exception=False` only when the application can record all failed items. |
| Many 429 responses | Cluster backpressure or chunks/concurrency too large | Reduce `chunk_size`, workers, or `max_chunk_bytes`; use bounded `max_retries` and backoff; monitor cluster health. |
| All actions in a chunk fail | Wrong index, auth, mapping, serialization, or unreachable service | Inspect the first item and HTTP exception; validate one representative action before restarting the stream. |
| Unexpected document fields | Action has no `_source` or payload metadata is mixed with document fields | Use `_source` explicitly for index/create; use `doc` for update; run the bundled offline action check. |
| `ScanError`/scroll failure | Source query, scroll context, or service failure | Check source index/query/privileges and cluster health; reduce scroll size and rerun from a known checkpoint. |
| Memory grows during ingestion | Input list is materialized, chunks are too large, or failure records accumulate | Use a generator, bound chunk bytes, stream failures to durable storage, and avoid `list()` around the helper. |
| Async helper cannot be awaited | Used a synchronous helper or iterated incorrectly | Use the matching `async_` helper, `await async_bulk(...)`, or `async for` over async streaming/scan. |
| `TypeError` in action callback | Callback does not return `(header, body)` or input shape is not mapping/bytes | Test `expand_action` on a tiny fixture and preserve the callback contract. |
| Retry duplicates writes | Operation is not idempotent | Include stable IDs or application idempotency keys, and retry only documented transient statuses. |

Do not use `ignore_status` to hide a data or privilege problem. Treat a status
as ignorable only when it is an explicit, reviewed part of the workflow.
