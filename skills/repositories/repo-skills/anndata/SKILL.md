---
name: anndata
description: "Use AnnData to build, inspect, combine, store, lazily read, and
  extend annotated data matrices in memory and on disk."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# AnnData Repo Skill

Use this repo skill when a task involves `anndata`, `AnnData`, annotated data matrices, `.h5ad`, `.zarr`, backed mode, lazy reads, `anndata.concat`, `AnnCollection`, `anndata.acc`, or AnnData extension namespaces. AnnData is a Python package for annotated data matrices with aligned observations, variables, multidimensional annotations, pairwise arrays, layers, unstructured metadata, and native HDF5/Zarr storage.

## First Checks

- Install AnnData with `pip install anndata` or `conda install -c conda-forge anndata` when the project does not already provide it.
- For lazy reads or remote Zarr workflows, install the package extra that provides `xarray`, `dask`, `requests`, and `aiohttp`: `pip install "anndata[lazy]"`.
- Prefer public imports such as `import anndata as ad` and `from anndata import AnnData`; avoid leading-underscore internals unless the task is explicitly repository maintenance.
- Confirm importability before deeper work:

```bash
python - <<'PY'
import anndata as ad
from anndata import AnnData
print(ad.__name__, AnnData)
PY
```

- Run [`scripts/smoke_anndata_core.py`](scripts/smoke_anndata_core.py) for a safe bundled smoke test covering construction, concat, H5AD, and optional Zarr round-trips.

## Route Map

- Use [`sub-skills/data-model/SKILL.md`](sub-skills/data-model/SKILL.md) for constructing, inspecting, mutating, validating, slicing, copying, or repairing in-memory `AnnData` objects and aligned containers such as `X`, `obs`, `var`, `layers`, `obsm`, `varm`, `obsp`, `varp`, `uns`, and `raw`.
- Use [`sub-skills/storage-io/SKILL.md`](sub-skills/storage-io/SKILL.md) for `.h5ad`, Zarr, backed mode, lazy reads, sparse on-disk datasets, element-level `read_elem`/`write_elem`, encoding metadata, compression, chunking, and I/O troubleshooting.
- Use [`sub-skills/combining-data/SKILL.md`](sub-skills/combining-data/SKILL.md) for `anndata.concat`, mapping-vs-sequence keys, merge and join decisions, batch labels, duplicate names, pairwise graph retention, `AnnCollection`, and `experimental.concat_on_disk`.
- Use [`sub-skills/accessors-extensions/SKILL.md`](sub-skills/accessors-extensions/SKILL.md) for `anndata.acc.A` references, reusable validation or plotting helpers, JSON/string reference forms, `register_anndata_namespace`, and extension namespace debugging.

## Common Workflows

1. For a new object, start with `data-model`: confirm `X.shape == (len(obs), len(var))`, choose stable `obs_names` and `var_names`, add aligned arrays only when their leading axes match, then run the bundled structure inspector when shape problems are likely.
2. For persistence, move to `storage-io`: choose `.h5ad` for single-file exchange or Zarr for directory/object-store workflows, validate round-trips with a tiny fixture, and use backed/lazy reads only when their access constraints fit the task.
3. For multi-dataset integration, use `combining-data`: decide `axis`, `join`, `merge`, `uns_merge`, `label`, `keys`, `index_unique`, `fill_value`, and whether memory pressure requires `AnnCollection` or `concat_on_disk`.
4. For reusable library code, use `accessors-extensions`: represent fields with `A.obs[...]`, `A.obsm[...][:, i]`, or `A.layers[...]`, validate references before indexing, and keep extension namespaces small and explicitly typed.

## Shared References And Scripts

- Read [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting install/import, optional dependency, data validation, API misuse, storage backend, and workflow-routing issues before diving into sub-skill-specific troubleshooting.
- Read [`references/repo-provenance.md`](references/repo-provenance.md) when deciding whether this generated skill is stale against a newer AnnData checkout or release.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json) is structured metadata used by DisCo's managed `repo-skills-router` import.
- Run [`scripts/smoke_anndata_core.py`](scripts/smoke_anndata_core.py) to validate import, core object construction, concat behavior, and optional H5AD/Zarr round-trips with tiny temporary fixtures.

## Decision Points

- Use sparse `X` and sparse layers when data is mostly zero; dense arrays are simpler for tiny examples but can hide memory pressure.
- Treat `.raw` as an intentional snapshot of original `X`, `var`, and `varm`; later `.var` mutations do not automatically update `.raw.var`.
- Use `.copy()` before mutating subsets when parent preservation or warning-free behavior matters.
- Use `join="inner"` for conservative concat across features and `join="outer"` only when downstream code can handle missing values or sparse zero fill.
- For `anndata.concat`, use mapping keys or sequence `keys`, not both, when creating batch labels.
- Use backed mode for limited H5AD inspection and reads; do not assume every in-memory mutation works without materializing.
- Treat `experimental` APIs as useful but less stable; mention optional dependencies and deprecations such as `AnnLoader` moving toward `annbatch.Loader` when relevant.

## Troubleshooting Priority

1. Verify the import, installed version, and optional extras relevant to the task.
2. Reproduce with a tiny `AnnData` object before scaling to large files or many batches.
3. Check shapes and names on every aligned slot.
4. Isolate storage problems with a fresh tiny H5AD or Zarr round-trip.
5. For concat surprises, print `shape`, `obs_names`, `var_names`, label categories, `.uns.keys()`, and relevant `.obsm`/`.varm`/`.obsp` keys.
6. For accessor or extension errors, validate references and namespace signatures before optional plotting, storage, or downstream package imports.
