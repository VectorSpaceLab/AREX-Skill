# Dask Array API Reference

## Collection Basics

| API | Use for | Notes |
| --- | --- | --- |
| `dask.array.Array` | Lazy blocked ndarray-like collection | Carries `shape`, `dtype`, `chunks`, `numblocks`, and graph metadata. Computation happens only through explicit collection execution such as `compute()`. |
| `da.asarray`, `da.asanyarray` | Convert compatible array-like objects | Useful when mixed NumPy/Dask operations should become lazy Dask arrays. |
| `da.from_array(x, chunks="auto", name=None, lock=False, asarray=None, fancy=True, getitem=None, meta=None, inline_array=False)` | Wrap NumPy-like storage with `shape`, `ndim`, `dtype`, and slicing | Lazy wrapper for HDF5, Zarr, NetCDF, memory arrays, and duck arrays. Choose chunks deliberately; `chunks="auto"` uses Dask config and may inspect storage chunk hints. |
| `da.from_delayed`, `da.stack`, `da.concatenate` | Build arrays from delayed pieces or multiple arrays | Provide exact `shape` and `dtype` for delayed pieces. Prefer `map_blocks` for regularly indexed file stacks when possible. |
| `da.store` | Write array chunks into mutable targets | For IO workflows; coordinate with storage backend chunking and scheduler choice. |

## Creation and Random

| API family | Use for | Notes |
| --- | --- | --- |
| `da.arange`, `da.linspace`, `da.ones`, `da.zeros`, `da.empty`, `da.full` | Synthetic and initialized arrays | Always provide explicit `chunks` for predictable graphs. |
| `da.ones_like`, `da.zeros_like`, `da.full_like` | Preserve shape/chunks from another array | Override `chunks`, `dtype`, or `shape` when needed. |
| `da.random.default_rng()` and `da.random.*` | Lazy random arrays | Provide `size` and `chunks`. Random chunks are generated lazily and independently. |

## NumPy-Like Operations

| API family | Use for | Notes |
| --- | --- | --- |
| Arithmetic and ufuncs | Elementwise work | Usually maps naturally block-by-block and preserves chunking. |
| Slicing and fancy indexing | Select subsets lazily | Integer/slice/list/boolean indexing is supported, but lists in multiple axes and multidimensional Dask integer indexers are limited. Repeated indices can create large output chunks. |
| Reductions: `sum`, `mean`, `std`, `var`, `min`, `max`, `arg*`, `nan*`, `percentile`, `topk` | Aggregate along axes | Prefer reductions over `map_blocks(..., drop_axis=...)` when dropping a chunked axis because reductions avoid concatenating a whole axis into each block function call. |
| `da.linalg`, `da.fft`, `da.stats` | Linear algebra, FFT, and statistical functions | Coverage is broad but not complete NumPy parity. Check shape/chunk requirements before promising a function is supported. |

## Custom Blocked Algorithms

| API | Use for | Key parameters |
| --- | --- | --- |
| `da.map_blocks(func, *args, dtype=None, chunks=None, drop_axis=None, new_axis=None, enforce_ndim=False, meta=None, **kwargs)` | Apply a Python/NumPy function independently to matching block positions | Provide `dtype`; provide `chunks`, `drop_axis`, and `new_axis` when shape changes; provide `meta` when 0-D inference fails or when output chunk type is non-NumPy. `block_info` and `block_id` can be accepted by `func`. |
| `da.blockwise(func, out_ind, *args, dtype=None, adjust_chunks=None, new_axes=None, align_arrays=True, concatenate=None, meta=None, **kwargs)` | Express tensor/block index operations with explicit index labels | Use for generalized elementwise, broadcasting, transpose, contractions, tensor products, and custom chunk alignment. Missing input indices in `out_ind` are contractions. |
| `da.map_overlap(func, *args, depth=None, boundary=None, trim=True, align_arrays=True, allow_rechunk=True, **kwargs)` | Apply local stencil/filter operations needing neighboring borders | `depth` controls halo width; `boundary` supports values like `reflect`, `periodic`, `nearest`, `none`, or constants; `allow_rechunk` may be required when depth exceeds chunk size. |
| `da.overlap.overlap` and `da.overlap.trim_internal` | Manual halo expansion and trimming | Use when a workflow needs explicit control instead of the one-shot `map_overlap`. |
| `da.apply_gufunc(func, signature, *args, axes=None, axis=None, keepdims=False, output_dtypes=None, output_sizes=None, vectorize=None, allow_rechunk=False, meta=None, **kwargs)` | Wrap generalized ufunc-like operations over core dimensions | Core dimensions must usually be contained in single chunks unless `allow_rechunk=True`, which can increase memory significantly. Prefer `meta` or `output_dtypes` to avoid inference surprises. |
| `da.gufunc`, `da.as_gufunc` | Reusable generalized ufunc wrappers/decorators | Dask wrappers are experimental and do not create true NumPy generalized ufuncs for non-Dask arrays. |

## Chunk and Rechunk APIs

| API | Use for | Notes |
| --- | --- | --- |
| `x.chunks`, `x.chunksize`, `x.numblocks` | Inspect block layout | `chunks` is normalized as explicit tuples per dimension. `numblocks` is often the compatibility check for `map_blocks`. |
| `x.rechunk(chunks="auto", threshold=None, block_size_limit=None, balance=False, method=None)` / `da.rechunk` | Change block layout without changing shape | `-1` means a single chunk along that dimension; dicts can target selected axes; `balance=True` can remove tiny leftovers; `method` can be `tasks` or `p2p` when distributed support is available. |
| `x.compute_chunk_sizes()` | Resolve unknown chunks | Performs immediate computation and mutates the array in place. Use only when the workflow truly needs known chunks for operations like slicing. |
| `da.core.normalize_chunks`, `da.core.unify_chunks` | Internal/advanced planning utilities | Useful as evidence for how Dask normalizes chunks and aligns arrays, but most user workflows should call public array APIs. |

## Backend and Duck Array APIs

| API | Use for | Notes |
| --- | --- | --- |
| `da.register_chunk_type` | Register new duck array chunk types | Helps Dask understand NumPy-like chunk implementations. |
| `meta=` parameters | Preserve output chunk type | Use empty arrays such as `np.array((), dtype=...)`, sparse empty arrays, or CuPy empty arrays when inference would otherwise choose the wrong backend. |
| CuPy/sparse/image/tiledb integrations | Optional accelerated or specialized chunks/IO | Treat as optional dependency workflows. Provide CPU-only fallbacks unless the user confirms GPU/backend availability. |

## Experimental Array Expression Flag

Dask includes an experimental array expression implementation under `dask.array._array_expr`. The `array.query-planning` configuration flag must be set before importing `dask.array` for a Python process. Do not advise toggling it after `dask.array` has already been imported; start a fresh process with the desired config instead.
