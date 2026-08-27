# IO and checkpoint troubleshooting

Use the smallest reproducer that preserves coordinate order, dtype, and store
geometry. First validate the store with the bundled tiny smoke script; then
classify the failure below. Do not delete a persistent output or checkpoint
until the required slices and manifests have been copied or intentionally
classified as disposable.

## Store and coordinate failures

### `Coordinate dimension ... not in ... store`

**Cause:** `write` or `read` supplied a dimension that was not initialized, or
the reopened store has a different schema.

**Recovery:** inspect `list(io)`/`io.coords`, compare ordered keys and values,
then recreate the exact complete schema with `add_array` or use a new output
store. Do not silently append a dimension with a different meaning to an
existing forecast.

### `Non-index coordinate ... must match the complete coordinate system`

**Cause:** Async Zarr received a sliced coordinate outside `parallel_coords`.

**Recovery:** pass the full non-parallel coordinate array on every write, or put
the iterated dimension in `parallel_coords` with its complete value set at
construction. Do not work around this by changing chunk sizes after arrays
exist.

### `parallel_coords` mismatch, duplicate, or missing value

**Cause:** values are not unique, a write contains a value absent from the
constructor's complete index, or a reopened store has different index values.

**Recovery:** reopen with the exact stored arrays, including dtype/time unit
normalization. If the desired coordinate set is genuinely different, use a new
store and a new checkpoint identity. Do not pass a subset merely because only
that subset is being resumed.

### Multidimensional coordinate shape assertion

**Cause:** a mesh coordinate was sliced or omitted while writing/reading.

**Recovery:** supply the full stored multidimensional coordinate with the same
shape, or convert the problem to explicit one-dimensional coordinates before
initialization. A partial mesh coordinate cannot be safely indexed by these
backends.

### Wrong values after a partial write

**Cause:** tensor axes do not follow coordinate insertion order, coordinate
values are duplicated, or the selected coordinate subset has a different order
than the tensor slice.

**Recovery:** print each coordinate name, length, dtype, and selected indices;
assert the tensor shape equals the selected lengths; perform a one-cell write
with recognizable values. Use `split_coords` when variable names were intended
to be arrays. Never rely on positional indexing alone.

## Async, chunk, and shard failures

### Data is missing after `blocking=False`

**Cause:** the process read or exited before background futures and shard buffers
were drained.

**Recovery:** call `io.close()` exactly at the end of the writer, or `io.flush()`
when continuing. If a future failed, `flush`/`close` surfaces the first error;
fix that root error before rerunning. `__getitem__` may flush for inspection but
is not a replacement for explicit lifecycle management.

### `Shard size ... must be a multiple of ... chunk size`

**Cause:** `shard_coords[k] % chunk_size[k] != 0`.

**Recovery:** choose a shard size that is a positive multiple of the effective
chunk size, or remove the shard setting. For non-parallel coordinates, use a
shard at least as large as the full dimension or make that coordinate parallel.
Recreate the store if the array already exists with incompatible geometry.

### Memory growth, slow flush, or timeout while sharding

**Cause:** shard buffers and codec copies can be several times the logical shard
size; too many flushes may be in flight, or the store is slower than the model.

**Recovery:** lower `shard_coords` and/or `max_inflight_shards`, lower
`pool_size`, use smaller non-parallel chunks, or choose a faster/compressed
layout. Increase `async_timeout` only after checking memory and store
throughput. Measure representative data rather than assuming the largest shard
is fastest.

### Previous data disappears after a multi-process sharded run

**Cause:** two ranks owned different chunks of the same shard. Each rank flushed
a complete shard and the later write won; this is not detected.

**Recovery:** treat the affected shard values as unreliable, map process-owned
indices to shard boundaries, and rerun into a new store with shards aligned to
one rank's complete ownership (usually shard along a per-rank `lead_time`
dimension). Do not expect read-modify-write to repair simultaneous cross-rank
ownership.

### Restarted Async Zarr run warns about read-modify-write

**Cause:** `close()`/`flush()` emitted an incomplete shard, or a prior run left a
shard object in the store. A fresh backend detects the object and merges new
chunks to avoid clobbering old values.

**Recovery:** this is safe if one writer owns the shard and coordinates/geometries
match. Validate both the old and new slices. For the fast path, stop and resume
at shard boundaries or choose a shard size matching restart units. Never let two
processes merge the same shard concurrently.

### `store_kwargs` or writable-store error

**Cause:** `store_kwargs` was supplied for a local path/store instance, or the
provided Zarr store is read-only.

**Recovery:** use `store_kwargs` only with a URL string such as `s3://...`, or
configure the store instance before passing it. Supply a writable store. Keep
credentials in the runtime environment and verify access with a tiny temporary
fixture before the full run.

### Existing array is invisible after metadata consolidation

**Cause:** Async Zarr requires live store membership for lookups and creation;
a stale consolidated snapshot can hide arrays created since consolidation.

**Recovery:** reopen through the backend's live metadata path, do not set a
consolidated mode for live creation, and consolidate only after all writes are
complete. If the store was externally modified, compare its live arrays and
coordinate metadata before continuing.

## Checkpoint failures and restart diagnosis

### `select(-1)` raises `IndexError`

**Cause:** the checkpoint path/name has no committed rows, the wrong path was
opened, or a previous `flush_interval=None` session was never flushed.

**Recovery:** inspect `checkpoint.path`, `checkpoint.catalog`, and the run's
process logs. Use `with checkpoint` for a new run, or recover the original path
and explicitly call `flush` after a safe boundary. Do not fabricate a row from
an IO store without verifying its last complete write.

### Checkpoint says complete but output slice is absent

**Cause:** custom code called `ckpt.write` before `io.write` completed, or a
non-blocking Async Zarr writer was not flushed before checkpointing.

**Recovery:** enforce IO-write-then-checkpoint ordering and close/flush Async
Zarr before the durable checkpoint boundary. Compare checkpoint lead time with
actual stored coordinate values and rebuild the checkpoint if metadata is ahead
of data.

### Level 0/1 reruns instead of continuing the rollout

**Cause:** built-in deterministic/diagnostic workflows intentionally do not
assume component state is sufficient below level 2.

**Recovery:** accept the rerun if deterministic recomputation is valid, or use
level 2 with a checkpoint-aware model/component. Confirm that the component
actually binds/restores state; changing the level alone cannot add support.

### State does not restore or constructor sees defaults

**Cause:** the component was constructed before `with checkpoint.select(-1)`
activated the existing session, or it is not checkpoint-aware.

**Recovery:** construct restartable components inside the selected context. Check
`state.checkpoint_state_loaded`, `state.checkpoint_level`, and the selected row
metadata. A late-adopted state can warn and cannot replay constructor side
effects.

### `CheckpointStateCollision` or `CheckpointStateSchemaError`

**Cause:** two components bound the same fully qualified dataclass state type, or
the current dataclass fields/types/default schema differ from the saved state.

**Recovery:** use distinct dataclass types for distinct components and keep a
stable schema. To intentionally change schema, start a new checkpoint identity
and validate the new run; do not bypass the error by editing manifests.

### `CheckpointSerializationError`

**Cause:** metadata/state contains an unsupported object, an object-dtype array,
or a dictionary with non-string keys.

**Recovery:** store small primitive metadata or supported arrays/tensors, and
keep large forecast fields in IO. Convert object arrays to a non-object dtype or
serialize a supported representation explicitly.

## Synthetic hard case: partial shard plus checkpoint

To diagnose a coupled failure, use a tiny `lead_time` axis of eight values and
`shard_coords={"lead_time": 4}`:

1. Write indices 0–5 to a fresh `AsyncZarrBackend`, call `close()`, and record a
   checkpoint only after close/flush.
2. Reopen both stores in a new backend with the identical complete
   `parallel_coords` and checkpoint `select(-1)`.
3. Write indices 6–7, close, and assert indices 0–7 equal the source fixture.
4. Repeat with two writers whose ownership splits a four-index shard; confirm
   that the unsafe layout is rejected by review even if one run appears correct.

This case tests partial-shard merge, coordinate identity, explicit lifecycle,
and the fact that checkpoint metadata cannot repair cross-process shard
ownership. It belongs in verification planning, not in the runtime skill's
persistent output directory.
