# Dask Array Workflows

## Wrap Existing NumPy-Like Storage

Use `da.from_array` when the source exposes `shape`, `ndim`, `dtype`, and NumPy-style slicing.

```python
import dask.array as da

x = da.from_array(storage, chunks=(1000, 1000))
```

Checklist:

- Align Dask chunks with storage chunks or an integer multiple of storage chunks.
- Avoid tiny Dask chunks; many workflows work best with tens to hundreds of MB per chunk.
- Use `lock=True` or an explicit lock if a storage object is not thread-safe.
- Use `meta=` for non-NumPy chunk types or when type inference would be wrong.
- Keep the source object lifetime valid until computation finishes.

## Build Arrays from Files or Delayed Pieces

Use `from_delayed` when each piece is naturally loaded by a delayed function and exact piece metadata is known.

```python
import dask
import dask.array as da

lazy_piece = dask.delayed(load_one_array)(path)
piece = da.from_delayed(lazy_piece, shape=(512, 512), dtype="float32")
stack = da.stack([piece], axis=0)
```

For regular stacks, consider `map_blocks` with `block_id` so each block reads its own file or tile. That avoids creating long Python lists of delayed arrays for large regular datasets.

## Slice and Index Efficiently

Dask computes only needed blocks for slices, so slicing can be cheap even after lazy elementwise operations. Keep these constraints in mind:

- Supported: integers, slices, one-axis integer lists/arrays, one-axis boolean lists/arrays, Dask boolean masks, and 0-D/1-D Dask integer indexers.
- Limited: lists in multiple axes and multidimensional Dask integer indexers.
- Unknown chunks block many slicing operations; resolve with `compute_chunk_sizes()` only when acceptable.
- Repeated fancy indices can create oversized output chunks; control behavior with `array.slicing.split_large_chunks` configuration.

## Use Reductions Rather Than Manual Axis Drops

Prefer built-in reductions for `sum`, `mean`, `std`, `var`, `min`, `max`, `arg*`, `nan*`, percentile-like operations, and top-k. Built-ins preserve lazy graph structure and avoid materializing a whole dropped axis inside one `map_blocks` call.

```python
result = x.mean(axis=0)
```

If implementing a custom reduction, use `dask.array.reduction` or `blockwise` rather than `map_blocks(..., drop_axis=...)` on large chunked axes.

## Apply Simple Block Functions with `map_blocks`

Use `map_blocks` when each output block corresponds to one block position from one or more inputs.

```python
import numpy as np
import dask.array as da

x = da.arange(12, chunks=4)
y = x.map_blocks(lambda block: block.reshape(2, -1), dtype=x.dtype, chunks=(2, 2), new_axis=0)
```

Rules of thumb:

- Always provide `dtype` for public recipes.
- Provide `chunks` whenever block shape changes.
- Use `new_axis` for inserted dimensions and `drop_axis` for removed dimensions, but avoid `drop_axis` on heavily chunked axes.
- Set `enforce_ndim=True` while debugging shape-changing functions.
- Provide `meta=` if the function fails on Dask's fake 0-D inference input or returns a non-NumPy chunk type.
- Accept `block_info=None` or `block_id=None` in the function when block location determines file names, coordinates, or boundary behavior.

## Use `blockwise` for Indexed Block Algebra

Use `blockwise` when block relationships are clearer as labeled indices:

```python
import operator
import dask.array as da

z = da.blockwise(operator.add, "ij", x, "ij", y, "ij", dtype=x.dtype)
```

Patterns:

- Output labels define block layout.
- Input labels missing from output labels are contractions.
- `new_axes={"z": 5}` adds an output dimension.
- `adjust_chunks={"i": lambda n: 2 * n}` updates chunk sizes when a function changes block lengths.
- `align_arrays=True` allows Dask to split chunks so inputs align; set it to `False` only when pre-aligned arrays are required.

## Add Overlap for Stencils and Local Filters

Use `map_overlap` for filters, rolling windows, derivatives, image morphology, and simulations requiring halo data.

```python
import numpy as np
import dask.array as da

x = da.arange(64).reshape(8, 8).rechunk((4, 4))
y = x.map_overlap(lambda block: block - np.roll(block, 1, axis=0), depth={0: 1, 1: 0}, boundary=0)
```

Planning steps:

- Choose chunk sizes larger than `2 * depth` along overlapped axes when possible.
- Choose `boundary` per axis: `reflect`, `periodic`, `nearest`, `none`, or a constant such as `0` or `np.nan`.
- Keep `trim=True` unless the function already removes halo cells.
- If `depth` exceeds chunk sizes, Dask may rechunk when `allow_rechunk=True`; otherwise the workflow can fail.
- For asymmetric depth, use tuple values and `boundary="none"`.

## Change Chunk Layout with `rechunk`

Use `rechunk` when downstream operations need a different layout, not as a default reflex.

```python
x2 = x.rechunk({0: -1, 1: "auto"}, block_size_limit="128MiB")
```

Guidance:

- `-1` means one chunk along an axis and can be memory-heavy.
- Dict syntax changes only selected axes.
- `balance=True` can avoid tiny final chunks.
- Large cross-axis rechunks may create large intermediate graphs or communication; prefer staged rechunks for big layout changes.
- In distributed contexts, Dask may choose peer-to-peer rechunking when available and graph size justifies it.

## Wrap Generalized UFuncs

Use `apply_gufunc` when a function consumes or produces core dimensions described by a NumPy gufunc signature.

```python
import numpy as np
import dask.array as da

def stats(block):
    return np.mean(block, axis=-1), np.std(block, axis=-1)

mean, std = da.apply_gufunc(stats, "(i)->(),()", x, output_dtypes=(float, float))
```

Checklist:

- Put core dimensions in single chunks, or pass `allow_rechunk=True` only after considering memory growth.
- Use `output_dtypes=` or `meta=`; `meta` is preferred when output chunk type matters.
- Use `output_sizes=` when new core dimensions appear in outputs.
- Use `vectorize=True` only when the Python function itself does not broadcast over loop dimensions.

## Use Random, Linalg, FFT, and Stats

- Random: create a generator with `da.random.default_rng()` and pass both `size` and `chunks`.
- Linalg: Dask implements useful but incomplete NumPy linear algebra. Check chunk structure, especially for factorizations and solves.
- FFT: use `da.fft` for chunked FFT workflows and verify axis/chunk constraints on transformed dimensions.
- Stats: use `da.stats` for statistical functions backed by Dask Array.

## Optional Backends

Dask Array can coordinate NumPy-like chunks such as CuPy or sparse arrays. Keep backend workflows conditional:

- Confirm the package and hardware exist before using CuPy, image, TileDB, or sparse-specific examples.
- Use `meta=` with an empty backend array so `map_blocks`, `map_overlap`, or gufunc outputs keep the intended chunk type.
- Register custom chunk types when extending Dask to new duck arrays.
- Do not promise every NumPy operation works on every backend; Dask delegates much behavior to the chunk library.

## Geospatial-Like Overlap and Rechunk Planning Case

For a 2D raster or geospatial tile workflow:

1. Inspect source storage chunks, e.g. `(256, 256)`.
2. Pick Dask chunks that are multiples of storage chunks and large enough for work, e.g. `(1024, 1024)` or `(2048, 1024)` depending on memory.
3. Ensure stencil depth is small relative to chunks, e.g. `depth={0: 8, 1: 8}` with reflective or constant boundaries.
4. Apply `map_overlap` for the local filter.
5. Rechunk only if the next workflow changes orientation, such as column-wise statistics or writing to a target store with a different chunk grid.
6. Estimate memory before `rechunk({0: -1})` or other single-axis consolidation.
