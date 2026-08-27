# AsyncQdrantClient Reference

## When to Use It

Use `AsyncQdrantClient` when Qdrant calls run inside an async application, worker, API handler, notebook cell, or test suite. The async client exposes the same high-level operations as `QdrantClient`, but most operations return coroutines and must be awaited.

```python
from qdrant_client import AsyncQdrantClient

client = AsyncQdrantClient(":memory:")
```

Use the sync client instead when the surrounding code is synchronous and there is no event loop to integrate with.

## Initialization Parity

`AsyncQdrantClient` accepts the same main location choices as the sync client:

- `AsyncQdrantClient(":memory:")` creates an in-memory local Qdrant instance for deterministic async tests and examples.
- `AsyncQdrantClient(path="qdrant-data")` uses local persistent storage. Close it after use so file locks and collection resources are released.
- `AsyncQdrantClient(url="http://localhost:6333")` connects to a Qdrant server over REST by default.
- `AsyncQdrantClient(host="localhost", port=6333)` is equivalent to setting a local server host and REST port.
- `AsyncQdrantClient(url="https://cluster.example", api_key="...", prefer_grpc=True)` can use authenticated remote access and prefer gRPC where supported.

Only one of `location`, `url`, `host`, or `path` may be set. Cloud inference is rejected for local mode; use FastEmbed/local inference or switch to a cloud/server client for cloud inference.

## Lifecycle

Create the client inside the event-loop lifetime that will use it, then close it explicitly.

```python
from qdrant_client import AsyncQdrantClient

async def use_qdrant() -> None:
    client = AsyncQdrantClient(url="http://localhost:6333", timeout=10)
    try:
        collections = await client.get_collections()
        print([collection.name for collection in collections.collections])
    finally:
        await client.close()
```

Close matters for both backends:

- Remote clients close async HTTP resources and any gRPC channel pool.
- Persistent local clients close local collections and release the storage lock.
- After close, create a new client instead of reusing the old one.

## Awaited Operation Flow

Most high-level operations are awaited directly:

```python
from qdrant_client import models

await client.create_collection(
    collection_name="items",
    vectors_config=models.VectorParams(size=3, distance=models.Distance.COSINE),
)

await client.upsert(
    collection_name="items",
    points=[
        models.PointStruct(id=1, vector=[0.1, 0.2, 0.3], payload={"tag": "a"}),
        models.PointStruct(id=2, vector=[0.2, 0.1, 0.0], payload={"tag": "b"}),
    ],
)

count = await client.count(collection_name="items")
records = await client.retrieve(collection_name="items", ids=[1, 2])
query = await client.query_points(collection_name="items", query=[0.1, 0.2, 0.3], limit=2)
```

Common awaited categories:

- Collection lifecycle: `collection_exists`, `create_collection`, `update_collection`, `delete_collection`, `get_collection`, `get_collections`.
- Point writes: `upsert`, `delete`, `update_vectors`, `delete_vectors`, `batch_update_points`.
- Point reads: `query_points`, `query_batch_points`, `query_points_groups`, `retrieve`, `scroll`, `count`, `facet`.
- Payload and indexes: `set_payload`, `overwrite_payload`, `delete_payload`, `clear_payload`, `create_payload_index`, `delete_payload_index`.
- Aliases: `update_collection_aliases`, `get_aliases`, `get_collection_aliases`.
- Snapshots and cluster operations on server deployments: snapshot, shard, and cluster methods are also coroutines.

`upload_points` and `upload_collection` are intentionally synchronous helper methods on `AsyncQdrantClient`. They perform their own batching and return `None`; do not `await` those two helpers.

## Converting a Sync Recipe

Convert sync code mechanically, then review lifecycle and helper exceptions:

1. Change `QdrantClient` to `AsyncQdrantClient`.
2. Wrap the workflow in `async def` and call it from the application's event loop or with `asyncio.run()` at a script entry point.
3. Add `await` before collection, point, query, payload, alias, snapshot, and close calls.
4. Leave `upload_points` and `upload_collection` un-awaited, or replace them with awaited `upsert`/`batch_update_points` if the surrounding workflow needs strict async call sites.
5. Put `await client.close()` in `finally` or application shutdown code.

### Async Batch Query and Payload Update Example

```python
from qdrant_client import AsyncQdrantClient, models

async def update_and_query() -> list[int | str]:
    client = AsyncQdrantClient(":memory:")
    try:
        await client.create_collection(
            collection_name="recipes",
            vectors_config=models.VectorParams(size=3, distance=models.Distance.COSINE),
        )
        await client.upsert(
            collection_name="recipes",
            points=[
                models.PointStruct(id=1, vector=[0.9, 0.1, 0.0], payload={"meal": "breakfast"}),
                models.PointStruct(id=2, vector=[0.0, 0.9, 0.1], payload={"meal": "dinner"}),
            ],
        )
        await client.set_payload(
            collection_name="recipes",
            payload={"reviewed": True},
            points=[1, 2],
        )
        responses = await client.query_batch_points(
            collection_name="recipes",
            requests=[
                models.QueryRequest(query=[1.0, 0.0, 0.0], limit=1),
                models.QueryRequest(query=[0.0, 1.0, 0.0], limit=1),
            ],
        )
        return [response.points[0].id for response in responses]
    finally:
        await client.close()
```

## Local and Server Differences

The async entry point intentionally keeps local and remote code similar, but not every server behavior exists locally.

- Local mode is best for small tests, examples, and prototypes. For large collections or concurrent storage access, use a Qdrant server.
- Local `:memory:` mode is process-local and disappears when the client is dropped or the process exits.
- Persistent local mode uses storage locks; open one client per storage directory unless you know the concurrency model.
- Raw REST and gRPC properties are available only on remote clients; local clients raise `NotImplementedError` for raw transport stubs.
- Server-only distributed and shard workflows require an actual Qdrant service. Local mode can list empty snapshot collections in some cases, but snapshot creation/recovery and cluster operations should be treated as server workflows unless verified for the chosen local setup.
- Local alias responses may not compare the same way as remote assertions. Inspect the response's `.aliases` field rather than treating the response object itself as an empty-list boolean.

## Generated Parity Caveats

The async client is generated to mirror the sync client's public API and delegate to async local/remote backends. Treat this as parity guidance, not a reason for skill users to run maintainer generation tools.

- Prefer high-level `AsyncQdrantClient` methods over raw generated REST/gRPC stubs unless a task explicitly needs transport-level behavior.
- When a sync method exists but the async method signature seems different, check the installed package's `AsyncQdrantClient` signature instead of guessing from older examples.
- Generated docstrings may contain sync wording such as `QdrantClient`; examples in this sub-skill show the async call pattern that should be used.
- Maintainer consistency checks and async-generation scripts are provenance and maintenance references only. They are not bundled runtime scripts and are not prerequisites for using this skill.
