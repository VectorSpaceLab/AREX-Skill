# Storage I/O Troubleshooting

Use this matrix for AnnData H5AD/Zarr reads, writes, backed access, lazy reads, element-level operations, sparse datasets, and Zarr v3 metadata issues.

## Quick Triage

H5AD root inspection:

```python
import h5py

with h5py.File("input.h5ad", "r") as handle:
    print(dict(handle.attrs))
    print(list(handle.keys()))
```

Zarr root inspection:

```python
import zarr

group = zarr.open("input.zarr", mode="r")
print(dict(group.attrs))
print(list(group.keys()))
```

Tiny bundled validation:

```bash
python sub-skills/storage-io/scripts/check_anndata_io_roundtrip.py
python sub-skills/storage-io/scripts/check_anndata_io_roundtrip.py --backed-lazy
python sub-skills/storage-io/scripts/check_anndata_io_roundtrip.py --skip-zarr
```

## Missing Optional Dependencies

### `ModuleNotFoundError: No module named 'h5py'`

Likely cause: the runtime lacks HDF5 support needed for `.h5ad`.

Recovery:

- Install AnnData with H5AD-capable dependencies.
- Confirm `python -c "import anndata, h5py"` works.
- If only Zarr is needed, avoid `.h5ad` paths but keep in mind existing H5AD files still require h5py.

### `ModuleNotFoundError: No module named 'zarr'`

Likely cause: the runtime lacks Zarr support.

Recovery:

- Install a Zarr version compatible with the active AnnData version.
- Confirm `python -c "import anndata, zarr"` works.
- Use `.h5ad` only if Zarr workflows are not required.

### Lazy read fails with missing `xarray`, dask, or related dependency

Likely cause: `anndata.experimental.read_lazy` and `read_elem_lazy` require optional lazy/backed dependencies beyond eager reads.

Recovery:

- Confirm eager reading works first on a tiny fixture.
- Install AnnData's lazy/dask/xarray-related optional dependencies.
- Fall back to `read_h5ad(..., backed="r")` for H5AD inspection when lazy dependencies are unavailable.
- Fall back to `read_elem` or `sparse_dataset` for targeted element access.

## Encoding And Registry Failures

### `IORegistryError`, “No read method registered”, or “raised while reading key ...”

Likely cause: invalid or unsupported `encoding-type` / `encoding-version` metadata on the failing element.

Recovery:

- Inspect the failing element's attributes, not just the root group.
- Use high-level `read_h5ad` or `read_zarr` for whole stores before direct `read_elem`; high-level readers include more compatibility paths.
- If one element is corrupted, copy the store, reconstruct that element from trusted data, and rewrite it with `anndata.io.write_elem`.
- If a newer AnnData wrote the store, use a reader version that supports the encoding, then rewrite a fresh store.
- For Zarr, check whether consolidated metadata is stale after manual edits.

### Root store lacks `encoding-type` or `encoding-version`

Likely cause: very old AnnData format, a non-AnnData HDF5/Zarr hierarchy, or a manually created group.

Recovery:

- Confirm `obs` and `var` exist before treating the root as AnnData.
- Try `ad.read_h5ad(path)` or `ad.read_zarr(path)` and capture warnings.
- If it is truly not an AnnData store, build a new `AnnData` object from validated arrays/dataframes and write a fresh store.
- Do not add root metadata blindly to an arbitrary hierarchy.

### `OldFormatWarning`

Likely cause: older AnnData dataframe or raw encodings.

Recovery:

- Read the file with the newest compatible AnnData available.
- Validate critical content: shape, names, key sets, selected annotations, and sparse/dense expectations.
- Write a fresh `.h5ad` or `.zarr` copy.
- Re-read the new copy and compare expected checks before replacing any original.

## Backed And Lazy Lifecycle Problems

### Backed H5AD object fails after file close

Likely cause: a backed object depends on its open HDF5 file.

Recovery:

- Keep the file open for the full lifetime of backed access.
- Wrap backed access in `try/finally` and call `adata.file.close()` after use.
- Convert to memory with `adata.to_memory()` before closing if later operations need materialized arrays.

### H5AD file locking or open-handle errors

Likely cause: another process or previous backed object has the file open, or the filesystem has restrictive HDF5 locking behavior.

Recovery:

- Close all backed objects and HDF5 handles.
- Avoid multiple writers or `backed="r+"` opens on the same file.
- Copy to a local scratch path and retry read-only access.
- Write to a new path and replace only after validation if an application needs an update.

### Backed changes to `obs`, `var`, `layers`, or `uns` disappear

Likely cause: backed mode persists in-place `X` updates, not arbitrary slot mutations.

Recovery:

- Use `backed="r+"` only for intentional `X` updates.
- For annotation or metadata edits, call `to_memory()` or read eagerly, edit, then write a new H5AD.
- Re-read the new file and verify the edited fields.

### Lazy object cannot be written directly

Likely cause: some lazy/backed dataframe components use `Dataset2D`, which AnnData does not write directly in all paths.

Recovery:

- Materialize the necessary components with `.to_memory()` before writing.
- For a whole object, validate `adata.to_memory()` on a subset before materializing everything.
- If memory is insufficient, redesign the workflow around element-level reads or on-disk concatenation rather than direct rewrite.

## Zarr Consolidated Metadata

### Zarr read sees stale keys, misses new keys, or warns about consolidated metadata

Likely cause: the store was structurally edited after consolidated metadata was written, or it was never consolidated.

Recovery:

- Open the store with `zarr.open_group(path, mode="a", use_consolidated=False)`.
- Compare key lists if needed using consolidated and unconsolidated opens.
- Re-run `zarr.consolidate_metadata(group.store)` after structural edits.
- Re-read with `ad.read_zarr(path)` or `ad.experimental.read_lazy(path)`.

### `Cannot overwrite/edit a store with consolidated metadata`

Likely cause: `anndata.io.write_elem` is being used on a Zarr group opened with consolidated metadata.

Recovery:

```python
import zarr
import anndata as ad

group = zarr.open_group("input.zarr", mode="a", use_consolidated=False)
ad.io.write_elem(group["obs"], "new_column", values)
zarr.consolidate_metadata(group.store)
```

Do not edit consolidated metadata files manually unless no API repair path exists and a copy has been made.

## Sparse, Dense, Compression, And Chunking

### `ValueError` or `NotImplementedError` for `as_sparse` / `as_dense`

Likely cause: AnnData supports H5AD dense/sparse conversion options only for `"X"` and `"raw/X"`.

Recovery:

- Use `read_h5ad(path, as_sparse=("X",))` or `("raw/X",)` only.
- Use `write_h5ad(path, as_dense=("X",))` or `("raw/X",)` only.
- Convert layers or other arrays explicitly in memory before writing.
- Use only `scipy.sparse.csr_matrix` or `scipy.sparse.csc_matrix` for `as_sparse_fmt`.

### Memory pressure during eager read

Likely cause: full materialization, dense-stored arrays, oversized dense-to-sparse chunks, or missing lazy dependencies.

Recovery:

- For H5AD inspection, start with `read_h5ad(path, backed="r")`.
- For dense-stored `X`, use `as_sparse=("X",)` and reduce `chunk_size`.
- For Zarr or mixed stores, use `experimental.read_lazy` after installing optional dependencies.
- Read only needed elements with `read_elem` or `sparse_dataset`.
- Avoid `.to_memory()` until a subset confirms memory needs.

### `read_elem_lazy(..., chunks=...)` rejects chunks

Likely cause: chunk tuple length does not match dimensionality or sparse chunks split the minor axis.

Recovery:

- CSR sparse: use chunks like `(rows_per_chunk, n_vars)`.
- CSC sparse: use chunks like `(n_obs, cols_per_chunk)`.
- Use `None` or `-1` for a full axis.
- Start with `chunks=None` to use AnnData defaults, then tune.

### Sparse dataset append fails

Likely cause: format or shape mismatch.

Recovery:

- Append CSR to CSR and CSC to CSC only.
- CSR append requires matching number of columns.
- CSC append requires matching number of rows.
- Use sparse matrices or backed sparse datasets, not dense arrays.
- Test append behavior in a scratch store before modifying important data.

### H5AD custom compression cannot be read elsewhere

Likely cause: an external HDF5 compression filter is not installed in the reader environment.

Recovery:

- Prefer `compression="gzip"`, `"lzf"`, or no compression for broad compatibility.
- Import required HDF5 filter plugins before reading if custom compression is unavoidable.
- Rewrite with a broadly compatible compressor before sharing.
- Prefer Zarr for workflows that need portable codec configuration.

### Zarr codec, sharding, or GPU path behaves unexpectedly

Likely cause: Zarr v3 codec/sharding/GPU behavior is version-specific and not a universal AnnData I/O default.

Recovery:

- Reproduce with a tiny local Zarr store.
- Disable custom codecs, sharding, GPU settings, or `zarrs` acceleration to confirm baseline behavior.
- Keep general AnnData storage on CPU-backed Zarr unless dense-only GPU I/O has been validated in the target environment.
- Use explicit `zarr_write_format`, chunks, compressor, and sharding settings only when downstream readers are known to support them.

## Keys, Paths, And Stores

### Write fails for keys containing `/`

Likely cause: forward slashes imply nested paths and are restricted for AnnData element keys.

Recovery:

- Rename user-facing keys from values like `"sample/1"` to `"sample_1"`.
- Use nested groups deliberately only with low-level APIs and clear path semantics.
- Use `k="/"` only to write an object into the current root group.

### Write target is read-only, partially exists, or parent directory is missing

Likely cause: permissions, missing parent directories, or a failed previous write left a partial target.

Recovery:

- Create parent directories before writing.
- Write to a fresh scratch path first.
- Remove a partial Zarr directory only after confirming it is safe.
- Re-read and validate before replacing a previous production store.

### Remote Zarr store is slow or inconsistent

Likely cause: missing consolidated metadata, object-store consistency delays, many small chunks/files, or unsupported store abstraction.

Recovery:

- Prefer consolidated metadata for remote reads.
- Avoid mutating remote stores in place; write a new versioned store when possible.
- Tune chunks and sharding with a representative small benchmark.
- Validate the same store with eager `read_zarr` and `experimental.read_lazy` on a small subset or fixture.

## Recovery Principles

- Work on a copy before repairing metadata or elements.
- Prefer high-level readers for whole-store compatibility checks.
- Use `read_elem` and `write_elem` for targeted encoded elements only when metadata is valid and the intended object is known.
- Reconsolidate Zarr metadata after structural edits.
- Always perform a readback validation with shape, names, key sets, and selected values.
- Close HDF5-backed objects and handles promptly.
