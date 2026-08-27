# AnnData H5AD/Zarr File Format Notes

AnnData stores use a hierarchical array layout over HDF5 (`.h5ad`, via h5py) and Zarr (`.zarr`, via zarr). The two formats are structurally similar: arrays and groups on disk correspond to AnnData arrays, dataframes, mappings, sparse matrices, and nested metadata.

## Core Encoding Contract

Every encoded element should have string-valued metadata:

- `encoding-type`: logical type, such as `anndata`, `array`, `csr_matrix`, `csc_matrix`, `dataframe`, `categorical`, `dict`, `string`, `string-array`, `numeric-scalar`, `nullable-integer`, `nullable-boolean`, or `nullable-string-array`.
- `encoding-version`: version of that logical encoding.

A whole AnnData root group is expected to carry:

```text
encoding-type = anndata
encoding-version = 0.1.0
```

The root group must contain `obs` and `var` dataframes. It may also contain `X`, `layers`, `obsm`, `varm`, `obsp`, `varp`, `uns`, and `raw`.

## Root Hierarchy

A typical whole-object store has keys like:

```text
/
  X
  obs
  var
  layers
  obsm
  varm
  obsp
  varp
  uns
  raw
```

Required shape relationships:

- `X`: `(n_obs, n_vars)` when present.
- `layers/*`: `(n_obs, n_vars)`.
- `obsm/*`: first dimension `n_obs`.
- `varm/*`: first dimension `n_vars`.
- `obsp/*`: first two dimensions `(n_obs, n_obs)`.
- `varp/*`: first two dimensions `(n_vars, n_vars)`.
- `obs`: dataframe with `n_obs` rows, even if it only stores an index.
- `var`: dataframe with `n_vars` rows, even if it only stores an index.
- `uns`: encoded mapping whose contents may be recursively encoded.

Use `../data-model/SKILL.md` for in-memory slot semantics; this file covers storage validation.

## Dense Arrays

Dense arrays are HDF5 datasets or Zarr arrays.

Expected metadata:

```text
encoding-type = array
encoding-version = 0.2.0
```

Inspect dense `X` safely:

```python
import h5py

with h5py.File("input.h5ad", "r") as handle:
    if "X" in handle and hasattr(handle["X"], "shape"):
        print(handle["X"].shape, handle["X"].dtype, dict(handle["X"].attrs))
```

## Sparse Arrays

CSR and CSC sparse matrices are stored as groups because HDF5 and Zarr do not have a native compressed sparse matrix type.

Expected sparse group metadata:

```text
encoding-type = csr_matrix  # or csc_matrix
encoding-version = 0.1.0
shape = [n_rows, n_cols]
```

Expected child arrays:

```text
data
indices
indptr
```

Use cases:

- `anndata.io.read_elem(group)` returns an in-memory SciPy sparse matrix.
- `anndata.io.sparse_dataset(group)` returns a backed sparse dataset wrapper for slicing.
- `anndata.experimental.read_elem_lazy(group)` returns a lazy dask-backed sparse object when lazy dependencies are available.

Safe sparse inspection:

```python
import h5py
import anndata as ad

with h5py.File("input.h5ad", "r") as handle:
    attrs = dict(handle["X"].attrs)
    if attrs.get("encoding-type") in {"csr_matrix", "csc_matrix"}:
        X = ad.io.sparse_dataset(handle["X"])
        print(X.shape, X.dtype)
```

## DataFrames

DataFrames such as `obs` and `var` are stored as groups with one child array per column and one child array for the index.

Expected dataframe metadata:

```text
encoding-type = dataframe
encoding-version = 0.2.0
_index = <key of index array>
column-order = [<column keys in order>]
```

Rules:

- The group must contain an array for the index named by `_index`.
- Each dataframe column is stored as an encoded child array or group.
- Column entries must have equivalent first dimensions.
- Categorical columns are groups with `codes` and `categories`.

## Mappings

Mappings such as `layers`, `obsm`, `varm`, `obsp`, `varp`, and nested `uns` values are stored as groups.

Expected mapping metadata:

```text
encoding-type = dict
encoding-version = 0.1.0
```

A mapping group recursively contains encoded elements. Do not assume raw HDF5/Zarr children are readable unless they carry AnnData encoding metadata.

## Scalars, Strings, Categoricals, And Nullable Arrays

Common encodings:

- Numeric scalar: `encoding-type = numeric-scalar`, `encoding-version = 0.2.0`.
- String scalar: `encoding-type = string`, `encoding-version = 0.2.0`.
- String array: `encoding-type = string-array`, `encoding-version = 0.2.0`.
- Categorical: group with `encoding-type = categorical`, `encoding-version = 0.2.0`, boolean `ordered`, and child arrays `codes` and `categories`.
- Nullable integer: group with `encoding-type = nullable-integer`, `encoding-version = 0.1.0`, child arrays `values` and `mask`.
- Nullable boolean: group with `encoding-type = nullable-boolean`, `encoding-version = 0.1.0`, child arrays `values` and `mask`.
- Nullable string: group with `encoding-type = nullable-string-array`, `encoding-version = 0.1.0`, child arrays `values` and `mask`, and optional `na-value`.

If writing pandas nullable string arrays fails or changes representation, check `anndata.settings.allow_write_nullable_strings` and round-trip the affected annotation columns explicitly.

## H5AD Inspection

Use h5py to inspect a file without materializing the full object:

```python
import h5py

with h5py.File("input.h5ad", "r") as handle:
    print(dict(handle.attrs))
    print(list(handle.keys()))
    for key in ["obs", "var", "X"]:
        if key in handle:
            print(key, dict(handle[key].attrs))
```

Minimum whole-store checks:

```python
with h5py.File("input.h5ad", "r") as handle:
    assert "obs" in handle and "var" in handle
    assert handle.attrs.get("encoding-type") in {"anndata", None}
```

`None` at the root can occur in older files. Read with AnnData, validate, and rewrite to a new file if `OldFormatWarning` appears.

## Zarr Inspection

Use zarr to inspect a store:

```python
import zarr

group = zarr.open("input.zarr", mode="r")
print(dict(group.attrs))
print(list(group.keys()))
for key in ["obs", "var", "X"]:
    if key in group:
        print(key, dict(group[key].attrs))
```

Current AnnData writes consolidate Zarr metadata by default. If you edit a store after writing, open it unconsolidated, write the change, and reconsolidate:

```python
import zarr
import anndata as ad

group = zarr.open_group("input.zarr", mode="a", use_consolidated=False)
ad.io.write_elem(group["obs"], "quality_score", quality_score_array)
zarr.consolidate_metadata(group.store)
```

If consolidated metadata is stale, readers may see old keys, miss new keys, reject writes with a consolidated metadata error, or warn before falling back to unconsolidated reads.

## Zarr V2 And V3 Notes

- AnnData uses `anndata.settings.zarr_write_format` when it internally opens writable Zarr groups; the verified default is `3`.
- `anndata.settings.auto_shard_zarr_v3` defaults to `True` and applies automatic sharding for Zarr v3 writes when no explicit `shards` are provided.
- Zarr v3 writes are consolidated by default through `AnnData.write_zarr` and `anndata.io.write_zarr`.
- Zarr v3 sharding reduces many-small-file pressure, but shard sizes and compressors should be validated on a tiny store before production use.
- Zarr v3 default codec behavior may differ from older Zarr expectations; set a compressor explicitly only when the runtime and downstream readers support it.

## Legacy And Invalid Encodings

Symptoms of invalid encoding metadata usually surface as `IORegistryError` with the failing key in the error message. Common causes are:

- Missing `encoding-type` or `encoding-version` on a manually created group.
- Unsupported or misspelled encoding type.
- Store written by a newer AnnData than the reader supports.
- Stale consolidated Zarr metadata after a structural edit.

Safe recovery sequence:

1. Copy the store before repair.
2. Inspect the failing element's attributes and shape.
3. Prefer high-level `read_h5ad` or `read_zarr` for whole stores because they include compatibility paths.
4. Reconstruct or rewrite only the broken element with `anndata.io.write_elem` when the correct in-memory value is known.
5. For Zarr, reconsolidate metadata after structural edits.
6. Re-read the whole store and validate shape, names, and expected keys.

## Round-Trip Validation Checklist

After any write or repair:

- Re-read the result with `read_h5ad` or `read_zarr`.
- Compare `shape`, `obs_names`, and `var_names`.
- Compare selected `layers`, `obsm`, `varm`, `obsp`, `varp`, and `uns` keys expected by the workflow.
- Confirm whether `X` is dense or sparse as intended.
- Inspect compression/chunks only where they matter to the downstream consumer.
- Close backed or HDF5-lazy handles.
- Run `scripts/check_anndata_io_roundtrip.py` in the target environment for a tiny deterministic fixture.
