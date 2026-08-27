---
name: storage-io
description: "Read, write, choose, inspect, and troubleshoot AnnData H5AD/Zarr
  storage, backed mode, lazy reads, sparse datasets, element-level I/O, and Zarr
  v3 options."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Storage I/O

Use this sub-skill when a task mentions `.h5ad`, `.zarr`, HDF5, Zarr, storage formats, backed mode, lazy reads, `read_h5ad`, `read_zarr`, `write_h5ad`, `write_zarr`, `anndata.io.read_elem`, `anndata.io.write_elem`, `anndata.io.sparse_dataset`, encoding metadata, sparse on-disk arrays, compression, chunking, Zarr v3, metadata consolidation, or `concat_on_disk` storage prerequisites.

## Route First

- Continue here for whole-object H5AD/Zarr reads and writes, storage choice, backed/lazy access, element-level reads/writes, sparse on-disk datasets, encoding metadata, and storage-specific failures.
- Route object construction, aligned slot shape rules, views, `obs`/`var` semantics, `.raw`, and in-memory mutation to `../data-model/SKILL.md`.
- Route multi-object combination semantics to `../combining-data/SKILL.md`; use this sub-skill only to prepare readable input stores and validate writable output stores for `concat_on_disk`.
- Route accessors, references, and extension namespaces to `../accessors-extensions/SKILL.md`.

## Use The Bundled Files

- `references/api-reference.md` lists verified public I/O signatures, stable versus experimental APIs, and option notes.
- `references/file-format.md` distills the H5AD/Zarr hierarchy, required encoding metadata, and inspection checks.
- `references/io-workflows.md` gives decision workflows for H5AD versus Zarr, backed versus lazy access, element I/O, sparse datasets, Zarr v3 metadata, sharding, and compressor choices.
- `references/troubleshooting.md` maps storage symptoms to causes and recovery steps.
- `scripts/check_anndata_io_roundtrip.py` creates tiny deterministic H5AD and/or Zarr fixtures, reads them back, optionally checks backed/lazy access, and prints pass/fail without network access.

## Default Decisions

- Prefer `.h5ad` for single-file local exchange and HDF5 `backed` reads; close backed objects with `adata.file.close()`.
- Prefer Zarr for directory or cloud-style stores, chunk tuning, consolidated metadata, sharding, and codec configuration.
- Use full `read_h5ad`/`read_zarr` for small or final validation reads; use `read_h5ad(..., backed="r")` for low-memory H5AD inspection; use `anndata.experimental.read_lazy` for experimental dask/xarray-backed low-memory reads.
- Treat `anndata.experimental.read_lazy`, `read_dispatched`, and `write_dispatched` as experimental APIs; use stable high-level methods and `anndata.io.read_elem`/`write_elem` unless callback-based traversal or lazy materialization is required.
- After writing any store, re-read it and validate shape, names, expected keys, sparse/dense representation, and backing/lazy file lifecycle.

## Quick Checks

```bash
python sub-skills/storage-io/scripts/check_anndata_io_roundtrip.py
python sub-skills/storage-io/scripts/check_anndata_io_roundtrip.py --backed-lazy
python sub-skills/storage-io/scripts/check_anndata_io_roundtrip.py --output-dir ./tmp-anndata-io --keep
```

When running the script from outside the skill directory, use its full path. The script creates only local temporary fixtures unless `--output-dir` is provided.
