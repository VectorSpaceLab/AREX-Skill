---
name: preprocessing-qc
description: "Use Scanpy preprocessing for filtering, QC metrics,
  normalization/log transforms, HVG selection, scaling/regression, PCA
  preparation, sampling/downsampling, basic batch correction wrappers, and
  Scrublet doublet workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Scanpy Preprocessing and QC

Use this sub-skill when a task needs to prepare an `AnnData` object for graph construction, embedding, clustering, marker testing, or reporting with `import scanpy as sc` and `sc.pp.*` APIs.

## Route by task

| User need | Use | Details |
|---|---|---|
| Filter cells/genes or compute QC metrics | `sc.pp.filter_cells`, `sc.pp.filter_genes`, `sc.pp.calculate_qc_metrics` | See [QC and filtering](references/workflows.md#qc-and-filtering). |
| Preserve raw counts, normalize, or log-transform | `adata.layers`, `sc.pp.normalize_total`, `sc.pp.log1p` | See [Normalization, log, and layers](references/workflows.md#normalization-log-and-layers). |
| Select HVGs, including batch-aware or Seurat v3 flavors | `sc.pp.highly_variable_genes` | See [Highly variable genes](references/workflows.md#highly-variable-genes). |
| Scale, regress covariates, or compute PCA features | `sc.pp.scale`, `sc.pp.regress_out`, `sc.pp.pca` | See [Scaling, regression, and PCA](references/workflows.md#scaling-regression-and-pca). |
| Sample cells/counts before expensive preprocessing | `sc.pp.sample`, `sc.pp.downsample_counts`, legacy `sc.pp.subsample` | See [Sampling and downsampling](references/workflows.md#sampling-and-downsampling). |
| Apply simple preprocessing batch correction | `sc.pp.combat`, `sc.pp.harmony_integrate` | See [Basic batch correction](references/workflows.md#basic-batch-correction). |
| Detect doublets or simulate doublets | `sc.pp.scrublet`, `sc.pp.scrublet_simulate_doublets` | See [Doublet detection](references/workflows.md#doublet-detection). |
| Apply bundled preprocessing recipes | `sc.pp.recipe_seurat`, `sc.pp.recipe_zheng17`, `sc.pp.recipe_weinreb17` | See [Recipes](references/workflows.md#recipes). |
| Check a local install with a tiny fixture | bundled script | Run `python sub-skills/preprocessing-qc/scripts/scanpy_preprocess_qc_smoke.py`. |

## Fast rules

- Preserve count data before destructive transforms: `adata.layers["counts"] = adata.X.copy()` before `normalize_total`, `log1p`, `scale`, or `regress_out`.
- Make QC and HVG calls explicit about representation: pass `layer="counts"` or `use_raw=True` only when that slot contains the intended matrix.
- Keep `calculate_qc_metrics(..., percent_top=...)` values no larger than `adata.n_vars`; use `percent_top=None` or small values for tiny fixtures.
- Use `inplace=False` to inspect return values for `calculate_qc_metrics`, `filter_*`, `normalize_total`, or `highly_variable_genes`; use `copy=True` only where the API documents copied `AnnData` returns.
- Prefer `scale(zero_center=False)` for sparse-memory-sensitive workflows; `scale(zero_center=True)`, `regress_out`, and ComBat can densify data.
- Run `pca` before `harmony_integrate`, then route `neighbors`, UMAP, clustering, marker ranking, graph plotting, and embedding interpretation to `graph-embedding-analysis`.
- Route IO/data loading to `io-data-access`, plotting/report figures to `plotting-reporting`, and optional integration method selection beyond core Scanpy wrappers to `external-integrations`.

## Required references

- [Workflows](references/workflows.md)
- [API quick reference](references/api-reference.md)
- [Troubleshooting](references/troubleshooting.md)
- [Smoke script](scripts/scanpy_preprocess_qc_smoke.py)
