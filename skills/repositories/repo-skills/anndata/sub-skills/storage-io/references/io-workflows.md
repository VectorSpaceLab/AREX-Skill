# Storage I/O Workflows

These workflows assume `import anndata as ad` and use public APIs unless explicitly marked experimental.

## Choose H5AD Or Zarr

Use `.h5ad` when:

- A single local file is easiest to move, archive, or hand to another tool.
- HDF5 backed mode is needed with `read_h5ad(..., backed="r")`.
- Downstream tools expect H5AD specifically.
- You want simple local round-trips without directory-store management.

Use Zarr when:

- Data is naturally a directory, mapping, or object-store hierarchy.
- Chunking, sharding, codecs, or cloud-style access matter.
- `experimental.read_lazy` should read arrays and dataframes with dask/xarray-style backing.
- Many workers need independent chunk reads and the store metadata is consolidated.

Validation rule: write a tiny or sampled store first, re-read it in the same environment, and verify shape/names/key expectations before scaling up.

## Full H5AD Read/Write

```python
import anndata as ad

adata.write_h5ad("output.h5ad", compression="lzf")
copy = ad.read_h5ad("output.h5ad")
assert copy.shape == adata.shape
```

Compression guidance:

- `compression=None`: fastest baseline and broad compatibility.
- `compression="lzf"`: fast built-in HDF5 compression.
- `compression="gzip"`: often smaller output but slower read/write.
- Custom HDF5 filters require plugin availability in every reader environment; avoid them for shared files unless the dependency is controlled.

Sparse-to-dense compatibility:

```python
adata.write_h5ad("dense-X.h5ad", as_dense=("X",))
```

Only `"X"` and `"raw/X"` are valid for H5AD `as_dense`.

## Read Dense-Stored H5AD `X` As Sparse

Use this only when a dense on-disk `X` should become sparse in memory:

```python
from scipy import sparse
import anndata as ad

adata = ad.read_h5ad(
    "dense-X.h5ad",
    as_sparse=("X",),
    as_sparse_fmt=sparse.csr_matrix,
    chunk_size=6000,
)
assert sparse.issparse(adata.X)
```

- Only `"X"` and `"raw/X"` are supported.
- Use CSR for row-oriented access and CSC for column-oriented access.
- Decrease `chunk_size` under memory pressure; increase it for speed when memory allows.

## H5AD Backed Mode

Use backed mode for low-memory inspection or limited `X` updates.

Read-only:

```python
import anndata as ad

adata = ad.read_h5ad("large.h5ad", backed="r")
try:
    print(adata.shape)
    print(adata.X[:10, :10])
finally:
    adata.file.close()
```

Mutable `X` updates:

```python
adata = ad.read_h5ad("large.h5ad", backed="r+")
try:
    adata.X[0, 0] = 0
finally:
    adata.file.close()
```

Do not rely on backed mode to persist arbitrary metadata changes. For `obs`, `var`, `layers`, or `uns` edits:

```python
backed = ad.read_h5ad("large.h5ad", backed="r")
try:
    in_memory = backed.to_memory()
finally:
    backed.file.close()

in_memory.obs["batch"] = "A"
in_memory.write_h5ad("large-with-batch.h5ad")
```

## Full Zarr Read/Write

```python
import anndata as ad

adata.write_zarr("output.zarr", chunks=(1024, adata.n_vars))
copy = ad.read_zarr("output.zarr")
assert copy.shape == adata.shape
```

- `chunks` affects dense `X`; sparse matrices use sparse group encoding.
- Current writes consolidate metadata by default.
- Use Zarr v3 by default unless downstream consumers require v2.
- Use `with ad.settings.override(zarr_write_format=2): ...` only for a documented compatibility need.

## Mutate A Zarr Store After Consolidated Write

Consolidated metadata makes reads faster and is default for current AnnData writes, but it makes structural mutations require care. The safe sequence is:

```python
import zarr
import anndata as ad

group = zarr.open_group("output.zarr", mode="a", use_consolidated=False)
ad.io.write_elem(group["obs"], "quality_score", quality_score_array)
zarr.consolidate_metadata(group.store)
check = ad.read_zarr("output.zarr")
assert "quality_score" in check.obs
```

If opening or writing fails with a consolidated metadata message, do not patch random metadata files by hand. Reopen unconsolidated, perform the edit, reconsolidate, and re-read.

## Zarr V3 Sharding And Compressors

Default settings observed for the inspected runtime:

```python
ad.settings.zarr_write_format       # 3
ad.settings.auto_shard_zarr_v3      # True
```

Guidance:

- Leave `auto_shard_zarr_v3=True` for ordinary v3 writes unless a benchmark or downstream constraint says otherwise.
- Explicit `shards` in lower-level `dataset_kwargs` override automatic sharding.
- Use `experimental.write_dispatched` when different elements need different sharding/chunking choices.
- Zarr v3 default codec behavior may differ from older v2/blosc expectations; pass a compressor only when the selected Zarr version and downstream readers support it.
- For Zarr v3, Zarr APIs may use `compressors` internally even when higher-level examples speak about a single compressor.

Tiny custom chunking with dispatched write:

```python
import zarr
import anndata as ad

root = zarr.open_group("custom.zarr", mode="w", zarr_format=3)

def callback(write_func, store, key, elem, *, dataset_kwargs, iospec):
    if hasattr(elem, "shape") and iospec.encoding_type == "array":
        dataset_kwargs = {**dataset_kwargs, "chunks": tuple(min(128, s) for s in elem.shape)}
    write_func(store, key, elem, dataset_kwargs=dataset_kwargs)

ad.experimental.write_dispatched(root, "/", adata, callback=callback)
zarr.consolidate_metadata(root.store)
```

Treat this as experimental and validate with a small store before applying it to production data.

## Lazy Reads

Use lazy reads when eager reads would load too much data or when remote/object-store access benefits from chunked/lazy arrays.

H5AD path:

```python
import anndata as ad

adata = ad.experimental.read_lazy("large.h5ad")
try:
    print(adata.shape, type(adata.X))
finally:
    if getattr(adata, "isbacked", False):
        adata.file.close()
```

Explicit HDF5 file lifetime:

```python
import h5py
import anndata as ad

with h5py.File("large.h5ad", "r") as handle:
    adata = ad.experimental.read_lazy(handle)
    print(adata.X[:10, :10])
```

Zarr:

```python
adata = ad.experimental.read_lazy("large.zarr", load_annotation_index=False)
print(adata.shape)
```

Notes:

- `read_lazy` is experimental and requires lazy dependencies.
- For H5AD path inputs, the returned object owns an open HDF5 file handle.
- For Zarr, consolidated metadata is strongly preferred. Unconsolidated reads may warn, be slower, or be incomplete for remote stores.
- `load_annotation_index=False` avoids loading real `obs`/`var` indexes immediately; expect range-like dataframe indexes until materialized.
- Lazy AnnData objects containing `Dataset2D` components may not be writable directly; convert those components or the object to memory before writing.

## Read One Element

Read just annotations from H5AD:

```python
import h5py
import anndata as ad

with h5py.File("input.h5ad", "r") as handle:
    obs = ad.io.read_elem(handle["obs"])
    var = ad.io.read_elem(handle["var"])
print(obs.shape, var.shape)
```

Read a Zarr layer:

```python
import zarr
import anndata as ad

group = zarr.open("input.zarr", mode="r")
counts = ad.io.read_elem(group["layers/counts"])
```

Read one element lazily:

```python
X = ad.experimental.read_elem_lazy(group["X"], chunks=(500, None))
```

For sparse arrays, keep the minor axis whole: CSR chunks look like `(rows_per_chunk, n_vars)` and CSC chunks look like `(n_obs, cols_per_chunk)`.

## Write One Element

Write a DataFrame or array into a scratch store:

```python
import h5py
import anndata as ad

with h5py.File("scratch.h5", "w") as handle:
    ad.io.write_elem(handle, "obs", adata.obs)
```

Write into Zarr after a whole-store write:

```python
import zarr
import anndata as ad

group = zarr.open_group("input.zarr", mode="a", use_consolidated=False)
ad.io.write_elem(group["obs"], "quality_score", adata.obs["quality_score"].to_numpy())
zarr.consolidate_metadata(group.store)
```

Use `k="/"` only when writing an object directly into the current root group.

## Sparse On-Disk Dataset Workflow

```python
import h5py
import anndata as ad

with h5py.File("input.h5ad", "r") as handle:
    X = ad.io.sparse_dataset(handle["X"])
    print(X.shape, X.dtype)
    block = X[:100, :]
```

Load fully only after confirming it fits:

```python
full = X.to_memory()
```

Append rules:

- CSR appends along rows; the number of columns must match.
- CSC appends along columns; the number of rows must match.
- Formats must match (`csr` to `csr`, `csc` to `csc`).
- The target store must be writable and not a consolidated Zarr group opened as consolidated.

## Convert Between H5AD And Zarr

H5AD to Zarr:

```python
adata = ad.read_h5ad("input.h5ad")
adata.write_zarr("output.zarr", chunks=(1024, adata.n_vars))
assert ad.read_zarr("output.zarr").shape == adata.shape
```

Zarr to H5AD:

```python
adata = ad.read_zarr("input.zarr")
adata.write_h5ad("output.h5ad", compression="lzf")
assert ad.read_h5ad("output.h5ad").shape == adata.shape
```

For large data, consider whether a full eager conversion is acceptable. If not, route the higher-level multi-file or out-of-core plan to `../combining-data/SKILL.md` and keep this sub-skill focused on store readability and output validation.

## Prepare Storage For `concat_on_disk`

Before `anndata.experimental.concat_on_disk`:

- Confirm each input path/group is readable by `read_h5ad`, `read_zarr`, or `experimental.read_lazy` depending on the intended path.
- Confirm every input has valid `obs` and `var` and no partially written store structure.
- For Zarr inputs, avoid stale consolidated metadata; reconsolidate after any manual edits.
- Confirm the output parent exists and the output target can be created fresh.
- Decide output format and chunking before concatenation; use Zarr for large chunked outputs and H5AD for a single file.

After `concat_on_disk`, validate the output shape, expected `obs` labels, and selected keys with a readback.

## Choose Low-Memory Access Mode

Use full read when:

- The dataset fits in memory.
- You need to modify many slots and write a new complete file.
- You need maximum API compatibility with ordinary in-memory AnnData operations.

Use `read_h5ad(backed="r")` when:

- The source is H5AD.
- You need quick shape/key inspection or slices of `X`.
- You do not need to persist metadata edits in place.
- You can close the file promptly.

Use `experimental.read_lazy` when:

- The source is Zarr, remote-like, or too large for eager read.
- The workflow can handle dask/xarray-backed arrays/dataframes.
- Optional lazy dependencies are installed.
- You can validate any materialization boundary with `.to_memory()` on a subset first.
