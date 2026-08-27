---
name: client-operations
description: "Use sync QdrantClient for collections, point writes, universal
  queries, payloads, indexes, aliases, snapshots, facets, matrix search,
  batching, and cluster-adjacent client methods."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Client Operations

Use this sub-skill when a task asks for synchronous `QdrantClient` workflows after the client is already configured: create or inspect collections, insert/update/delete points, run query/search/recommend/discover operations, mutate payloads, create payload or vector indexes, manage aliases, use snapshots, run facets or matrix search, or choose the right sync method for a Qdrant operation.

## Start Here

- Read `references/api-reference.md` to choose the correct `QdrantClient` method, understand accepted REST/gRPC model inputs, and check important parameters such as `wait`, `timeout`, `consistency`, `ordering`, `using`, `with_payload`, and `with_vectors`.
- Read `references/workflows.md` for self-contained recipes covering collection creation, upsert/retrieve/query, filters, payload mutation, aliases, indexes, facets, matrix search, snapshots, and shard/cluster-adjacent methods.
- Read `references/troubleshooting.md` when calls fail with unknown keyword assertions, vector dimension/name errors, invalid filters or payloads, timeout/write-ordering surprises, unsupported local operations, or server availability issues.

## Boundaries

- Use this sub-skill for sync public API operations on an existing `QdrantClient` instance, including method-level REST/gRPC model acceptance.
- Use `../local-mode/SKILL.md` for choosing `QdrantClient(":memory:")` versus persistent local storage, local storage cleanup, and local-mode limitations beyond method behavior.
- Use `../connection-and-transport/SKILL.md` for `url`, `host`, `api_key`, TLS, headers, auth providers, `prefer_grpc`, ports, server compatibility, and network errors.
- Use `../async-client/SKILL.md` for `AsyncQdrantClient`, async context management, and awaitable method equivalents.
- Use `../inference/SKILL.md` when `models.Document`, `models.Image`, FastEmbed, remote cloud inference, or embedding-size discovery is central to the task.
- Use `../migration-and-upload/SKILL.md` for high-volume ingestion, `upload_points`, `upload_collection`, `migrate`, batching internals, parallel upload, and retry strategy.
- Use `../models-and-conversions/SKILL.md` for deep REST/gRPC conversion details, generated model schemas, and translating between low-level gRPC and REST structures.

## Method Choice Cheatsheet

- Collection lifecycle: `collection_exists`, `create_collection`, `get_collection`, `get_collections`, `update_collection`, `delete_collection`; avoid new use of deprecated `recreate_collection`.
- Point writes: `upsert`, `update_vectors`, `delete_vectors`, `delete`, `batch_update_points`; use migration/upload guidance for large initial loads.
- Reads and queries: `query_points`, `query_batch_points`, `query_points_groups`, `retrieve`, `scroll`, `count`.
- Advanced query forms: pass `models.NearestQuery`, `models.RecommendQuery`, `models.DiscoverQuery`, `models.ContextQuery`, `models.FusionQuery`, `models.Prefetch`, `models.LookupLocation`, and `score_threshold` through `query_points`.
- Payload and indexes: `set_payload`, `overwrite_payload`, `delete_payload`, `clear_payload`, `create_payload_index`, `delete_payload_index`, `create_vector_name`, `delete_vector_name`, `facet`.
- Administration: `update_collection_aliases`, `get_aliases`, `get_collection_aliases`, snapshot methods, shard-key methods, cluster-status methods, and optimization/telemetry methods.

## Safe Defaults

- Prefer `from qdrant_client import QdrantClient, models` and `qdrant_client.models` classes in examples.
- Start examples with `QdrantClient(":memory:")` when no server behavior is required, but route persistent local and connection setup details to sibling sub-skills.
- For mutating server calls, decide intentionally whether `wait=True` is required; it is the default for most direct updates and snapshots but not for bulk upload helpers.
- For reads, request only needed payload/vector data using `with_payload` and `with_vectors`; full vectors can be large.
- For multi-vector collections, always name the vector with `using="name"` in queries unless the query vector structure already carries the name.
