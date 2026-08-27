# AnnData Cross-Cutting Troubleshooting

Read this when a task fails before it is clearly owned by a focused sub-skill, or when install/import, optional dependency, or workflow-routing issues block progress.

## Import And Version Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'anndata'` | Package is not installed in the active environment | Install with `pip install anndata` or `conda install -c conda-forge anndata`, then rerun the import check in the root `SKILL.md`. |
| `ImportError` for `h5py`, `zarr`, `pandas`, `scipy`, or `numpy` | Partial or inconsistent environment | Run `python -m pip check`; reinstall AnnData in a clean environment if resolver conflicts remain. |
| Lazy-read failures mentioning `xarray`, `dask`, `requests`, or `aiohttp` | Lazy/remote storage dependencies are missing | Install `anndata[lazy]` for workflows that use `anndata.experimental.read_lazy` or remote Zarr stores. |
| Unexpected public API differences | Skill and installed package are from different versions | Compare the installed version and current checkout with `references/repo-provenance.md`; refresh the skill if public signatures changed. |

## Routing Failures

- If the issue is an `AnnData(...)` constructor error, shape mismatch, `obs`/`var` index issue, view warning, or `.raw` confusion, use `sub-skills/data-model/SKILL.md`.
- If the issue involves `.h5ad`, Zarr, backed mode, lazy reads, `read_elem`, `write_elem`, compression, chunks, or encoding metadata, use `sub-skills/storage-io/SKILL.md`.
- If the issue involves combining multiple objects or files, use `sub-skills/combining-data/SKILL.md`.
- If the issue involves `anndata.acc.A`, reference strings/JSON, plotting/validation references, or extension namespaces, use `sub-skills/accessors-extensions/SKILL.md`.

## Data Validation First Aid

Before debugging complex workflows, create or load a tiny object and print:

```python
print(adata.shape)
print(adata.obs_names.is_unique, adata.var_names.is_unique)
print(list(adata.layers), list(adata.obsm), list(adata.varm), list(adata.obsp), list(adata.varp))
print(adata.is_view)
```

Then run the nearest bundled helper:

- `sub-skills/data-model/scripts/inspect_anndata_structure.py` for object structure and aligned-slot checks.
- `sub-skills/storage-io/scripts/check_anndata_io_roundtrip.py` for storage round-trips.
- `sub-skills/combining-data/scripts/plan_anndata_concat.py` for concat parameter risks.
- `sub-skills/accessors-extensions/scripts/demo_anndata_accessor.py` for reference and namespace basics.

## Optional Dependency Boundaries

- GPU arrays require optional CuPy packages (`gpu`, `cu11`, or `cu12` extras in package metadata) and suitable hardware; do not assume GPU-backed arrays work in CPU-only environments.
- `AnnLoader` is PyTorch-oriented and deprecated in favor of `annbatch.Loader`; avoid adding PyTorch solely for ordinary AnnData manipulation.
- Remote Zarr stores can require network access, credentials, or object-store-specific libraries outside AnnData. Treat those as environment prerequisites, not AnnData API bugs.

## Stop Conditions

Stop and ask for environment or data access details when:

- A task requires private remote stores, credentials, or non-public datasets.
- The requested GPU/CUDA path is unavailable on the machine and no CPU fallback is acceptable.
- A large storage or concat operation would overwrite user data; reproduce first with a tiny fixture.
