---
name: models-and-conversions
description: "Use qdrant_client.models, REST model classes, REST/gRPC
  interoperability, pydantic compatibility helpers, payload/filter/query
  schemas, inference schema parsing, and conversion debugging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Models and Conversions

Use this sub-skill when a task is about constructing `qdrant_client.models` objects, choosing generated REST model classes or enums, understanding accepted REST/gRPC inputs, converting between REST and gRPC shapes, debugging pydantic validation, inspecting filter/query/payload schemas, or tracing inference-object paths through schema parsing.

## Start Here

- Read `references/models-reference.md` for common classes, enums, constructor patterns, strict validation behavior, payload/filter/query model shapes, and inference-object schema notes.
- Read `references/conversions.md` for `RestToGrpc`, `GrpcToRest`, common type aliases, payload value conversion, datetime handling, prefetch/query request conversion, sparse/vector batch conversion, and debugging tactics.
- Read `references/troubleshooting.md` when pydantic rejects extra fields, enums do not match, sparse vectors or batches fail conversion, REST/gRPC protobuf types are mixed incorrectly, datetime ranges shift, or nested prefetch/filter conversion is confusing.
- Run `scripts/conversion_smoke.py` for deterministic examples covering nested filters, `min_should`, prefetch query requests, sparse vectors, payload datetime conversion, and round-trip REST/gRPC checks.

## Boundaries

- Use this sub-skill for data-model construction, generated REST model details, REST/gRPC conversion helpers, pydantic v1/v2 compatibility, payload/filter/query schemas, inference schema parsing, and conversion-level debugging.
- Use `../client-operations/SKILL.md` for actual `QdrantClient` collection, upsert, query, payload, index, alias, snapshot, facet, or matrix-search calls.
- Use `../inference/SKILL.md` for local FastEmbed, Cloud inference, model catalogs, embedding-size helpers, and end-to-end `Document`/`Image` workflows.
- Use `../connection-and-transport/SKILL.md` for raw REST/gRPC stubs, transport selection, authentication, channel lifecycle, and network behavior.
- Use `../async-client/SKILL.md` for awaitable client APIs; the same model classes usually apply after the async method is chosen.
- Use `../migration-and-upload/SKILL.md` for bulk upload helpers, batch splitting, retry strategy, and high-volume ingestion behavior.

## Safe Defaults

- Prefer `from qdrant_client import models` in user-facing examples, then construct `models.VectorParams`, `models.PointStruct`, `models.Filter`, and query classes from that namespace.
- Treat generated REST models as strict pydantic models: use documented field names, avoid unknown keywords, and pass enum values from `models.Distance`, `models.Fusion`, `models.PayloadSchemaType`, and related enums rather than ad-hoc spelling.
- For conversion debugging, convert one object at a time with `RestToGrpc.convert_*` or `GrpcToRest.convert_*` and inspect the resulting message/model before involving a live client.
- For query APIs, normalize a single `Prefetch` versus `list[Prefetch]` intentionally; conversion wraps a single top-level `QueryRequest.prefetch` into a list for gRPC `QueryPoints`.
- Keep `Document`, `Image`, and `InferenceObject` examples at schema/construction level here; route embedding execution and optional dependencies to `inference`.

## Minimal Patterns

```python
from qdrant_client import models
from qdrant_client.conversions.conversion import RestToGrpc

query = models.QueryRequest(
    prefetch=models.Prefetch(
        query=models.NearestQuery(nearest=[0.1, 0.2, 0.3]),
        using="dense",
        filter=models.Filter(
            must=[models.FieldCondition(key="kind", match=models.MatchValue(value="doc"))]
        ),
        limit=20,
    ),
    query=models.FusionQuery(fusion=models.Fusion.RRF),
    limit=5,
)

grpc_query = RestToGrpc.convert_query_request(query, collection_name="docs")
```

```python
from qdrant_client import models

point = models.PointStruct(
    id=1,
    vector={"dense": [0.1, 0.2, 0.3], "sparse": models.SparseVector(indices=[2], values=[0.8])},
    payload={"tag": "example"},
)
```

## Acceptance Checks

- Model examples use real qdrant-client classes and field names, not raw JSON guesses.
- Conversion guidance distinguishes REST pydantic models from protobuf gRPC messages and names the exact converter direction.
- Troubleshooting covers strict extra-field validation, enum spelling, sparse vector length/shape, protobuf/REST type confusion, datetime/timezone conversion, and nested prefetch/filter normalization.
- No runtime instruction depends on reading the original repository checkout, tests, docs, or local environment paths.
