# Local Mode Troubleshooting

## Persistent Path Is Already Accessed

Symptom:

```text
Storage folder ... is already accessed by another instance of Qdrant client. If you require concurrent access, use Qdrant server instead.
```

Cause: `QdrantClient(path=...)` opens an exclusive lock file in the local store. A second live client, process, notebook kernel, test worker, or stale script can block access.

Fix:

- Reuse a single client instance for the store path.
- Call `client.close()` before reopening the same `path`.
- Use a different temporary directory per parallel test worker.
- Move to Qdrant server if multiple processes must read or write concurrently.

## Local Collection Is Too Large

Symptom:

```text
Local mode is not recommended for collections with more than 20,000 points.
```

Cause: local mode keeps Python/numpy-backed collection state and is intended for small experiments, not production-size stores.

Fix:

- Keep local tests small and deterministic.
- Reduce fixture size or sample the dataset.
- Switch to Qdrant in Docker, a managed server, or Qdrant Cloud when size or query latency matters.
- Treat the warning as a migration signal rather than a tunable threshold.

## Raw REST Or gRPC Client Is Not Supported

Symptom:

```text
gRPC client is not supported for <class 'qdrant_client.local.qdrant_local.QdrantLocal'>
REST client is not supported for <class 'qdrant_client.local.qdrant_local.QdrantLocal'>
```

Cause: local mode implements high-level `QdrantClient` methods directly and does not expose generated raw transport clients.

Fix:

- Use high-level methods such as `create_collection`, `upsert`, `query_points`, `scroll`, `count`, `retrieve`, and `delete_collection`.
- If code needs `client.http`, `client.grpc_points`, or `client.grpc_collections`, instantiate a remote/server client instead.
- Route transport-specific debugging to `connection-and-transport`.

## Client Was Closed

Symptom:

```text
QdrantLocal instance is closed. Please create a new instance.
```

Cause: `client.close()` was called and later code attempted to reuse the same local client.

Fix:

- Create a new `QdrantClient(":memory:")` or `QdrantClient(path=...)` after closing.
- Scope clients with `try/finally` so the close happens at the end of the workflow.
- For persistent stores, close the old client before opening a new one on the same `path`.

## Vector Name Or Shape Mismatch

Common symptoms:

```text
Dense vector <name> is not found in the collection
Sparse vector <name> is not found in the collection
Multivector <name> is not found in the collection
Wrong input: Not existing vector name error: <name>
```

Other shape mismatches can surface as numpy or validation errors during upsert or query.

Causes:

- A query uses `using="text"` but the collection configured only the default unnamed vector.
- A sparse query is sent to a dense vector name, or a dense list query is sent to a sparse-only collection.
- A multivector query is sent to a vector that lacks `multivector_config`.
- Upserted vector dimensions do not match `models.VectorParams(size=...)`.
- A point in a named-vector collection omits a vector required by the query path.

Fix:

- Match collection configuration, point vector keys, and query `using` exactly.
- Use `vectors_config={}` with `sparse_vectors_config={"text": models.SparseVectorParams()}` for sparse-only collections.
- Use `models.VectorParams(..., multivector_config=models.MultiVectorConfig(...))` for multivectors.
- Keep all dense vectors at the declared `size`.
- Query the default unnamed vector by omitting `using`, and query named vectors by passing `using=<name>`.

## Persistent Data Did Not Reappear

Causes:

- The first client used `QdrantClient(":memory:")` instead of `QdrantClient(path=...)`.
- The script reopened a different directory path.
- The first client never finished the create/upsert workflow before the process exited.
- A test used a temporary directory that was deleted after the context manager exited.

Fix:

- Use `QdrantClient(path=str(store_dir))` for both write and read phases.
- Close the writer before reopening in another client.
- Log or pass the same store directory explicitly.
- For tests, keep the temporary directory alive across write and reopen assertions.

## Constructor Picks Remote Instead Of Local

Symptom: the code unexpectedly tries to reach `http://...` or a host/port instead of opening a local store.

Cause: `QdrantClient(location="some/path")` treats a non-`:memory:` string as a URL-like remote location. Persistent local mode requires `path="some/path"`.

Fix:

```python
QdrantClient(":memory:")          # local ephemeral
QdrantClient(path="./qdrant-db")  # local persistent
QdrantClient(url="http://...")    # remote/server
```

Also avoid setting more than one of `location`, `url`, `host`, or `path`.

## Cloud Inference Rejected In Local Mode

Symptom:

```text
Cloud inference is not supported for local Qdrant, consider using FastEmbed or switch to Qdrant Cloud
```

Cause: `cloud_inference=True` is only valid for a Qdrant Cloud/server client.

Fix:

- For local inference with `models.Document`, install and use the FastEmbed extras covered by `inference`.
- For Cloud inference, instantiate a remote Cloud client with `cloud_inference=True`.

## Fusion Query Requires Prefetches

Symptom:

```text
Cannot perform fusion without prefetches
Query is required for merging prefetches
```

Cause: local fusion merges prefetch result sets. A `models.FusionQuery` without `prefetch`, or a nested prefetch without its own query, has no sources to merge.

Fix:

```python
client.query_points(
    "collection",
    prefetch=[
        models.Prefetch(query=[1, 0, 0, 0], using="text", limit=10),
        models.Prefetch(query=[1, 0, 0, 0], using="image", limit=10),
    ],
    query=models.FusionQuery(fusion=models.Fusion.RRF),
    limit=10,
)
```

## Payload Filter Returns No Points

Likely causes:

- The payload path is wrong for nested dictionaries or arrays.
- The field exists but has a list value and the match condition expects a scalar not present in the list.
- Date strings are not parseable as datetimes for `DatetimeRange`.
- Geo filters use invalid `{"lat": ..., "lon": ...}` payload shapes.
- `must`, `should`, and `must_not` conditions combine more strictly than intended.

Fix:

- Inspect one record with `scroll(..., with_payload=True)`.
- Use JSON-path style keys such as `country.cities[].name`, and quote literal dotted keys like `the."nested.key"`.
- Add conditions incrementally until the first failing condition is isolated.
- Prefer small local fixtures with known payloads when debugging filter behavior.
