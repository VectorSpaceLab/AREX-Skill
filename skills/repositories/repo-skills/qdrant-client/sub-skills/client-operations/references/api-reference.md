# Sync QdrantClient API Reference

This reference covers public synchronous `QdrantClient` operation families for qdrant-client 1.18.0. The sync client accepts both REST model classes from `qdrant_client.models` and low-level gRPC structures in many method bodies, converting between transports when possible. Prefer `qdrant_client.models` for new code because the client warns that direct `grpc.PointStruct` input is deprecated for point upserts and does not support local inference features.

## Client Entry Point Notes

`QdrantClient` can be constructed for local or remote operation. Method behavior below assumes the client already exists. Connection, authentication, URL/host/path mode selection, `prefer_grpc`, TLS, and headers belong in the connection/transport sub-skill; persistent local path behavior belongs in the local-mode sub-skill.

Important constructor options verified for qdrant-client 1.18.0 include `location`, `url`, `host`, `path`, `port`, `grpc_port`, `prefer_grpc`, `api_key`, `cloud_inference`, `local_inference_batch_size`, `pool_size`, and `headers`. Only one of `location`, `url`, `host`, or `path` should be specified. `QdrantClient(":memory:")` creates an in-memory local instance; `QdrantClient(path="...")` creates a persistent local instance; remote defaults use localhost REST unless URL/host settings say otherwise.

## Method-Level Conventions

- Most public methods assert that no unexpected keyword arguments remain and raise an `AssertionError` with `Unknown arguments: [...]` for misspelled or stale kwargs.
- Direct update methods usually default to `wait=True`; `timeout` is operation-specific and measured in seconds where supported.
- Read methods often accept `consistency`, `timeout`, and sometimes `shard_key_selector` for distributed deployments.
- Write methods often accept `ordering` with weak/medium/strong semantics and sometimes `shard_key_selector` for custom sharding.
- `with_payload` can be `True`, `False`, a list of payload keys, or a payload selector model. `with_vectors` can be `True`, `False`, or a list of vector names.
- `QdrantClient` routes custom methods through local, REST, or gRPC implementations. `client.http`, `client.grpc_points`, and `client.grpc_collections` are raw generated clients and are only available for remote clients.

## Collection Lifecycle

Use these methods to create, inspect, update, and delete collections:

- `collection_exists(collection_name) -> bool`: check existence before creating or deleting.
- `get_collections()`: list collection names/descriptions.
- `get_collection(collection_name)`: inspect configuration, vector params, payload schema, counts, warnings, and optimizer status.
- `create_collection(collection_name, vectors_config=None, sparse_vectors_config=None, shard_number=None, sharding_method=None, replication_factor=None, write_consistency_factor=None, on_disk_payload=None, hnsw_config=None, optimizers_config=None, wal_config=None, quantization_config=None, timeout=None, strict_mode_config=None, metadata=None) -> bool`: create an empty collection.
- `update_collection(collection_name, optimizers_config=None, collection_params=None, vectors_config=None, hnsw_config=None, quantization_config=None, timeout=None, sparse_vectors_config=None, strict_mode_config=None, metadata=None) -> bool`: patch mutable collection configuration.
- `delete_collection(collection_name, timeout=None) -> bool`: remove a collection and its data.
- `recreate_collection(...)`: deprecated; prefer `collection_exists` plus `delete_collection`/`create_collection` when replacement is intentional.

`vectors_config` accepts either a single `models.VectorParams(size=..., distance=...)` for unnamed vectors or a mapping such as `{"text": models.VectorParams(...), "image": models.VectorParams(...)}` for named vectors. `sparse_vectors_config` accepts a mapping of sparse vector names to `models.SparseVectorParams`.

## Point Writes and Deletes

Use direct point methods for normal-sized updates and route high-volume ingestion to the migration/upload sub-skill.

- `upsert(collection_name, points, wait=True, ordering=None, shard_key_selector=None, update_filter=None, update_mode=None, timeout=None) -> models.UpdateResult`: insert or overwrite points. `points` can be a list of `models.PointStruct` or a `models.Batch`/points batch structure.
- `update_vectors(collection_name, points, wait=True, ordering=None, shard_key_selector=None, update_filter=None, timeout=None)`: update only specified vectors and keep payload/other vectors unchanged. Use `models.PointVectors(id=..., vector=...)` with a list vector or a named-vector dict.
- `delete_vectors(collection_name, vectors, points, wait=True, ordering=None, shard_key_selector=None, timeout=None)`: remove named vectors from selected points. Use `vectors=[""]` for an unnamed/default vector.
- `delete(collection_name, points_selector, wait=True, ordering=None, shard_key_selector=None, timeout=None)`: delete points by ids or a `models.Filter`/selector.
- `batch_update_points(collection_name, update_operations, wait=True, ordering=None, timeout=None) -> list[models.UpdateResult]`: execute `models.UpsertOperation`, `models.DeleteOperation`, `models.SetPayloadOperation`, `models.OverwritePayloadOperation`, `models.DeletePayloadOperation`, `models.ClearPayloadOperation`, `models.UpdateVectorsOperation`, and related update operation models in one request.

Common write controls:

- `wait=True`: return after the update is applied; safer for examples and tests.
- `wait=False`: return after the server accepts the update; useful for throughput but reads immediately after the write may not observe it.
- `ordering="weak"`, `"medium"`, or `"strong"`: trade throughput for ordering/consistency in distributed deployments.
- `update_filter`: apply updates only to existing points matching a filter; non-matching points may be inserted for `upsert` unless `update_mode` changes that behavior.
- `update_mode`: use insert-only or update-only strategies when the default upsert semantics are not desired.

## Reads, Scroll, Count, and Query

- `retrieve(collection_name, ids, with_payload=True, with_vectors=False, consistency=None, shard_key_selector=None, timeout=None) -> list[models.Record]`: fetch stored points by id.
- `scroll(collection_name, scroll_filter=None, limit=10, order_by=None, offset=None, with_payload=True, with_vectors=False, consistency=None, shard_key_selector=None, timeout=None) -> (records, next_offset)`: iterate all matching points sorted by id unless `order_by` is supplied.
- `count(collection_name, count_filter=None, exact=True, shard_key_selector=None, timeout=None) -> models.CountResult`: count all or filtered points. Use `exact=False` only when approximate counts are acceptable.
- `query_points(collection_name, query=None, using=None, prefetch=None, query_filter=None, search_params=None, limit=10, offset=None, with_payload=True, with_vectors=False, score_threshold=None, lookup_from=None, consistency=None, shard_key_selector=None, timeout=None) -> models.QueryResponse`: universal search/recommend/discover/context endpoint.
- `query_batch_points(collection_name, requests, consistency=None, timeout=None) -> list[models.QueryResponse]`: run multiple `models.QueryRequest` objects to reduce round trips.
- `query_points_groups(collection_name, group_by, query=None, using=None, prefetch=None, query_filter=None, search_params=None, limit=10, group_size=3, with_payload=True, with_vectors=False, score_threshold=None, with_lookup=None, lookup_from=None, consistency=None, shard_key_selector=None, timeout=None) -> models.GroupsResult`: query and group results by a payload field.

`query_points` accepts a point id, dense vector `list[float]`, multi-vector `list[list[float]]`, sparse vector, NumPy array, or query model. Query model choices include:

- `models.NearestQuery(nearest=...)` for explicit nearest-neighbor search, including optional `models.Mmr` for diversity.
- `models.RecommendQuery(recommend=models.RecommendInput(positive=[...], negative=[...], strategy=...))` for recommendation from positive/negative examples.
- `models.DiscoverQuery(discover=models.DiscoverInput(target=..., context=[...]))` for discovery from a target and context.
- `models.ContextQuery(context=[models.ContextPair(positive=..., negative=...)])` for context search.
- `models.FusionQuery(fusion=models.Fusion.RRF)` or `models.FusionQuery(fusion=models.Fusion.DBSF)` when combining multiple `prefetch` branches.
- `models.SampleQuery(...)` for sampling query forms supported by the server/model schema.

Use `using="vector_name"` for named-vector collections. Use `lookup_from=models.LookupLocation(collection="other_collection", vector="vector_name")` when query examples should be dereferenced from another collection/vector field.

`models.Document`, `models.Image`, and other inference objects can be supplied to selected query/write methods, but embedding behavior belongs in the inference sub-skill.

## Payload Mutation

- `set_payload(collection_name, payload, points, key=None, wait=True, ordering=None, shard_key_selector=None, timeout=None)`: merge/assign payload fields to selected points. With `key="nested.path"`, set inside a nested payload path.
- `overwrite_payload(collection_name, payload, points, wait=True, ordering=None, shard_key_selector=None, timeout=None)`: replace selected points' payloads with exactly the supplied payload.
- `delete_payload(collection_name, keys, points, wait=True, ordering=None, shard_key_selector=None, timeout=None)`: delete selected keys from selected points.
- `clear_payload(collection_name, points_selector, wait=True, ordering=None, shard_key_selector=None, timeout=None)`: remove all payload from selected points.

`points`/`points_selector` accepts point ids, a `models.Filter`, or a selector model depending on the method. Payload values must be JSON-like and serializable by the client model layer.

## Indexes and Vector Names

- `create_payload_index(collection_name, field_name, field_schema=None, field_type=None, wait=True, ordering=None, timeout=None)`: index a payload field for faster filtered operations. Use `field_schema`; `field_type` is deprecated compatibility naming.
- `delete_payload_index(collection_name, field_name, wait=True, ordering=None, timeout=None)`: remove a payload field index.
- `create_vector_name(collection_name, vector_name, vector_name_config, wait=True, ordering=None, timeout=None)`: add a new named dense or sparse vector to an existing collection.
- `delete_vector_name(collection_name, vector_name, wait=True, ordering=None, timeout=None)`: remove a named vector from a collection.

Payload index schemas include enum values such as `models.PayloadSchemaType.KEYWORD`, `INTEGER`, `FLOAT`, `GEO`, `TEXT`, `BOOL`, `DATETIME`, and `UUID`. Text, keyword, integer, geo, and other index parameter models can be supplied when advanced index configuration is needed.

## Facets and Matrix Search

- `facet(collection_name, key, facet_filter=None, limit=10, exact=False, consistency=None, timeout=None, shard_key_selector=None) -> models.FacetResponse`: count unique values for a payload key; use `exact=True` for exact counts and a suitable payload index for server performance.
- `search_matrix_pairs(collection_name, query_filter=None, limit=3, sample=10, using=None, consistency=None, timeout=None, shard_key_selector=None) -> models.SearchMatrixPairsResponse`: compute nearest-neighbor distance matrix in pair format.
- `search_matrix_offsets(collection_name, query_filter=None, limit=3, sample=10, using=None, consistency=None, timeout=None, shard_key_selector=None) -> models.SearchMatrixOffsetsResponse`: compute nearest-neighbor distance matrix in offset format.

Matrix search should specify `using` on named-vector collections and choose `sample` high enough for the intended analysis. The local, REST, and gRPC implementations are covered by congruence tests for filtered and unfiltered matrix search.

## Aliases

- `update_collection_aliases(change_aliases_operations, timeout=None) -> bool`: atomically create, delete, and rename collection aliases.
- `get_aliases() -> models.CollectionsAliasesResponse`: list all aliases.
- `get_collection_aliases(collection_name) -> models.CollectionsAliasesResponse`: list aliases for one collection.

Use `models.CreateAliasOperation(create_alias=models.CreateAlias(collection_name=..., alias_name=...))`, `models.DeleteAliasOperation(delete_alias=models.DeleteAlias(alias_name=...))`, and `models.RenameAliasOperation(rename_alias=models.RenameAlias(old_alias_name=..., new_alias_name=...))`.

## Snapshots

Snapshot methods are server-oriented. Local mode exposes listing methods but create/delete/recover snapshot methods raise local-mode unsupported errors.

- Collection snapshots: `list_snapshots(collection_name)`, `create_snapshot(collection_name, wait=True)`, `delete_snapshot(collection_name, snapshot_name, wait=True)`, `recover_snapshot(collection_name, location, api_key=None, checksum=None, priority=None, wait=True)`.
- Full-storage snapshots: `list_full_snapshots()`, `create_full_snapshot(wait=True)`, `delete_full_snapshot(snapshot_name, wait=True)`.
- Shard snapshots: `list_shard_snapshots(collection_name, shard_id)`, `create_shard_snapshot(collection_name, shard_id, wait=True)`, `delete_shard_snapshot(collection_name, shard_id, snapshot_name, wait=True)`, `recover_shard_snapshot(collection_name, shard_id, location, api_key=None, checksum=None, priority=None, wait=True)`.

Snapshot recovery can overwrite local collection data on the server side. Treat `location`, `api_key`, `checksum`, and `priority` as operational inputs and verify them before running recovery.

## Shard and Cluster-Adjacent Methods

These methods are advanced and often meaningful only against a server/distributed deployment:

- `create_shard_key(collection_name, shard_key, shards_number=None, replication_factor=None, placement=None)` and `delete_shard_key(collection_name, shard_key)` for custom-sharded collections.
- `list_shard_keys(collection_name)` to inspect custom shard keys.
- `cluster_collection_update(collection_name, cluster_operation, timeout=None)` to move/replicate/drop/restart shard operations through cluster operation models.
- `collection_cluster_info(collection_name)`, `cluster_status()`, `cluster_telemetry(details_level=None, timeout=None)`, `recover_current_peer()`, `remove_peer(peer_id, force=None, timeout=None)`, and `get_optimizations(collection_name, completed_limit=None)` for operations and diagnostics.

Route transport failures, authentication, TLS, and server compatibility errors to connection/transport guidance. Route detailed model construction for cluster operation objects to models/conversions guidance if the task requires low-level conversions.
