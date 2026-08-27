# Preprocessing API Quick Reference

This reference covers the public `sc.pp` APIs owned by the `preprocessing-qc` sub-skill for Scanpy version `0.1.0.dev1+g39f12414f` style checkouts. Use `import scanpy as sc`.

## QC and filtering

| API | Key parameters | Return and mutation | Output slots |
|---|---|---|---|
| `sc.pp.calculate_qc_metrics` | `expr_type="counts"`, `var_type="genes"`, `qc_vars=()`, `percent_top=(50, 100, 200, 500)`, `layer=None`, `use_raw=False`, `log1p=True`, `inplace=False` | With `inplace=False`, returns `(obs_metrics, var_metrics)`; with `inplace=True`, writes metrics | `.obs["total_counts"]`, `.obs["n_genes_by_counts"]`, `.obs["pct_counts_<qc_var>"]`, `.var["n_cells_by_counts"]`, `.var["mean_counts"]` |
| `sc.pp.filter_cells` | Exactly one threshold from `min_counts`, `min_genes`, `max_counts`, `max_genes`; `inplace=True`, `copy=False` | Subsets `AnnData` in place, returns copy with `copy=True`, or returns `(mask, values)` with `inplace=False` | May add `.obs["n_counts"]` or `.obs["n_genes"]` |
| `sc.pp.filter_genes` | Exactly one threshold from `min_counts`, `min_cells`, `max_counts`, `max_cells`; `inplace=True`, `copy=False` | Subsets `AnnData` in place, returns copy with `copy=True`, or returns `(mask, values)` with `inplace=False` | May add `.var["n_counts"]` or `.var["n_cells"]` |

## Normalization and transforms

| API | Key parameters | Return and mutation | Notes |
|---|---|---|---|
| `sc.pp.normalize_total` | `target_sum=None`, `exclude_highly_expressed=False`, `max_fraction=0.05`, `key_added=None`, `layer=None`, `obsm=None`, `inplace=True`, `copy=False` | Mutates `.X`, a layer, or an `obsm` entry by default; `inplace=False` returns a dict; `copy=True` returns copied `AnnData` | `target_sum=1e4` is common for log-normalized workflows; `target_sum=1e6` is CPM-like. |
| `sc.pp.log1p` | `base=None`, `copy=False`, `chunked=None`, `chunk_size=None`, `layer=None`, `obsm=None` | Mutates the selected representation unless `copy=True` | Sets `adata.uns["log1p"]`; warns when the object already appears log-transformed. |
| `sc.pp.sqrt` | `copy=False` | Mutates or returns a copy/array depending on input | Less common than `log1p`; ensure downstream methods expect square-root transformed values. |

## HVG selection

| API | Key parameters | Return and mutation | Notes |
|---|---|---|---|
| `sc.pp.highly_variable_genes` | `layer=None`, `n_top_genes=None`, cutoff arguments, `span=0.3`, `n_bins=20`, `flavor="seurat"`, `subset=False`, `inplace=True`, `batch_key=None`, `check_values=True` | Writes `.var` and sometimes `.uns` by default; with `inplace=False`, returns a `DataFrame` | `seurat` and `cell_ranger` expect log-normalized data; `seurat_v3` and `seurat_v3_paper` expect raw integer counts and optional `scanpy[skmisc]`. |
| `sc.pp.recipe_seurat` | `log=True`, filtering/scaling/HVG parameters | Mutates `AnnData` | Convenient but less transparent than explicit steps. |
| `sc.pp.recipe_zheng17` | `log=True`, filtering/HVG/scaling parameters | Mutates `AnnData` | Uses `cell_ranger`-style HVG selection. |
| `sc.pp.recipe_weinreb17` | `log=True`, CV/Fano/PCA parameters | Mutates `AnnData` | Designed for dense data; avoid for sparse matrices unless converted intentionally. |

## Scaling, regression, PCA, and graph prep

| API | Key parameters | Return and mutation | Output slots and cautions |
|---|---|---|---|
| `sc.pp.scale` | `zero_center=True`, `max_value=None`, `copy=False`, `layer=None`, `obsm=None`, `mask_obs=None` | Mutates selected representation or returns copy | Writes `.var["mean"]` and `.var["std"]` by default, or mask-specific mean/std columns with `mask_obs`; `zero_center=True` densifies sparse matrices. |
| `sc.pp.regress_out` | `keys`, `layer=None`, `n_jobs=None`, `copy=False` | Replaces `.X` or selected layer; returns copy with `copy=True` | Use after normalization/log; can densify and overcorrect. |
| `sc.pp.pca` | `n_comps=None`, `layer=None`, `obsm=None`, `zero_center=True`, `svd_solver=None`, `chunked=False`, `chunk_size=None`, `rng=None`, `mask_var=None`, `key_added=None`, `copy=False` | Stores PCA on `AnnData`; for array input returns PCA array | Default writes `.obsm["X_pca"]`, `.varm["PCs"]`, `.uns["pca"]`; if `.var["highly_variable"]` exists, PCA uses it unless `mask_var=None`. |
| `sc.pp.neighbors` | `use_rep`, `n_pcs`, `key_added`, metric/connectivity parameters | Writes graph structures | Mention only as the handoff after PCA/Harmony; route detailed graph/UMAP/clustering work to `graph-embedding-analysis`. |

## Sampling and downsampling

| API | Key parameters | Return and mutation | Notes |
|---|---|---|---|
| `sc.pp.sample` | `n=None`, `fraction=None`, `axis=0`, `replace=False`, `copy=False`, `rng=None` | Samples observations or variables in place, or returns copy with `copy=True` | Use for representative subsampling before expensive preprocessing; set `rng` for reproducibility. |
| `sc.pp.downsample_counts` | `counts_per_cell=None`, `total_counts=None`, `replace=False`, `copy=False`, `rng=None` | Mutates counts or returns copy | Use on count-like matrices; choose per-cell or global total downsampling, not both. |
| `sc.pp.subsample` | `fraction=None`, `n_obs=None`, `random_state=None`, `copy=False` | Legacy sampling helper | Prefer `sample` for new code when available. |

## Batch correction and doublets

| API | Key parameters | Return and mutation | Notes |
|---|---|---|---|
| `sc.pp.combat` | `key="batch"`, `covariates=None`, `inplace=True` | Replaces `.X` by default or returns corrected matrix with `inplace=False` | Requires a categorical batch column; each batch needs enough cells; dense output is expected. |
| `sc.pp.harmony_integrate` | `key`, `basis="X_pca"`, `adjusted_basis="X_pca_harmony"`, tuning/convergence parameters, `rng=None` | Writes adjusted coordinates | Run after PCA; downstream neighbors should use the adjusted basis. |
| `sc.pp.scrublet` | `adata_sim=None`, `batch_key=None`, `sim_doublet_ratio=2.0`, `expected_doublet_rate=0.05`, `n_prin_comps=30`, `threshold=None`, `copy=False`, `rng=None` | Writes doublet calls or returns copied `AnnData` | Raw counts are expected when Scanpy simulates doublets; `threshold=None` needs `scikit-image` for automatic thresholding. |
| `sc.pp.scrublet_simulate_doublets` | `layer=None`, `sim_doublet_ratio=2.0`, `synthetic_doublet_umi_subsampling=1.0`, `rng=None` | Returns simulated doublet `AnnData` | Preprocess observed and simulated matrices consistently before manual `scrublet(..., adata_sim=...)`. |

## Install extras relevant to this sub-skill

- Core preprocessing works with the base `scanpy` install.
- Add `scanpy[skmisc]` for `highly_variable_genes(..., flavor="seurat_v3")` and `flavor="seurat_v3_paper"`.
- Add `scanpy[scrublet]` or ensure `scikit-image` is available when `scrublet(threshold=None)` should choose a threshold automatically.
- Add `scanpy[bbknn]`, `scanpy[scanorama]`, or other integration extras only when routing to external integration workflows, not for the core preprocessing wrappers here.
