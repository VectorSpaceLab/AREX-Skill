# Storage I/O API Reference

Use public `anndata` APIs in user-facing workflows. Avoid private `anndata._io` imports unless debugging AnnData internals.

## Stable Whole-Object Reads

### `anndata.read_h5ad(filename, backed=None, *, as_sparse=(), as_sparse_fmt=csr_matrix, chunk_size=6000)`

Reads an `.h5ad` HDF5 file.

- `backed=None` or `False`: fully materializes the object in memory.
- `backed="r"`: opens read-only backed mode; keep the HDF5 file open while using the returned object.
- `backed="r+"` or `True`: opens mutable backed mode; use only when intentionally updating `X` in place.
- Backed mode currently persists updates to `X`, not arbitrary changes to `obs`, `var`, `layers`, or `uns`; save metadata changes by materializing and writing a new file.
- `as_sparse=("X",)` or `("raw/X",)`: reads dense-stored `X` or `raw/X` as sparse.
- `as_sparse_fmt`: use `scipy.sparse.csr_matrix` or `scipy.sparse.csc_matrix` only.
- `chunk_size`: row chunk size used only for dense-to-sparse reads; larger chunks can speed reads but use more memory.

Safe pattern:

```python
import anndata as ad

adata = ad.read_h5ad("input.h5ad")
assert adata.shape == (adata.n_obs, adata.n_vars)

backed = ad.read_h5ad("input.h5ad", backed="r")
try:
    print(backed.shape, backed.isbacked)
finally:
    backed.file.close()
```

### `anndata.read_zarr(store)`

Reads a hierarchical Zarr store into an in-memory `AnnData` object.

- `store` can be a filesystem path, mutable mapping, or open Zarr group.
- Use an open group when reading a nested AnnData group or when the store abstraction is already configured.
- Zarr does not use H5AD-style `backed` mode; choose `experimental.read_lazy` for low-memory Zarr workflows.
- Current AnnData Zarr reads handle HDF5/Zarr-like encoding metadata and selected backward-compatibility layouts.

Safe pattern:

```python
import anndata as ad

adata = ad.read_zarr("input.zarr")
assert "obs" in adata and "var" in adata
```

## Stable Whole-Object Writes

### `AnnData.write_h5ad(filename=None, *, convert_strings_to_categoricals=True, compression=None, compression_opts=None, as_dense=())`

Writes an AnnData object to `.h5ad`.

- `filename=None` writes to the current backing file only for a backed object; otherwise pass a path.
- `convert_strings_to_categoricals=True` converts string annotation columns to categoricals before writing, including `raw.var` when present.
- `compression=None`, `"lzf"`, and `"gzip"` are common choices; `gzip` usually shrinks files more but slows writing and reading.
- `compression_opts` passes HDF5 filter options, such as gzip level.
- `as_dense` supports only `"X"` and `"raw/X"`; use this for downstream tools that require dense storage.

```python
adata.write_h5ad("out.h5ad", compression="lzf")
roundtripped = ad.read_h5ad("out.h5ad")
assert roundtripped.shape == adata.shape
```

### `AnnData.write_zarr(store, *, chunks=None, convert_strings_to_categoricals=True, consolidate_metadata=True)`

Writes an AnnData object to a Zarr store.

- `store` can be a path, mutable mapping, or compatible Zarr store.
- `chunks` sets dense `X` chunks. Sparse arrays are encoded as sparse groups with `data`, `indices`, and `indptr`.
- `convert_strings_to_categoricals=True` mirrors H5AD writes.
- `consolidate_metadata=True` writes consolidated metadata by default; this improves lazy and remote-style reads but means structural edits require unconsolidated open plus reconsolidation.
- AnnData writes use `anndata.settings.zarr_write_format` when it opens a writable group internally; the verified default is `3`.

```python
adata.write_zarr("out.zarr", chunks=(1024, adata.n_vars))
roundtripped = ad.read_zarr("out.zarr")
assert roundtripped.shape == adata.shape
```

## Stable Element-Level APIs

### `anndata.io.read_elem(elem)`

Reads one encoded HDF5 or Zarr storage element.

- `elem` may be an HDF5 group/dataset, Zarr group/array, or compatible storage element.
- The element must have AnnData encoding metadata: `encoding-type` and `encoding-version`.
- Returns the matching in-memory object, such as a NumPy array, SciPy CSR/CSC sparse matrix, pandas DataFrame, categorical, mapping, scalar, or AnnData object.
- High-level `read_h5ad` and `read_zarr` include additional legacy compatibility; try them before direct `read_elem` on old stores.

```python
import h5py
import anndata as ad

with h5py.File("input.h5ad", "r") as handle:
    obs = ad.io.read_elem(handle["obs"])
```

### `anndata.io.write_elem(store, k, elem, *, dataset_kwargs=mappingproxy({}))`

Writes one encoded element into an HDF5 or Zarr group.

- `store` is a writable HDF5 or Zarr group.
- `k` is the key. Use `"/"` only to write directly into the current root group.
- Absolute keys referring to direct children are accepted; ordinary nested slash keys are restricted, especially for Zarr and H5AD writes.
- `dataset_kwargs` passes creation options such as HDF5 compression, Zarr chunks, compressor/compressors, or sparse indptr dtype.
- A Zarr group with consolidated metadata cannot be overwritten/edited directly; open with `use_consolidated=False`, write, then reconsolidate.

```python
import h5py
import anndata as ad

with h5py.File("elements.h5", "w") as handle:
    ad.io.write_elem(handle, "obs", adata.obs)
with h5py.File("elements.h5", "r") as handle:
    obs = ad.io.read_elem(handle["obs"])
```

### `anndata.io.sparse_dataset(group, *, should_cache_indptr=True)`

Wraps an encoded CSR/CSC sparse group as a backed sparse dataset.

- `group` must have sparse encoding metadata, usually `encoding-type` of `csr_matrix` or `csc_matrix` and a `shape` attribute.
- The result behaves like `anndata.abc.CSRDataset` or `anndata.abc.CSCDataset`.
- Indexing returns sparse selections; `to_memory()` loads the full matrix.
- `append()` appends same-format sparse matrices or sparse datasets with compatible non-appended dimensions.
- `should_cache_indptr=True` improves repeated slices; set it to `False` for many short-lived opens that read only small subsets.

```python
with h5py.File("input.h5ad", "r") as handle:
    X = ad.io.sparse_dataset(handle["X"])
    block = X[:10, :]
```

## Experimental And Lazy APIs

These APIs are useful but should be presented as experimental, version-sensitive, and dependent on optional lazy dependencies such as `xarray` and dask.

### `anndata.experimental.read_lazy(store, *, load_annotation_index=True)`

Reads as much of an AnnData H5AD/Zarr store lazily as possible.

- Accepts `.h5ad` paths, HDF5 file/group objects, Zarr paths, mutable mappings, and Zarr groups.
- For H5AD paths, the returned object has an open HDF5 file attached at `adata.file`; close it when done.
- Passing an already opened `h5py.File` gives explicit lifetime control.
- For Zarr paths, consolidated metadata is preferred; unconsolidated reads can warn and are slower or less complete.
- `load_annotation_index=False` avoids loading true `obs`/`var` indexes immediately and uses range-like indexes in lazy dataframe views.

```python
lazy = ad.experimental.read_lazy("large.zarr", load_annotation_index=False)
print(lazy.shape, type(lazy.X))
```

### `anndata.experimental.read_elem_lazy(elem, chunks=None, **kwargs)`

Lazily reads one encoded element.

- Dense arrays default to on-disk chunks when possible.
- CSR sparse defaults are approximately `(1000, n_vars)`.
- CSC sparse defaults are approximately `(n_obs, 1000)`.
- `chunks` must match dimensionality; for sparse arrays only the major axis can be chunked. Use `None` or `-1` for the full axis.

### `anndata.experimental.read_dispatched(elem, callback)`

Reads an encoded element while calling `callback(read_func, elem_name, elem, iospec=iospec)` at each encoded element.

- Use when a workflow needs selective materialization, dask conversion, or custom handling by `iospec.encoding_type`.
- The callback should call `read_func(elem)` for default behavior or return an alternative object.
- Returning `None` intentionally omits that element from the recursive result.

### `anndata.experimental.write_dispatched(store, key, elem, callback, *, dataset_kwargs=mappingproxy({}))`

Writes recursively while calling `callback(write_func, store, key, elem, dataset_kwargs=dataset_kwargs, iospec=iospec)` at each encoded element.

- Use when different elements need different chunks, sharding, or storage options.
- Use `key="/"` to write an AnnData object into the root group.
- Always forward to `write_func(store, key, elem, dataset_kwargs=dataset_kwargs)` unless intentionally skipping or replacing an element.

## Zarr Settings

### `anndata.settings.zarr_write_format`

- Verified default: `3`.
- Controls the Zarr version AnnData uses when it internally opens a writable Zarr group.
- Set to `2` only when a downstream consumer requires Zarr v2.
- Verify round-trips after changing this setting.

### `anndata.settings.auto_shard_zarr_v3`

- Verified default: `True`.
- Applies to AnnData writing mechanisms for Zarr v3 when the caller has not provided explicit `shards`.
- Ignored for Zarr v2.
- Does not override user-defined shard options.
- Shards are experimental Zarr v3 behavior; validate with a tiny local store before using on production data.

```python
with ad.settings.override(zarr_write_format=3, auto_shard_zarr_v3=True):
    adata.write_zarr("out.zarr")
```

## Storage Prerequisites For `concat_on_disk`

`anndata.experimental.concat_on_disk` belongs to the combining-data sub-skill, but storage readiness is handled here:

- Inputs must be paths or open HDF5/Zarr groups readable by AnnData.
- Choose output `.h5ad` or `.zarr` intentionally; use Zarr for chunked directory/cloud-style output and H5AD for single-file output.
- Ensure input files are not stale, partially written, or missing `obs`/`var`.
- Avoid mutating consolidated Zarr inputs during concat.
- After concat, use `read_h5ad`, `read_zarr`, or a lazy read to validate the output shape and expected batch annotations.
