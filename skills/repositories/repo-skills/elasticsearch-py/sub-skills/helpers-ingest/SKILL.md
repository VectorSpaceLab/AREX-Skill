---
name: helpers-ingest
description: "Guide Elasticsearch Python bulk indexing, streaming, scanning,
  reindexing, parallel ingestion, async helpers, action validation, and
  partial-failure recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Helpers and ingestion

Use this route for bulk indexing, updates/deletes, streaming ingestion, scan,
reindex, parallel work, or helper-specific error handling. Start with a
configured `Elasticsearch` or `AsyncElasticsearch` from
[client-operations](../client-operations/SKILL.md).

## Choose a helper

- `helpers.bulk(client, actions)`: consume an iterable and return a count plus
  either an error list or (with `stats_only=True`) an error count.
- `helpers.streaming_bulk(...)`: stream `(ok, item)` results and control
  `chunk_size`, `max_chunk_bytes`, `flush_after_seconds`, retries, and whether
  successful items are yielded.
- `helpers.parallel_bulk(...)`: parallelize chunk submission when throughput
  justifies the extra concurrency and ordering is not required.
- `helpers.scan(client, query=...)`: scroll through matching documents; use
  `preserve_order=True` only when the ordering cost is intentional.
- `helpers.reindex(client, source_index, target_index, ...)`: use the helper for
  server-side reindex workflows and verify target mappings/settings separately.
- `async_bulk`, `async_streaming_bulk`, `async_scan`, and `async_reindex`: use
  with `AsyncElasticsearch` and `await`/`async for` as appropriate.

Read [api-reference.md](references/api-reference.md) for signatures and return
shapes, [workflows.md](references/workflows.md) for action/generator recipes,
and [troubleshooting.md](references/troubleshooting.md) for partial failures,
retries, and service errors. Run [bulk_actions_smoke.py](scripts/bulk_actions_smoke.py)
for an offline action-shape check; it never connects to a cluster.

## Action contract

An action is usually a mapping containing `_index`, optionally `_id`, and a
payload. `_op_type` defaults to `index`; use `create`, `update`, or `delete`
explicitly. Index/create actions use the document fields; update actions use
`doc`, `doc_as_upsert`, or a script; delete actions contain metadata only.
Generate actions lazily so large input sets do not occupy memory. Validate the
index name, operation, identifiers, and JSON-serializable payload before
sending.

## Safety and correctness

- Use bounded chunks and explicit retry policy. A retry on 429 can be useful;
  blindly retrying a non-idempotent write can duplicate effects.
- Handle `BulkIndexError` or inspect streamed item results instead of assuming a
  successful HTTP response means every item succeeded.
- Do not run scan/reindex or index deletion against a production cluster until
  the query, target, privileges, and dry-run/rollback plan are reviewed.
- Route query construction to [dsl-search](../dsl-search/SKILL.md) and ES|QL
  construction to [esql-query-builder](../esql-query-builder/SKILL.md).
