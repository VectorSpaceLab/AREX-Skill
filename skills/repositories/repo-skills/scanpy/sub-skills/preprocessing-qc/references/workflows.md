# Preprocessing and QC Workflows

These workflows assemble Scanpy preprocessing steps while keeping matrix state, `AnnData` slots, optional dependencies, and handoffs explicit.

## QC and filtering

1. Start with cells in `.obs_names`, genes in `.var_names`, and raw count-like values in `.X` or a named layer.
2. Preserve counts if later steps will overwrite `.X`: `adata.layers["counts"] = adata.X.copy()`.
3. Mark QC gene groups in `.var`, for example mitochondrial genes with `adata.var["mito"] = adata.var_names.str.upper().str.startswith("MT-")`.
4. Compute QC metrics from the intended representation:

```python
sc.pp.calculate_qc_metrics(
    adata,
    qc_vars=["mito"],
    percent_top=(50, 100, 200, 500),
    layer="counts",
    inplace=True,
)
```

5. Inspect `.obs["total_counts"]`, `.obs["n_genes_by_counts"]`, `.obs["pct_counts_mito"]`, and `.var["n_cells_by_counts"]` before filtering.
6. Apply one filter threshold per call, checking shape after each call:

```python
sc.pp.filter_cells(adata, min_genes=200)
sc.pp.filter_cells(adata, max_counts=50_000)
sc.pp.filter_genes(adata, min_cells=3)
```

Use `inplace=False` to preview masks before subsetting:

```python
cell_mask, n_genes = sc.pp.filter_cells(adata, min_genes=200, inplace=False)
gene_mask, n_cells = sc.pp.filter_genes(adata, min_cells=3, inplace=False)
```

For tiny fixtures, reduce `percent_top` to values no larger than `adata.n_vars`, such as `(1, 2)`, or set `percent_top=None`.

## Normalization, log, and layers

A robust explicit pipeline is:

```python
adata.layers["counts"] = adata.X.copy()
sc.pp.calculate_qc_metrics(adata, qc_vars=["mito"], layer="counts", inplace=True)
sc.pp.normalize_total(adata, target_sum=1e4, key_added="size_factor")
sc.pp.log1p(adata)
```

Important semantics:

| Function | Default mutation | Return pattern | Representation notes |
|---|---|---|---|
| `normalize_total` | Updates `.X` when `inplace=True` | Returns `None`; with `inplace=False`, returns a dict with normalized arrays and normalization factors; with `copy=True`, returns copied `AnnData` | Supports `layer=` and `obsm=`. `copy=True` is incompatible with `inplace=False`. |
| `log1p` | Updates input unless `copy=True` | Returns copied object/array only with `copy=True` | Supports `layer=` and `obsm=`. Chunking applies only to `AnnData.X`, not layers or `obsm`. |
| `calculate_qc_metrics` | Does not mutate unless `inplace=True` | Returns `(obs_metrics, var_metrics)` with `inplace=False` | Supports `layer=` or `use_raw=True`. |

`normalize_total(target_sum=None)` scales cells to the median pre-normalization total. `exclude_highly_expressed=True` changes size-factor calculation and can trigger Dask computation when combined with lazy arrays, layer paths, or `key_added`.

## Highly variable genes

For log-normalized workflows:

```python
sc.pp.highly_variable_genes(
    adata,
    flavor="seurat",
    n_top_genes=2000,
    batch_key="batch",  # optional
    inplace=True,
)
adata = adata[:, adata.var["highly_variable"]].copy()
```

Flavor guidance:

| Flavor | Input expectation | Notes |
|---|---|---|
| `seurat` | Log-normalized data | Default dispersion-style workflow; can use cutoffs or `n_top_genes`. |
| `cell_ranger` | Log-normalized data | Common with `n_top_genes`; more sensitive to duplicate bin edges on small or sparse examples. |
| `seurat_v3` | Raw integer counts | Requires optional `scanpy[skmisc]`; use `n_top_genes`; with `batch_key`, ranks by median rank then number of batches. |
| `seurat_v3_paper` | Raw integer counts | Requires optional `scanpy[skmisc]`; with `batch_key`, tie-breaking follows the Seurat paper behavior. |

When counts are preserved in a layer, use that layer for raw-count HVG flavors while keeping `.X` log-normalized for downstream PCA:

```python
sc.pp.highly_variable_genes(
    adata,
    flavor="seurat_v3",
    layer="counts",
    n_top_genes=2000,
    batch_key="batch",
)
```

With `batch_key`, Scanpy merges per-batch HVG results and can add `highly_variable_nbatches` and `highly_variable_intersection` columns.

## Scaling, regression, and PCA

A standard post-HVG sequence is:

```python
adata.raw = adata.copy()  # optional snapshot after log normalization and before HVG subsetting
adata = adata[:, adata.var["highly_variable"]].copy()
sc.pp.regress_out(adata, ["total_counts", "pct_counts_mito"])
sc.pp.scale(adata, max_value=10)
sc.pp.pca(adata, n_comps=50, svd_solver="arpack")
```

Operational notes:

- `adata.raw = adata.copy()` preserves log-normalized values for marker visualization/reporting; it is not a substitute for raw count preservation in `layers["counts"]`.
- `regress_out` uses linear regression, can remove biological signal, and can densify sparse matrices.
- `scale` writes `.var["mean"]` and `.var["std"]` by default, or mask-specific mean/std columns when `mask_obs` is used; `zero_center=False` is sparse-friendly, while `zero_center=True` centers and densifies sparse input.
- `pca` writes `.obsm["X_pca"]`, `.varm["PCs"]`, and `.uns["pca"]`; `key_added="custom"` writes `.obsm["custom"]`, `.varm["custom"]`, and `.uns["custom"]`-style PCA metadata.
- If `.var["highly_variable"]` exists, PCA uses that mask by default; set `mask_var=None` to use all genes.
- Keep `n_comps` below the effective minimum dimension of the matrix. Tiny fixtures often need `n_comps=1` or `2`.
- After PCA or Harmony, route graph construction, UMAP, clustering, diffusion maps, marker ranking, and graph diagnostics to `graph-embedding-analysis`.

## Sampling and downsampling

Use sampling for quick prototypes or memory-bounded preprocessing, not as a hidden step in final analyses.

```python
sc.pp.sample(adata, n=10_000, axis=0, rng=0)       # sample cells
sc.pp.downsample_counts(adata, counts_per_cell=5_000, rng=0)
```

Guidance:

- Use `sc.pp.sample(..., copy=True)` when the original object must remain unchanged.
- Choose exactly one of `n` or `fraction` for `sample`.
- Choose `counts_per_cell` or `total_counts` for `downsample_counts`, not both.
- Run downsampling on count-like data before normalization/log transforms.
- Prefer reproducible `rng` values in examples, tests, and handoff scripts.

## Basic batch correction

| Method | Use when | Required state | Output |
|---|---|---|---|
| `sc.pp.combat(adata, key="batch", covariates=None)` | Correct expression matrix for a categorical batch covariate in a simple design | Batch key in `.obs`; each batch has enough cells; dense output is acceptable | Replaces `.X` by default or returns corrected array with `inplace=False`. |
| `sc.pp.harmony_integrate(adata, key="batch")` | Correct PCA embeddings before neighbor graph construction | PCA already stored in `.obsm["X_pca"]` or another `basis=` | Writes `.obsm["X_pca_harmony"]` by default. |

ComBat operates on the expression matrix and can remove biological signal in unbalanced designs unless relevant covariates are included. Harmony operates on embeddings; after Harmony, call neighbors with `use_rep="X_pca_harmony"` and use the graph/embedding sub-skill for downstream details.

## Doublet detection

Use `sc.pp.scrublet` on raw unnormalized counts from one sample or comparable batches:

```python
sc.pp.scrublet(
    adata,
    batch_key="sample",        # optional
    expected_doublet_rate=0.05,
    n_prin_comps=30,
    threshold=0.25,             # explicit threshold avoids auto-threshold optional dependency
    rng=0,
)
```

Results are stored in `.obs["doublet_score"]`, `.obs["predicted_doublet"]`, and `.uns["scrublet"]`. If `threshold=None`, automatic thresholding requires `scikit-image` through `scanpy[scrublet]` or a separate install.

For manual simulation workflows:

```python
adata.layers["counts"] = adata.X.copy()
adata_sim = sc.pp.scrublet_simulate_doublets(adata, layer="counts", rng=0)
# preprocess observed and simulated data consistently, then:
sc.pp.scrublet(adata, adata_sim=adata_sim, threshold=0.25, rng=0)
```

Keep observed and simulated genes aligned after filtering/HVG selection.

## Recipes

| Recipe | Expected input | Main behavior | Use cautiously when |
|---|---|---|---|
| `sc.pp.recipe_seurat` | Non-log data unless `log=False` | Filters, normalizes to `1e4`, log-transforms, selects HVGs, scales | You need explicit layer preservation or custom QC thresholds. |
| `sc.pp.recipe_zheng17` | Non-log data unless `log=False` | Filters genes by counts, normalizes, applies `cell_ranger` HVG logic, renormalizes after filtering, scales | Small matrices or sparse genes trigger HVG edge cases. |
| `sc.pp.recipe_weinreb17` | Dense non-log data unless `log=False` | Normalizes, filters by CV/Fano-style logic, runs PCA | Input is sparse or memory constrained. |

Prefer explicit pipelines when debugging or when a downstream agent must know which matrix each step used.
