# Client Operation Troubleshooting

Use this reference for synchronous `QdrantClient` method-level failures. Route connection setup, authentication, TLS, server availability, and transport-specific failures to the connection/transport sub-skill; route local persistence concerns to local-mode; route async issues to async-client; route embedding-object issues to inference.

## `AssertionError: Unknown arguments: [...]`

Most public sync methods assert that no unexpected `**kwargs` remain.

Likely causes:

- Misspelled parameter name, such as `filter=` instead of method-specific `query_filter=`, `scroll_filter=`, `count_filter=`, or `facet_filter=`.
- Using an option from a different method family, such as passing `consistency` to a write method that does not accept it.
- Old code using a renamed parameter. `update_collection` still accepts `optimizer_config` as compatibility input only when `optimizers_config` is not also supplied; prefer `optimizers_config`.
- Passing raw REST/HTTP API body fields directly into `QdrantClient` methods instead of using the client method signature.

Recovery:

1. Check `references/api-reference.md` for the exact method signature family.
2. Move model fields into the appropriate `models.*` object, for example `models.Filter(...)`, `models.QueryRequest(...)`, or alias operation models.
3. Keep only documented top-level method parameters in the client call.

## Collection Creation or Update Fails

Symptoms:

- Collection already exists or does not exist.
- Vector size/distance mismatch later during upsert/query.
- Named vector queries fail because the vector name is missing.
- Deprecated `recreate_collection` warnings appear.

Recovery:

- Use `collection_exists(collection_name)` before creating or deleting when idempotence matters.
- Use `get_collection(collection_name)` to inspect `config.params.vectors`, `config.params.sparse_vectors`, payload schema, and warnings.
- For unnamed vectors, create with a single `models.VectorParams(size=..., distance=...)` and upsert points with list vectors.
- For named vectors, create with a dict of vector names and upsert points with matching vector-name dictionaries.
- Prefer explicit delete/create flows over `recreate_collection` for new code because `recreate_collection` is deprecated.

## Upsert or Vector Update Fails

Likely causes:

- Point vector length does not match the collection vector size.
- Named-vector point data is missing a required vector name or includes an unknown one.
- Multi-vector data shape is wrong: use `list[list[float]]` for a multivector field, not a flat vector.
- Payload contains non-JSON-like values that cannot be serialized.
- `wait=False` was used and a read immediately after the update observes stale data.
- Direct gRPC point structures are used where `models.PointStruct` should be used.

Recovery:

- Inspect collection vector config with `get_collection` before constructing points.
- Use `models.PointStruct(id=..., vector=..., payload=...)` for normal upserts.
- Use `models.PointVectors(id=..., vector=...)` for `update_vectors`.
- Use `wait=True` while debugging or when the next line reads the updated data.
- Use JSON-compatible payload values: strings, numbers, booleans, lists, dicts, and null-equivalent values.

## Query Returns Wrong Results or Errors

Likely causes:

- Wrong vector name or missing `using` on a named-vector collection.
- Query vector dimension does not match the selected vector field.
- `query_filter` is omitted or incorrectly built.
- `with_payload=False` or `with_vectors=False` hides data expected in the result.
- `score_threshold` direction is misunderstood. Depending on distance function, scores above or below the threshold may be considered better.
- Large `offset` pagination is used for deep paging; `scroll` is usually better for collection iteration.
- Prefetch/fusion uses too-small `limit` values in prefetch branches, causing the final fusion query to miss expected candidates.

Recovery:

- For named vectors, pass `using="vector_name"` or use query/vector structures that explicitly identify the vector.
- Validate vector dimensions against `get_collection(...).config.params.vectors`.
- Use `models.Filter(must=[...])` and method-specific filter parameter names.
- Set `with_payload=True` or a payload key list when payload is needed; set `with_vectors=True` or vector-name list only when vectors are needed.
- For fusion, increase each `models.Prefetch(..., limit=...)` above the final `limit` and test without `score_threshold` first.

## Payload Mutation Surprises

Symptoms:

- Existing payload fields disappear.
- Nested payload update writes at the wrong location.
- Delete/clear payload affects more points than intended.

Recovery:

- Use `set_payload` to merge fields and `overwrite_payload` only when replacing the entire payload is intended.
- Use `key="nested.path"` for nested `set_payload` operations and verify with `retrieve(..., with_payload=True)`.
- For filtered payload updates/deletes, build a `models.Filter` first and test it with `scroll(..., scroll_filter=filter_)` before mutating.
- Use point-id lists for exact small target sets when possible.

## Payload Index, Facet, or Order-By Issues

Likely causes:

- Index schema does not match the actual payload value types.
- Faceting a field with mixed object/scalar types produces unexpected buckets or server-specific behavior.
- `exact=False` facet/count behavior is approximate.
- An unindexed payload field is used heavily for server-side filtering or ordering.

Recovery:

- Create payload indexes with the correct `models.PayloadSchemaType` such as `KEYWORD`, `INTEGER`, `FLOAT`, `BOOL`, `DATETIME`, `UUID`, `GEO`, or `TEXT`.
- Use `exact=True` for facets/counts where correctness is more important than speed.
- Verify payload values with `scroll(..., with_payload=[field_name])` before creating an index or facet.
- Delete and recreate an index if the field schema choice was wrong.

## Alias Update Does Not Match Expectations

Likely causes:

- Alias operation models are wrapped incorrectly.
- Rename/delete operations target the wrong alias name.
- Caller expects operations to apply one-by-one instead of atomically.

Recovery:

- Wrap operations as `models.CreateAliasOperation(create_alias=models.CreateAlias(...))`, `models.RenameAliasOperation(rename_alias=models.RenameAlias(...))`, or `models.DeleteAliasOperation(delete_alias=models.DeleteAlias(...))`.
- Submit related alias changes together with `update_collection_aliases` for atomicity.
- Verify results with both `get_aliases()` and `get_collection_aliases(collection_name)`.

## Snapshot Methods Fail in Local Mode

Local Qdrant mode does not support creating, deleting, or recovering full snapshots. Use a server-backed client for snapshot operations. Local mode may return empty lists for listing snapshots, but create/delete/recover calls are not a replacement for local persistent-storage backup behavior.

For server snapshots:

- Verify permissions and storage policy before `create_snapshot` or `create_full_snapshot`.
- Treat `recover_snapshot` and `recover_shard_snapshot` as destructive operations that can overwrite server-side collection data.
- Provide `checksum` and appropriate `priority` when recovery integrity or conflict behavior matters.

## `wait`, `timeout`, `ordering`, and Consistency Surprises

- `wait=True` waits for the operation to be applied; `wait=False` can improve throughput but makes immediate reads unsafe.
- A server `WAIT_TIMEOUT` can mean the operation was accepted but not applied before the timeout.
- `ordering="weak"` is fastest but may reorder writes in distributed deployments; `medium` and `strong` trade availability/performance for ordering guarantees.
- Read `consistency` controls how many replicas are queried for supported read/search methods and can affect latency and availability.
- `shard_key_selector` only makes sense for collections created with custom sharding.

Debug by using `wait=True`, a reasonable `timeout`, a narrow point id set, and `retrieve`/`count` checks before moving to bulk or distributed settings.

## Server Unavailable, Authentication, TLS, or gRPC Errors

These are connection/transport issues rather than client-operation API mistakes. Route to the connection-and-transport sub-skill when errors mention refused connections, DNS, TLS/certificates, API keys, unauthorized requests, compatibility checks, gRPC channel options, REST/gRPC port confusion, or `prefer_grpc` behavior.
