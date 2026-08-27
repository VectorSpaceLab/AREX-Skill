# Chunking and Performance

## Chunk Forms

Dask normalizes chunk specifications into explicit tuples per dimension.

| Input form | Meaning |
| --- | --- |
| `chunks=1000` | Uniform size in each dimension. |
| `chunks=(1000, 2000)` | Uniform block shape per axis. |
| `chunks=((1000, 1000, 500), (400, 400))` | Fully explicit block sizes. |
| `chunks={0: 1000, 1: 2000}` | Per-axis specification, often used for rechunking. |
| `chunks="auto"` | Dask chooses chunks using configuration and source hints. |
| `-1` in rechunk specs | One chunk spanning the full dimension. |

`chunks` means chunk shape, not number of chunks. For example, `chunks=1` creates one-element chunks and usually too many tasks.

## Chunk Selection Heuristics

Prefer chunks that satisfy all of these:

- Fit comfortably in worker memory with multiple active chunks at once.
- Are large enough that per-task compute time dominates scheduler overhead.
- Often fall in the tens-of-MB to 1-GB range depending on workload and memory; Dask docs note chunk sizes below 100 MB are often too small for array workloads.
- Align with the computation: thin chunks for frequent thin slicing, symmetric chunks for many 2D local operations, single/full chunks only when an algorithm requires them.
- Align with storage chunks or integer multiples of storage chunk dimensions to avoid repeated reads.
- Match chunks across arrays that are combined frequently.

## Storage Alignment

When loading from chunked storage such as HDF5, NetCDF, TIFF, or Zarr, inspect the storage chunk shape. If storage chunks are `(128, 64)`, a Dask chunk shape like `(1280, 6400)` preserves alignment while reducing scheduler overhead. If Dask chunks are not multiples of storage chunks, reads can repeat or fragment IO.

`chunks="auto"` may use a source object's `.chunks` attribute as a hint, but still validate the result against the intended workload.

## Unknown Chunks

Unknown chunks arise when array sizes depend on lazy computations, such as boolean filtering:

```python
y = x[x > 0]
```

Symptoms:

- `shape` or `chunks` contains `np.nan`.
- Slicing or shape-sensitive operations raise errors about unknown chunk sizes.

Fix options:

- For Dask Array, call `x.compute_chunk_sizes()` only when immediate computation is acceptable. It computes chunk lengths and mutates the array in place.
- For Dask DataFrame conversion, prefer `ddf.to_dask_array(lengths=True)` if row counts are needed and the cost is acceptable.
- Avoid operations requiring known chunks until after filtering is finalized.

## Rechunk Cost

Rechunking changes block layout but not array shape. It can be cheap along one axis and expensive when every old chunk intersects many new chunks.

Planning checklist:

- Inspect `x.chunks` and desired chunks before calling `rechunk`.
- Avoid unnecessary cross-axis reshuffles.
- Use staged rechunking for large old-to-new layout changes.
- Use `block_size_limit` or `array.chunk-size` to cap automatic chunks.
- Use `balance=True` when small leftover chunks harm downstream work.
- Treat `method="p2p"` as a distributed workflow feature; local workflows normally use task-based rechunking.

## Slicing Chunk Warnings

Repeated fancy indexing can create output chunks much larger than input chunks. Dask warns when indexing produces chunks much larger than the `array.chunk-size` config option.

- Set `array.slicing.split_large_chunks=True` to split large output chunks.
- Set `array.slicing.split_large_chunks=False` to accept the large chunks and silence the warning.
- Choose based on downstream memory pressure and whether large contiguous chunks are beneficial.

## `map_blocks` Shape and Metadata Inference

`map_blocks` tries to infer output dtype/type by running the function on fake 0-D data. This can fail for functions that expect dimensional arrays, backend-specific arrays, or nontrivial metadata.

Stabilize recipes by specifying:

- `dtype=` for output dtype.
- `chunks=` for changed block shape.
- `new_axis=` or `drop_axis=` for dimension changes.
- `meta=` as an empty representative array for output chunk type.
- `enforce_ndim=True` during debugging to catch shape mismatch at compute time.

## `map_blocks` Versus `blockwise`

Use `map_blocks` for one-output-block-per-input-block-position workflows. Use `blockwise` when the relationship is tensor-indexed, needs contractions, needs explicit new axes, or needs chunk-size adjustment by index label.

`map_blocks` aligns by `numblocks`, not physical chunk sizes. Inputs with the same number of blocks can be paired even if their block shapes differ.

## Overlap Performance

`map_overlap` expands each chunk by halo depth, runs the function, then trims by default. Overlap increases memory and communication.

- Keep chunks much larger than halo depth.
- Avoid depth larger than chunk size unless rechunking is acceptable.
- Use per-axis depths and boundaries to avoid unnecessary halo growth.
- Set `trim=False` only when the function handles trimming itself.

## Query Planning Caveat

`array.query-planning` controls the experimental array expression implementation. The flag is import-time sensitive: set it before importing `dask.array` in a fresh Python process. If a session already imported `dask.array`, restart before changing the flag.
