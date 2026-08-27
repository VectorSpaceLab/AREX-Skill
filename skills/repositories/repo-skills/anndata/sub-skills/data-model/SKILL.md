---
name: data-model
description: "Construct, inspect, validate, slice, copy, and mutate in-memory
  AnnData objects and their aligned annotations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# AnnData Data Model

Use this sub-skill when a task asks how to build, inspect, validate, subset, copy, convert, or mutate an in-memory `anndata.AnnData` object. Typical prompts mention `AnnData(...)`, `X`, `obs`, `var`, `layers`, `obsm`, `varm`, `obsp`, `varp`, `uns`, `.raw`, `obs_names`, `var_names`, views, copy-on-modify warnings, `.to_df()`, `.copy()`, `.to_memory()`, or shape/name validation.

## Route First

- Continue here for single-object construction, aligned slot contracts, index/name checks, view semantics, `.raw`, `to_df`, `copy`, `to_memory`, and safe in-memory mutation patterns.
- Route `.h5ad`, Zarr, backed reads/writes, lazy reads, element I/O, compression, and file lifecycle to [`../storage-io/SKILL.md`](../storage-io/SKILL.md).
- Route `anndata.concat`, `experimental.concat_on_disk`, `AnnCollection`, batch labels, joins, and multi-object merging to [`../combining-data/SKILL.md`](../combining-data/SKILL.md).
- Route `anndata.acc` references and `register_anndata_namespace` extension namespaces to [`../accessors-extensions/SKILL.md`](../accessors-extensions/SKILL.md).

## Use The Bundled Files

- [`references/api-reference.md`](references/api-reference.md) lists verified public signatures, construction forms, and method/property notes.
- [`references/object-model.md`](references/object-model.md) explains axis alignment, slot shape contracts, slicing, copy-on-modify views, `.raw`, and mutation rules.
- [`references/troubleshooting.md`](references/troubleshooting.md) maps common construction and mutation failures to concrete recovery steps.
- [`scripts/inspect_anndata_structure.py`](scripts/inspect_anndata_structure.py) prints a deterministic shape/key/name summary for a demo object, an `.h5ad`, or a Zarr store.

## Default Workflow

1. Establish the intended shape `(n_obs, n_vars)` from `X`, from `shape=...`, or from the aligned annotations being supplied.
2. Build `obs` with exactly `n_obs` rows and `var` with exactly `n_vars` rows; treat their indexes as `obs_names` and `var_names`.
3. Add aligned containers only after checking their axes: `layers` match `(n_obs, n_vars)`, `obsm` rows match `n_obs`, `varm` rows match `n_vars`, `obsp` match `(n_obs, n_obs)`, and `varp` match `(n_vars, n_vars)`.
4. Keep free-form metadata in `uns`; do not put axis-aligned arrays in `uns` when an aligned slot exists.
5. When subsetting, assume `adata[...]` returns a view until copied or mutated; use `.copy()` before intentional independent edits.
6. For normalized/counts snapshots, set `adata.raw = adata.copy()` before replacing `X` or filtering variables; remember `.raw` follows observation slicing but keeps its own variable axis.
7. Validate final objects with `.shape`, `.obs_names.is_unique`, `.var_names.is_unique`, slot keys, and the inspection script before handing them to storage, concat, or downstream analysis.

## Quick Checks

```bash
python sub-skills/data-model/scripts/inspect_anndata_structure.py
python sub-skills/data-model/scripts/inspect_anndata_structure.py --h5ad example.h5ad
python sub-skills/data-model/scripts/inspect_anndata_structure.py --zarr example.zarr
```

When running from outside the skill directory, use the script's full path. The script does not write outputs, access the network, or mutate inputs.
