# Dask Array Troubleshooting

## `ValueError: Array chunk sizes unknown`

Likely cause: filtering, dataframe conversion, or another lazy operation produced unknown chunk lengths.

Fix:

1. Inspect `x.shape` and `x.chunks` for `np.nan`.
2. If slicing or shape-sensitive operations are required, call `x.compute_chunk_sizes()` and note that it computes immediately and mutates the array.
3. For dataframe conversion, use `ddf.to_dask_array(lengths=True)` when the row-count computation is acceptable.
4. If exact lengths are not needed, restructure the workflow to delay slicing until after a reduction or write.

## Too Many Tiny Chunks

Symptoms: graph construction is slow, scheduler overhead dominates, dashboard shows many tiny tasks, or simple computations are slower than NumPy.

Fix:

- Increase chunk sizes; avoid `chunks=1` unless intentionally elementwise for a tiny example.
- Align chunks with storage and computations.
- Use `rechunk` sparingly to merge tiny chunks before expensive operations.
- If data fits in RAM and the user does not need scalability, recommend NumPy.

## Chunks Too Large or Worker Memory Spills

Symptoms: workers spill, tasks fail with memory errors, or `rechunk({axis: -1})` produces huge blocks.

Fix:

- Reduce per-chunk byte size using dtype itemsize and chunk shape estimates.
- Avoid full-axis chunks unless required by the algorithm.
- Rechunk in stages and set `block_size_limit`.
- Avoid `allow_rechunk=True` in gufunc/overlap workflows until memory impact is understood.

## `map_blocks` Shape Mismatch

Likely cause: the function changes block shape but `chunks`, `new_axis`, or `drop_axis` was omitted or wrong.

Fix:

1. Run the function on a representative NumPy block to learn output shape and dtype.
2. Pass `dtype=` and explicit `chunks=`.
3. Use `new_axis=` for inserted dimensions and `drop_axis=` for removed dimensions.
4. Use `enforce_ndim=True` while debugging.
5. Prefer `dask.array.reduction` over `drop_axis` when dropping a heavily chunked axis.

## `map_blocks` Metadata or 0-D Inference Failure

Likely cause: Dask called the function on fake 0-D data to infer dtype/type, and the function expects dimensional input or a backend-specific array.

Fix:

- Pass `dtype=` and `meta=` explicitly.
- Use an empty representative output, such as `np.array((), dtype="float32")` for NumPy or an empty CuPy/sparse array for those backends.
- Keep non-Dask keyword arguments constant; do not pass Dask arrays through `**kwargs`.

## `map_blocks` Inputs Pair Unexpected Blocks

Likely cause: `map_blocks` matches block positions by `numblocks`, not by equal physical chunk sizes.

Fix:

- Compare `x.numblocks`, `y.numblocks`, and `x.chunks`, `y.chunks`.
- Rechunk arrays to compatible layouts when physical block sizes must match.
- Use `blockwise` for more explicit index alignment.

## Rechunk Explodes Graph Size or Communication

Likely cause: old chunks and new chunks intersect in many small pieces, often during cross-axis layout changes.

Fix:

- Inspect old and target chunks first.
- Use intermediate staged rechunks.
- Set `block_size_limit` and consider `balance=True`.
- In distributed environments, allow Dask to choose a peer-to-peer rechunk method when available; otherwise expect task-based rechunking.

## `map_overlap` Gives Edge Artifacts

Likely cause: wrong `depth`, wrong `boundary`, or double trimming.

Fix:

- Match `depth` to the algorithm's stencil radius per axis.
- Choose `boundary` deliberately: `reflect`, `periodic`, `nearest`, `none`, or a constant.
- Keep `trim=True` unless the function trims internally.
- For asymmetric depth, use tuple depths with `boundary="none"`.

## Gufunc Core Dimension Errors

Likely cause: core dimensions span multiple chunks or output metadata is incomplete.

Fix:

- Rechunk core dimensions to single chunks, or pass `allow_rechunk=True` only after memory review.
- Provide `output_dtypes=` or `meta=`.
- Provide `output_sizes=` when outputs introduce new core dimensions.
- Confirm the signature describes core dimensions exactly.

## Optional Dependency Failures

Common optional dependencies include CuPy, sparse, image readers, TileDB, HDF5, Zarr, and NetCDF-related packages.

Fix:

- Confirm the package import and hardware/backend availability.
- Keep examples CPU-only unless the user asks for GPU or a specific backend.
- Use `meta=` to preserve backend chunk type.
- Do not treat GPU-only Dask tests as safe local verification unless GPU availability is confirmed.

## `array.query-planning` Seems Ignored

Likely cause: `dask.array` was imported before setting the import-time config flag.

Fix:

- Start a fresh Python process.
- Set `dask.config.set({"array.query-planning": True})` before importing `dask.array`, or use environment/YAML config loaded before import.
- Route config-file and CLI details to `configuration-diagnostics-cli`.

## Synthetic Debug Case: `new_axis` / `drop_axis` / `meta`

When diagnosing a shape-changing `map_blocks` bug:

1. Create a tiny NumPy block with the same ndim as one Dask chunk.
2. Call the user function eagerly and record output `shape`, `dtype`, and chunk type.
3. Translate shape changes into `chunks`, `new_axis`, and `drop_axis`.
4. Pass `meta=` if the eager function cannot run on fake 0-D data.
5. Turn on `enforce_ndim=True` to catch mismatches early.
