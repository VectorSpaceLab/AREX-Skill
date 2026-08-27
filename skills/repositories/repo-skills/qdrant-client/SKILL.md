---
name: qdrant-client
description: "Use the Python qdrant-client package for Qdrant vector database
  connections, local mode, sync and async operations, inference inputs, uploads,
  migrations, and REST/gRPC model conversion workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Qdrant Client

Use this repo skill when a task involves the Python `qdrant-client` package, `QdrantClient`, `AsyncQdrantClient`, `qdrant_client.models`, local mode, Qdrant Cloud/server connections, FastEmbed or Cloud inference inputs, bulk upload, migration, or REST/gRPC model conversion.

## Start Here

- Install with `pip install qdrant-client`; add exactly one optional inference extra only when needed: `qdrant-client[fastembed]` for CPU FastEmbed or `qdrant-client[fastembed-gpu]` for GPU FastEmbed.
- Verify basic import with `from qdrant_client import QdrantClient, AsyncQdrantClient, models`.
- Use `QdrantClient(":memory:")` for deterministic local examples and tests that do not require a running Qdrant server.
- Use `QdrantClient(url="http://localhost:6333")` or a Qdrant Cloud URL plus `api_key` for remote server workflows.
- Read `references/repo-provenance.md` before deciding whether this skill is current for a checkout, and read `references/troubleshooting.md` for cross-cutting install/import/service failures.
- Run `scripts/qdrant_client_smoke.py --mode local` after installation when you need a safe import/local/async/conversion check.

## Route By Task

- Use `sub-skills/client-operations/SKILL.md` for sync `QdrantClient` collection, point, query, payload, index, alias, snapshot, facet, matrix search, batching, and cluster-adjacent method choices.
- Use `sub-skills/local-mode/SKILL.md` for `QdrantClient(":memory:")`, persistent local stores, local dense/sparse/named/multivector queries, local locks, and local-to-server migration boundaries.
- Use `sub-skills/connection-and-transport/SKILL.md` for `url`, `host`, `prefix`, Qdrant Cloud `api_key`, REST versus gRPC, auth headers, compatibility checks, timeouts, pooling, raw clients, and close lifecycle.
- Use `sub-skills/async-client/SKILL.md` for `AsyncQdrantClient`, awaited collection/point/query/payload/snapshot operations, async local mode, and async lifecycle pitfalls.
- Use `sub-skills/inference/SKILL.md` for FastEmbed local inference, Qdrant Cloud remote inference, `models.Document`, `models.Image`, dense/sparse/hybrid model helpers, and optional dependency troubleshooting.
- Use `sub-skills/migration-and-upload/SKILL.md` for `upload_collection`, `upload_points`, batching, `parallel`, `wait`, `prefer_grpc`, retry behavior, and `migrate` workflows.
- Use `sub-skills/models-and-conversions/SKILL.md` for `qdrant_client.models`, strict pydantic model construction, REST/gRPC structures, `RestToGrpc`, `GrpcToRest`, filters, query requests, sparse vectors, and conversion debugging.

## Common Entry Points

```python
from qdrant_client import QdrantClient, AsyncQdrantClient, models

client = QdrantClient(":memory:")
client.create_collection(
    collection_name="demo",
    vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE),
)
```

```python
client = QdrantClient(
    url="https://example-cluster.region.cloud.qdrant.io:6333",
    api_key="<api-key>",
)
```

```python
client.upload_collection(
    collection_name="demo",
    vectors=[[0.1, 0.2, 0.3, 0.4]],
    payload=[{"source": "example"}],
    ids=[1],
    wait=True,
)
```

## Decision Rules

- Start with local mode for examples unless the user explicitly needs a server, Cloud features, distributed behavior, snapshots from a real service, or transport-specific debugging.
- Keep transport setup separate from API operation guidance: configure the client with `connection-and-transport`, then use `client-operations` or `migration-and-upload` for calls.
- Treat `models.Document` and `models.Image` as inference routes. They may require FastEmbed locally or `cloud_inference=True` remotely.
- Prefer `from qdrant_client import models` for user-facing code instead of importing generated REST or gRPC modules directly.
- Do not run examples that require credentials, model downloads, a Qdrant server, or large benchmark data unless the user asks for that environment explicitly.

## Bundled Helpers

- `scripts/qdrant_client_smoke.py` checks importability, local create/upsert/query, REST-to-gRPC conversion, and optional async local behavior without a server.
- Sub-skill scripts provide narrower checks: local-mode smoke, async local smoke, transport constructor probing, optional inference dependency reporting, upload shape validation, and conversion smoke examples.

## Refresh And Verification

- Use `references/repo-provenance.md` to compare this skill with a source checkout before refreshing.
- Verification artifacts and native test selections are summarized outside runtime skill content; runtime instructions never require opening the original repository checkout.
