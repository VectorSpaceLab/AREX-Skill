# Upload and Migration Reference

This reference covers qdrant-client 1.18.0 bulk upload and migration behavior at the user level. It is self-contained and focuses on public methods and operational consequences rather than private implementation details.

## Choose the Upload Method

| Task | Use | Why |
| --- | --- | --- |
| Vectors, payloads, and ids are separate aligned sequences | `client.upload_collection(...)` | The helper batches the three streams together and generates ids when `ids=None`. |
| Each point already has id, vector, and payload | `client.upload_points(...)` | The point object keeps multi-vector, sparse, and payload data together. |
| One-off or small mutation | `client.upsert(...)` | Direct CRUD is simpler; route detailed CRUD behavior to `client-operations`. |
| Bulk upload to a server with high throughput | `QdrantClient(..., prefer_grpc=True)` plus `upload_collection` or `upload_points` | The uploader chooses the gRPC batch uploader when `prefer_grpc=True`; otherwise it uses REST. |
| Upload with local embedding inputs | `upload_collection` / `upload_points` with inference objects after reading `inference` | The public client inspects inference objects before forwarding upload to the underlying client. |

## Public Signatures and Core Parameters

Server-facing `QdrantClient` upload helpers accept these important parameters:

```python
client.upload_collection(
    collection_name: str,
    vectors,
    payload=None,
    ids=None,
    batch_size=64,
    parallel=1,
    method=None,
    max_retries=3,
    wait=False,
    shard_key_selector=None,
    update_filter=None,
    update_mode=None,
)

client.upload_points(
    collection_name: str,
    points,
    batch_size=64,
    parallel=1,
    method=None,
    max_retries=3,
    wait=False,
    shard_key_selector=None,
    update_filter=None,
    update_mode=None,
)
```

Local clients accept the same public calls through `QdrantClient`, but local upload behaves synchronously like `wait=True` and ignores remote-only throughput knobs.

Parameter meanings:

- `batch_size`: number of points per upload request for server clients. Default is `64`.
- `parallel`: number of worker processes for server upload. Use `1` for the simplest behavior; use `2+` only when inputs are picklable and the environment supports multiprocessing.
- `method`: multiprocessing start method. If omitted, qdrant-client uses `forkserver` when available, otherwise `spawn`. Passing an unavailable method raises `ValueError`.
- `max_retries`: maximum attempts for generic batch failures. Rate-limit responses with retry-after are slept and retried according to the service signal.
- `wait`: `False` means each server request can return after the update is accepted; `True` waits for server-side application and is safer before immediate reads.
- `shard_key_selector`: writes to selected custom shard groups and overrides shard keys written in records. Use only when the collection uses custom sharding.
- `update_filter`: updates only matching existing points; non-matching points are inserted.
- `update_mode`: changes upsert semantics, such as insert-only or update-only strategies when supported by the server version.

## `upload_collection` Input Shapes

`upload_collection` expects the number of vector records, payload records, and ids to align. If `payload` or `ids` are omitted, qdrant-client supplies empty payloads or generated ids.

Common shapes:

```python
import numpy as np

vectors = np.asarray([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
payload = [{"group": "a"}, {"group": "b"}]
ids = [10, 11]
client.upload_collection("items", vectors=vectors, payload=payload, ids=ids, wait=True)
```

```python
vectors = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
client.upload_collection("items", vectors=vectors, ids=[10, 11], wait=True)
```

Named dense vectors can be provided as per-point vector dictionaries:

```python
vectors = [
    {"text": [0.1, 0.2, 0.3], "image": [0.9, 0.8]},
    {"text": [0.4, 0.5, 0.6], "image": [0.7, 0.6]},
]
client.upload_collection("items", vectors=vectors, payload=[{"i": 1}, {"i": 2}], wait=True)
```

Named numpy arrays are also supported when each named array has the same first dimension:

```python
vectors = {
    "text": np.asarray([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]),
    "image": np.asarray([[0.9, 0.8], [0.7, 0.6]]),
}
client.upload_collection("items", vectors=vectors, ids=[1, 2], wait=True)
```

Important alignment rules:

- `vectors` determines the intended point count.
- If `ids` is supplied, it should have exactly the same number of items as `vectors`.
- If `payload` is supplied, it should have exactly the same number of items as `vectors`.
- For named numpy vectors, all named arrays must have the same row count; otherwise qdrant-client asserts that each named vector should have the same number of vectors.
- If any provided stream is shorter than the vectors stream, batching can stop early or omit records. Validate lengths before upload rather than relying on a server error.
- Dense vector dimensions and vector names must match the target collection configuration. Sparse vectors must use matching `indices` and `values` lengths.

Use `scripts/upload_shape_check.py` to validate a JSON fixture or manifest before translating it into Python objects.

## `upload_points` Input Shapes

Use `upload_points` when point identity, vector data, and payload should stay bound together:

```python
from qdrant_client import models

points = [
    models.PointStruct(id=1, vector=[0.1, 0.2, 0.3], payload={"kind": "dense"}),
    models.PointStruct(
        id=2,
        vector={
            "text": [0.4, 0.5, 0.6],
            "sparse": models.SparseVector(indices=[1, 7], values=[0.2, 0.8]),
        },
        payload={"kind": "hybrid"},
    ),
]
client.upload_points("items", points=points, batch_size=64, wait=True)
```

`upload_points` is usually the better choice when:

- One payload belongs to multiple named vector fields.
- Sparse and dense vectors are mixed in a single point.
- You are reusing points returned by `scroll(..., with_vectors=True)` or migration code.
- Id generation should be explicit rather than automatic.

## REST Versus gRPC Upload

The uploader selected by qdrant-client depends on the client transport preference:

- `QdrantClient(..., prefer_grpc=False)` uses the REST batch uploader.
- `QdrantClient(..., prefer_grpc=True, grpc_port=6334)` uses the gRPC batch uploader for upload helpers.
- The REST uploader builds REST `PointStruct` objects and calls the REST upsert endpoint.
- The gRPC uploader converts ids, vectors, shard selectors, filters, and update modes to gRPC structures and calls the gRPC upsert endpoint.

Prefer gRPC when:

- A Qdrant server exposes the gRPC port.
- Large or frequent uploads make request overhead significant.
- The environment can connect to both the REST and gRPC ports if other methods still need REST coverage.

Prefer REST when:

- You are debugging request payloads or network/proxy behavior.
- The deployment does not expose gRPC.
- The task needs simpler connectivity or proxy configuration.

Connection construction, Cloud credentials, TLS, headers, and compatibility checks belong in `connection-and-transport`.

## Batching and Parallelism

For server clients, qdrant-client forms upload batches before sending them:

- `upload_points` batches `PointStruct` records into parallel lists of ids, vectors, and payloads.
- `upload_collection` batches vectors, payload, and ids together.
- Numpy arrays are sliced by rows and converted to Python lists before upload.
- If ids are omitted, generated UUID ids are used.
- If payload is omitted, empty payloads are used.

With `parallel=1`, the uploader runs in the current process. With `parallel > 1`, qdrant-client starts worker processes and sends batches through multiprocessing queues. Worker results are unordered, but each batch is independent because Qdrant point ids identify records.

Use `parallel > 1` when:

- A remote Qdrant server is the bottleneck target and parallel writes improve throughput.
- Inputs can be pickled and sent to worker processes.
- The script is protected by the usual multiprocessing entry-point guard when the platform requires it.

Keep `parallel=1` when:

- Running inside notebooks, interactive shells, serverless handlers, or applications that already manage worker pools.
- Debugging data-shape failures.
- Using non-picklable generators, file handles, database cursors, or objects bound to a single process.

For benchmarks or very large uploads, start with `batch_size=64`, `parallel=1`, `wait=True` for correctness, then raise `parallel`, adjust `batch_size`, and switch to `wait=False` only after count/query validation is separated from enqueueing.

## Wait Semantics and Validation

`wait=False` is the default for bulk upload to a server. It confirms that the server accepted the update request, not that all changes are immediately visible to reads. Use `wait=True` when:

- The next line calls `count`, `scroll`, `query_points`, or `get_collection` and expects the uploaded points to be present.
- A migration or test must assert exact point counts.
- A workflow needs deterministic failure behavior rather than eventual indexing.

Validation patterns:

```python
client.upload_points("items", points=points, wait=True)
assert client.count("items").count == expected_count
```

```python
client.upload_collection("items", vectors=vectors, payload=payload, ids=ids, wait=True)
info = client.get_collection("items")
assert info.points_count == len(ids)
```

For `wait=False`, poll `count` or `scroll` with a timeout before reporting success to a user or downstream system.

## Shard Keys, Filters, and Update Modes

Bulk helpers pass shard and update controls through to upsert:

```python
client.upload_collection(
    "items",
    vectors=vectors,
    payload=payload,
    ids=ids,
    shard_key_selector="tenant-a",
    wait=True,
)
```

Notes:

- `shard_key_selector` is meaningful for collections created with custom sharding. It writes updates into the selected shard group and overrides shard keys embedded in records.
- `update_filter` lets a write update only matching points while inserting non-matching points.
- `update_mode` can request insert-only or update-only behavior when supported by the server.
- Migration does not support collections with custom sharding even though upload can target custom shard keys.

## Migration APIs

Two equivalent entry points are available:

```python
source_client.migrate(
    dest_client,
    collection_names=None,
    batch_size=100,
    recreate_on_collision=False,
)
```

```python
from qdrant_client.migrate import migrate

migrate(
    source_client=source_client,
    dest_client=dest_client,
    collection_names=None,
    batch_size=100,
    recreate_on_collision=False,
)
```

Migration behavior:

1. Select collections from the source client. If `collection_names=None`, all source collections are selected. If a named collection is missing, an assertion fails before migration.
2. Reject selected source collections that use custom sharding.
3. Find same-named destination collections.
4. If collisions exist and `recreate_on_collision=False`, raise `ValueError` without migrating.
5. If `recreate_on_collision=True`, delete and recreate colliding destination collections.
6. Recreate selected destination collections from source collection config: dense vectors, sparse vectors, shard/replication/write-consistency settings, on-disk payload flag, HNSW config, optimizer config, WAL config, quantization config, strict mode config, and payload indexes.
7. Scroll source points with `with_vectors=True` and upload them to the destination with `upload_points(..., wait=True)`.
8. Assert that source and destination point counts are equal.

Migration is a collection-and-point migration helper, not a full operational backup plan. Do not assume aliases, snapshots, cluster topology, credentials, or application-side metadata are copied unless your workflow recreates them separately.

## Selected-Collection Migration

Use `collection_names` to migrate only chosen collections:

```python
source.migrate(
    destination,
    collection_names=["products", "documents"],
    batch_size=200,
    recreate_on_collision=False,
)
```

Before running it:

- Confirm each selected collection exists on the source.
- Confirm the destination either lacks those names or is safe to recreate.
- Confirm no selected source collection uses custom sharding.
- Stop writes to the selected source collections during migration or accept that the final count assertion can fail.

## Collision Policy

The default collision policy is conservative:

```python
source.migrate(destination, recreate_on_collision=False)
```

This raises `ValueError` if any selected destination collection already exists.

Use destructive recreation only when intended:

```python
source.migrate(destination, recreate_on_collision=True)
```

This deletes colliding destination collections, recreates their schema from the source, uploads source points, and then validates counts. It is appropriate for controlled refreshes, test fixtures, and destination scratch stores; it is risky for shared production collections.

## Local and Remote Migration Notes

- Local-to-local and local-to-server migration can be useful for prototyping or seeding a server from a local persistent store.
- Server-to-local migration can create a compact local fixture for development.
- Server-to-server migration requires both clients to stay reachable for collection inspection, scrolling, upload, and count validation.
- Local clients upload synchronously; remote clients depend on network availability, service limits, timeouts, and transport configuration.
- For large remote migrations, choose a conservative `batch_size`, use `prefer_grpc=True` on the destination when available, and migrate during a quiet period to avoid concurrent source changes.

## Safe Preflight Checklist

Before upload:

- The collection exists and vector names/dimensions match the planned vectors.
- `payload`, `ids`, and `vectors` have the same point count when supplied separately.
- Sparse vectors have equal `indices` and `values` lengths.
- `wait=True` is selected when immediate validation matters.
- `prefer_grpc=True` is used only when the gRPC port is reachable.
- `parallel > 1` is used only from a safe multiprocessing context.

Before migration:

- Source and destination clients are initialized and closeable.
- Selected source collections exist.
- Destination collision behavior is explicit.
- Custom-shard collections are excluded or handled manually.
- Source writes are paused or the final count assertion is expected to reflect a point-in-time race.
- The destination has enough resources and compatible server capabilities for the source collection configs.
