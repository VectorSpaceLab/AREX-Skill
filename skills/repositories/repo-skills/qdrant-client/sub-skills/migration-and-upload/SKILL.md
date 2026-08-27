---
name: migration-and-upload
description: "Use qdrant-client bulk upload and collection migration helpers for
  batching, parallel ingestion, REST/gRPC upload paths, retries, and
  collision-safe migration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Migration and Upload

Use this sub-skill when a task is about high-throughput ingestion or moving collections between Qdrant clients: `upload_collection`, `upload_points`, batching, `parallel`, `wait`, `max_retries`, REST versus gRPC uploader choice, or `client.migrate(...)` / `qdrant_client.migrate.migrate(...)`.

## Route Here For

- Loading many vectors, payloads, and ids into an existing collection.
- Choosing between `upload_collection` and `upload_points` for dense, named, sparse, or multivector data.
- Tuning `batch_size`, `parallel`, multiprocessing start `method`, `max_retries`, `wait`, `timeout`, and `prefer_grpc` for bulk upload.
- Explaining user-level uploader internals: how batches are formed, how REST/gRPC uploaders build points, and what parallel workers do.
- Migrating all or selected collections from one `QdrantClient` to another, including local-to-local, local-to-server, server-to-local, and server-to-server planning.
- Handling migration collisions, unsupported custom-shard collections, and post-migration count validation.

## Route Elsewhere

- Use `../client-operations/SKILL.md` for ordinary collection creation, `upsert`, `query_points`, `scroll`, `count`, payload updates, indexes, snapshots, and one-off writes.
- Use `../connection-and-transport/SKILL.md` for constructing remote clients, Qdrant Cloud credentials, `url`, ports, TLS, headers, and transport authentication.
- Use `../local-mode/SKILL.md` for deciding between `QdrantClient(":memory:")` and persistent local storage, local locks, and local persistence behavior.
- Use `../async-client/SKILL.md` when the surrounding application is async; treat these bulk helpers as blocking work unless the async reference says otherwise.
- Use `../inference/SKILL.md` when `models.Document`, `models.Image`, FastEmbed, or Qdrant Cloud inference objects are the main concern before upload.
- Use `../models-and-conversions/SKILL.md` for low-level REST/gRPC model conversion and generated model schema details.

## Start Here

1. Ensure the target collection already exists with vector names, dimensions, dense/sparse settings, and sharding policy that match the data.
2. Use `upload_collection` when vectors, payloads, and ids are separate aligned sequences; use `upload_points` when each item is already a `models.PointStruct` with its own id, vector, and payload.
3. For server or Cloud upload, prefer `wait=True` when the next step immediately reads counts or queries newly uploaded data. Leave `wait=False` only when enqueue acknowledgement is enough.
4. For high-throughput server upload, construct the client with `prefer_grpc=True` and a valid `grpc_port` when gRPC is available; REST remains the default and is easier to debug.
5. Read `references/upload-and-migration.md` before using `parallel > 1`, custom shard keys, named vectors, sparse vectors, or migration.
6. Run `scripts/upload_shape_check.py` against a small JSON fixture or planned upload manifest when vector/payload/id alignment is uncertain.

## Minimal Upload Patterns

Separate vectors, payloads, and ids:

```python
import numpy as np
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333", prefer_grpc=True, grpc_port=6334)
client.upload_collection(
    collection_name="items",
    vectors=np.asarray([[0.1, 0.2, 0.3], [0.2, 0.3, 0.4]], dtype="float32"),
    payload=[{"sku": "a"}, {"sku": "b"}],
    ids=[1, 2],
    batch_size=64,
    parallel=2,
    wait=True,
)
```

Point-structured upload:

```python
from qdrant_client import QdrantClient, models

client = QdrantClient(":memory:")
client.upload_points(
    collection_name="items",
    points=[
        models.PointStruct(id=1, vector=[0.1, 0.2, 0.3], payload={"sku": "a"}),
        models.PointStruct(id=2, vector={"text": [0.2, 0.3, 0.4]}, payload={"sku": "b"}),
    ],
    wait=True,
)
```

Shape check for a fixture before upload:

```bash
python sub-skills/migration-and-upload/scripts/upload_shape_check.py --spec upload.json --mode upload-collection --vector-size default=3
```

## Minimal Migration Pattern

```python
from qdrant_client import QdrantClient

source = QdrantClient(path="source-store")
destination = QdrantClient(":memory:")
source.migrate(
    destination,
    collection_names=["products", "documents"],
    batch_size=100,
    recreate_on_collision=False,
)
```

For the standalone function form:

```python
from qdrant_client.migrate import migrate

migrate(source_client=source, dest_client=destination, collection_names=["products"])
```

## Safety Defaults

- Do not use `recreate_on_collision=True` unless deleting and recreating same-named destination collections is intended.
- Do not migrate collections that use custom sharding; qdrant-client raises `ValueError` because that migration path is unsupported.
- Keep source collections stable during migration so final source and destination counts can match.
- For server uploads, increase `timeout` and reduce `batch_size` before increasing retry loops when payloads are large or the service is rate-limited.
- In local mode, upload helpers behave synchronously like `wait=True`; remote-only tuning knobs such as `parallel`, `batch_size`, and `wait` matter most for server clients.

## References

- `references/upload-and-migration.md` covers method signatures, accepted shapes, batching, REST/gRPC uploader choice, parallel workers, wait semantics, retry behavior, shard keys, and migration internals.
- `references/troubleshooting.md` covers exhausted generators, vector/payload/id mismatches, service availability, custom-shard migration failures, collisions, batch-size/timeouts, and count mismatches.
- `scripts/upload_shape_check.py` validates JSON upload fixtures or manifests without connecting to Qdrant.
