---
name: async-client
description: "Use AsyncQdrantClient for awaitable Qdrant collection, point,
  query, payload, alias, snapshot, and lifecycle workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Async Client

Use this sub-skill when a task needs Qdrant's Python async client rather than the sync `QdrantClient`.

## Read First

- Use `AsyncQdrantClient` from `qdrant_client` when the caller already has an event loop, needs non-blocking Qdrant I/O, or is converting a sync recipe to async.
- Await collection, point, query, payload, alias, snapshot, and cluster methods. End remote and persistent-local workflows with `await client.close()`.
- Async local mode supports the same client entry point: `AsyncQdrantClient(":memory:")` for ephemeral tests and `AsyncQdrantClient(path="...")` for persisted local data.
- Remote async supports REST and gRPC modes through the same constructor options as the sync client, including `url`, `host`, `port`, `grpc_port`, `prefer_grpc`, `api_key`, `timeout`, `pool_size`, and headers.
- Keep sync-only examples in `../client-operations/`, local storage details in `../local-mode/`, transport/auth setup in `../connection-and-transport/`, and embedding/inference details in `../inference/`.

## Common Patterns

```python
import asyncio
from qdrant_client import AsyncQdrantClient, models

async def main() -> None:
    client = AsyncQdrantClient(":memory:")
    try:
        await client.create_collection(
            collection_name="items",
            vectors_config=models.VectorParams(size=3, distance=models.Distance.COSINE),
        )
        await client.upsert(
            collection_name="items",
            points=[models.PointStruct(id=1, vector=[0.1, 0.2, 0.3], payload={"kind": "demo"})],
        )
        result = await client.query_points(collection_name="items", query=[0.1, 0.2, 0.3], limit=1)
        print(result.points[0].id)
    finally:
        await client.close()

asyncio.run(main())
```

For deeper async API coverage, read:

- `references/async-client.md` for lifecycle, initialization parity, awaited operations, local/server differences, and generated parity caveats.
- `references/troubleshooting.md` for coroutine, close, transport, event-loop, snapshot, and alias diagnostics.
- `scripts/async_local_smoke.py` for a deterministic in-memory smoke check that future agents can copy or run.

## Acceptance Checks

- Every async Qdrant method call in examples is awaited unless the method is intentionally synchronous, such as `upload_points` or `upload_collection`.
- Client cleanup uses `await client.close()` in a `finally` block or equivalent shutdown hook.
- Local examples avoid credentials and server dependencies; remote examples make service and credential requirements explicit.
- Maintainer async-generation scripts are treated as implementation provenance only, not runtime tools for users of this skill.
