# Migration and Upload Troubleshooting

Use this guide when qdrant-client bulk upload or migration fails, uploads fewer points than expected, or behaves differently between local and remote clients.

## Generator Exhausted on Retry or Reuse

Symptoms:

- A retry uploads zero points or fewer points than the first attempt.
- A second call with the same `points`, `vectors`, `payload`, or `ids` generator appears to do nothing.
- A migration-like wrapper retries a whole upload call and the retried iterable is empty.

Likely causes:

- Python generators are one-pass. qdrant-client materializes each batch for its internal batch retry, but it cannot rewind a generator after a whole upload call fails or after caller-owned retry logic reuses the same iterable.
- Separate `vectors`, `payload`, and `ids` iterables can advance independently if validation or logging consumes one of them first.

Fixes:

- Recreate generators inside each retry attempt.
- Prefer lists, tuples, numpy arrays, or small reusable fixtures for tests and migrations that may be retried.
- For streaming production loads, checkpoint the source stream by id or offset so a failed whole-call retry can resume intentionally.
- Run `scripts/upload_shape_check.py` on a representative JSON fixture before converting a source stream to upload objects.

## Payload, ID, and Vector Length Mismatch

Symptoms:

- Uploaded point count is lower than expected.
- Some payloads or ids are missing.
- `count` or `get_collection().points_count` does not match the source list length.
- Named numpy upload raises an assertion that each named vector should have the same number of vectors.

Likely causes:

- `upload_collection` combines vectors, payload, and ids by batch. Supplied `payload` and `ids` should have the same point count as `vectors`.
- A shorter iterable can truncate batching; longer `payload` or `ids` entries can be ignored after vectors end.
- Named vector arrays must all have the same row count.
- Sparse vector `indices` and `values` lengths must match.

Fixes:

- Check `len(vectors)`, `len(payload)`, and `len(ids)` before upload when they are materialized.
- Use `upload_points` when each point should carry its own id, vector, and payload without aligning separate streams.
- Validate a JSON fixture with `scripts/upload_shape_check.py --mode upload-collection`.
- Query or retrieve a few known ids after `wait=True` upload to confirm payload binding, not just point count.

## Vector Name or Dimension Mismatch

Symptoms:

- Upload fails with a server error about vector size, vector name, sparse vector config, or unsupported vector type.
- Upload succeeds for local fixtures but fails against a server collection.
- Querying named vectors later requires a vector name that was not uploaded.

Likely causes:

- The target collection was created with different vector names or dimensions than the upload data.
- A named-vector upload uses per-point dictionaries whose keys do not match collection vector names.
- Sparse vectors were sent to a collection without matching `sparse_vectors_config`.

Fixes:

- Inspect `client.get_collection(collection_name).config.params` before upload.
- Recreate the collection only when it is safe; otherwise transform the data to match the existing collection.
- Use `client-operations` for collection creation details and `models-and-conversions` for model/schema details.
- Validate expected dense dimensions with `scripts/upload_shape_check.py --vector-size name=size`.

## Remote Service Unavailable or Wrong Transport

Symptoms:

- REST upload raises connection errors or `UnexpectedResponse`.
- gRPC upload raises an RPC connectivity error.
- `prefer_grpc=True` works for no operations or only fails during upload.
- Upload workers fail with a generic worker termination error.

Likely causes:

- The Qdrant server or Cloud endpoint is unavailable.
- The REST port is reachable but the gRPC port is not exposed.
- TLS, API key, prefix, proxy, or header configuration belongs to the client constructor and is wrong.
- Worker processes cannot create their own REST/gRPC uploader clients with the supplied options.

Fixes:

- Start with `parallel=1` and `prefer_grpc=False` to isolate data-shape errors from transport errors.
- Verify `QdrantClient(url=..., api_key=...)` or `QdrantClient(host=..., port=..., grpc_port=...)` construction using `connection-and-transport` guidance.
- Switch back to `prefer_grpc=True` only after confirming the gRPC port is reachable.
- Increase `timeout` for large batches or slow networks.
- Use `client.close()` when clients are no longer needed, especially in workers and scripts.

## Batch Size, Timeout, and Rate Limits

Symptoms:

- Large batches time out.
- Upload warns that a batch failed and is retrying.
- Upload sleeps after a resource-exhausted or rate-limit response.
- The server accepts small uploads but rejects large uploads.

Likely causes:

- `batch_size` is too large for payload size, vector dimension, server limits, or network timeout.
- `wait=True` makes each batch slower because the server applies the update before responding.
- Server strict-mode write limits, rate limits, or resource pressure are active.
- `parallel` is too high for the server or client machine.

Fixes:

- Reduce `batch_size` first, then tune `parallel`.
- Increase client `timeout` for large requests.
- Use `prefer_grpc=True` when available for high-throughput uploads.
- Keep `wait=True` for correctness checks; use `wait=False` only when downstream validation is decoupled.
- Treat repeated rate-limit retry sleeps as a service-capacity signal, not just a client retry problem.

## Multiprocessing and Parallel Upload Failures

Symptoms:

- `ValueError` reports an unavailable start method.
- Upload works with `parallel=1` but fails with `parallel=2`.
- Worker processes terminate unexpectedly.
- Interactive notebooks or serverless functions hang during upload.

Likely causes:

- The selected `method` is not supported on the platform.
- The script is missing the multiprocessing entry-point guard required by the platform.
- Batch items or client options are not picklable.
- The runtime environment restricts process creation.

Fixes:

- Omit `method` and let qdrant-client choose `forkserver` or `spawn`, or pass a method from `multiprocessing.get_all_start_methods()`.
- Wrap script entry points in `if __name__ == "__main__":` before using `parallel > 1`.
- Use materialized Python values, numpy arrays, and `models.PointStruct` objects rather than open file handles or process-bound objects.
- Fall back to `parallel=1` when running in notebooks, web workers, or managed runtimes.

## Custom Shards Unsupported During Migration

Symptoms:

- `source_client.migrate(...)` raises `ValueError: Migration of collections with custom shards is not supported yet`.
- Upload with `shard_key_selector` works, but migration fails for the same collection.

Likely causes:

- Bulk upload supports writing to custom shard keys, but the migration helper rejects source collections whose sharding method is custom.

Fixes:

- Exclude custom-shard collections from `collection_names` and migrate them with a manual plan.
- Manually recreate destination sharding and shard keys, then scroll and upload per shard key if your application can define a safe mapping.
- Consider snapshots or Qdrant-native operational tooling for full custom-shard movement.

## Destination Collection Collisions

Symptoms:

- Migration raises `ValueError` listing collections that already exist in `dest_client`.
- A destination collection disappears during migration.

Likely causes:

- `recreate_on_collision=False` is the default and blocks migration into same-named destination collections.
- `recreate_on_collision=True` deletes and recreates colliding destination collections from source config.

Fixes:

- Keep `recreate_on_collision=False` for shared or production destinations.
- Rename destination collections before migration when data must be preserved.
- Use `recreate_on_collision=True` only for scratch stores, tests, controlled refreshes, or intentional replacement.
- Record selected `collection_names` explicitly instead of migrating all collections when the destination contains unrelated data.

## Local Versus Remote Count Assertion

Symptoms:

- Migration finishes uploads but raises an assertion that source and destination vector counts are not equal.
- Local-to-local migration passes, but server migration fails under concurrent writes.
- Counts match later after a delay for non-migration uploads.

Likely causes:

- Migration asserts `source_client.count(collection).count == dest_client.count(collection).count` after upload.
- Source collections changed while migration was scrolling.
- Destination upload failed partway through because of service limits, timeout, or transport errors.
- A normal bulk upload used `wait=False`, so immediate count reads raced server-side application. Migration itself uses `wait=True` for its upload calls.

Fixes:

- Pause writes to selected source collections during migration.
- Use a stable source snapshot or local persistent copy for repeatable migrations.
- Lower migration `batch_size` and increase destination client `timeout` for remote services.
- For non-migration upload validation, call upload with `wait=True` or poll `count` until the expected count appears.
- Compare a small sample of ids and payloads with `scroll(..., with_vectors=True)` when counts match but content correctness is still uncertain.

## Missing Source Collections

Symptoms:

- Migration raises an `AssertionError` that the source client does not have selected collections.

Likely causes:

- `collection_names` contains a typo or a collection that exists only on the destination.
- The source client points at a different local path, server, database prefix, or Cloud cluster than expected.

Fixes:

- Run `[c.name for c in source_client.get_collections().collections]` before migration.
- Verify local path versus `:memory:` selection in `local-mode`.
- Verify remote `url`, `host`, `port`, `prefix`, and credentials in `connection-and-transport`.
