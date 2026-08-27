---
name: local-mode
description: "Use qdrant-client local in-memory and persistent stores for safe
  prototyping, local vector tests, filtering, sparse/named/multivector queries,
  persistence, locks, and migration boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# local-mode

Use this sub-skill when the task is about running Qdrant through `qdrant-client` without a Qdrant server: `QdrantClient(":memory:")` for ephemeral tests or `QdrantClient(path=...)` for a persistent local store.

## Route Here For

- Local in-memory examples, fixtures, notebooks, and deterministic smoke tests.
- Persistent local storage that can be closed and reopened with the same collection data.
- Local dense, sparse, named-vector, multivector, payload-filter, and fusion-query behavior.
- Local-only limits: exclusive persistent-path locks, closed-instance errors, raw REST/gRPC client unavailability, and large-data warnings.
- Deciding when a prototype should move from local mode to a Qdrant server or Qdrant Cloud.

## Route Elsewhere

- Use `../client-operations/` for general collection, point, query, scroll, delete, batch, and CRUD method coverage that applies to both local and remote clients.
- Use `../connection-and-transport/` for server URLs, Cloud API keys, REST/gRPC transport, compatibility checks, TLS, timeouts, and raw transport clients.
- Use `../async-client/` for `AsyncQdrantClient(":memory:")` or async local usage.
- Use `../inference/` for FastEmbed, local model downloads, `models.Document`, GPU inference extras, and Cloud inference.

## Quick Start

```python
from qdrant_client import QdrantClient, models

client = QdrantClient(":memory:")
client.create_collection(
    "demo",
    vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE),
)
client.upsert(
    "demo",
    points=[models.PointStruct(id=1, vector=[1.0, 0.0, 0.0, 0.0], payload={"tag": "local"})],
)
hits = client.query_points("demo", query=[1.0, 0.0, 0.0, 0.0], limit=1).points
assert hits[0].id == 1
client.close()
```

For a deterministic validation script after installing `qdrant-client`, run:

```bash
python sub-skills/local-mode/scripts/local_mode_smoke.py --mode memory
python sub-skills/local-mode/scripts/local_mode_smoke.py --mode persistent
```

## Read Next

- `references/local-mode.md` for in-memory and persistent recipes, named dense/sparse/multivector examples, payload filtering, score thresholds, and migration guidance.
- `references/troubleshooting.md` for lock errors, large local collections, unsupported local raw clients, closed instances, vector mismatches, and persistence surprises.
- `scripts/local_mode_smoke.py` for a safe smoke helper that exercises local dense, sparse, multivector, fusion, filtering, persistence, and locking behavior.
