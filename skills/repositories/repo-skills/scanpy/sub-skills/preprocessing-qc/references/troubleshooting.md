# Preprocessing and QC Troubleshooting

## Raw counts were overwritten

Symptoms:

- QC totals reflect normalized or log-transformed values.
- `highly_variable_genes(..., flavor="seurat_v3")` warns that non-integers were found.
- Scrublet results change after normalization even though no simulated data were supplied.

Fix:

- Preserve counts before transforms: `adata.layers["counts"] = adata.X.copy()`.
- Run QC with `layer="counts"` or with `use_raw=True` only if `.raw` really contains the intended count matrix.
- Use `layer="counts"` for Seurat v3 HVG flavors.
- Use raw unnormalized counts for `scrublet` unless providing a consistently preprocessed `adata_sim`.

## Layer, raw, inplace, and copy confusion

Symptoms:

- A function returns `None` when a result was expected.
- `.X` changed but a layer did not, or a layer changed while `.X` stayed unchanged.
- `normalize_total(copy=True, inplace=False)` raises an error.
- Marker/reporting steps later cannot find pre-HVG expression values.

Fix:

- For `calculate_qc_metrics`, use `inplace=False` for returned data frames or `inplace=True` to write `.obs`/`.var`.
- For `filter_cells` and `filter_genes`, use `inplace=False` to get masks and metric arrays before subsetting.
- For `normalize_total`, use `inplace=False` to get a dict or `copy=True` to get a copied `AnnData`; do not combine them.
- For `log1p`, `scale`, `regress_out`, and `pca`, use `copy=True` only when a copied result is intended.
- Treat `.raw` as a log-normalized analysis snapshot for downstream reporting; treat `layers["counts"]` as the raw-count preservation slot.

## Sparse matrices become dense or memory spikes

Symptoms:

- Memory grows sharply during `scale`, `regress_out`, ComBat, or PCA.
- A sparse `.X` becomes a dense array.
- A warning mentions zero-centering sparse matrices.

Fix:

- Use `sc.pp.scale(adata, zero_center=False)` when sparse preservation is more important than centering.
- Avoid `regress_out` on very large sparse matrices unless densification is acceptable.
- Expect ComBat to use dense-style operations.
- For PCA, keep component counts modest and consider `zero_center=False` only when truncated-SVD style behavior is acceptable.

## Dask or lazy arrays compute unexpectedly

Symptoms:

- `normalize_total` triggers computation on a Dask-backed matrix.
- Logging or chunked operations do not behave the same for layers as for `.X`.

Fix:

- `normalize_total` can call `.compute()` when `exclude_highly_expressed=True`, when normalizing layers, or when `key_added` is used.
- Avoid those options for lazy exploratory passes, or materialize intentionally before preprocessing.
- `log1p(chunked=True)` applies to `AnnData.X`, not layers or `obsm` entries.
- QC functions may require CSR-like Dask chunks; CSC-style sparse Dask inputs can fail.

## Filtering removes all cells or genes

Symptoms:

- HVG, scaling, PCA, or Scrublet fails after QC filtering.
- Matrix shape becomes zero in one dimension.
- Tiny examples fail despite valid code for real datasets.

Fix:

- Apply one threshold per call and inspect `adata.shape` after every filter.
- Use permissive thresholds such as `min_counts=1` or `min_cells=1` for smoke fixtures.
- Preview masks with `inplace=False` before mutating the object.
- Recalculate QC metrics after major filtering when thresholds depend on updated totals.

## `percent_top` is too large

Symptoms:

- `calculate_qc_metrics` raises an index-related error on a small matrix.

Fix:

- Keep every requested `percent_top` value positive and no larger than `adata.n_vars`.
- Use `percent_top=None`, `percent_top=[]`, or small values such as `(1, 2)` for tiny fixtures.

## HVG optional dependency or flavor mismatch

Symptoms:

- `ImportError` mentions `skmisc`, `scikit-misc`, or `loess`.
- Seurat v3 HVG warns about non-integer values.
- Batch-aware HVG selects unexpected genes or columns are missing.
- `cell_ranger` fails on tiny matrices with duplicate bin edges.

Fix:

- Install `scanpy[skmisc]` only when Seurat v3 HVG is required.
- Use raw integer counts for `seurat_v3` and `seurat_v3_paper`; use log-normalized data for `seurat` or `cell_ranger`.
- Pass `batch_key=` only when batch labels are meaningful and sufficiently populated.
- On tiny examples, use `flavor="seurat"`, set `n_top_genes` below `adata.n_vars`, and avoid over-filtering.

## PCA component count or mask fails

Symptoms:

- PCA fails after HVG selection or filtering.
- `.obsm["X_pca"]` is missing after a PCA call.
- The number of returned components is smaller than expected.

Fix:

- Set `n_comps` below the effective minimum of selected cells and genes.
- Check whether `.var["highly_variable"]` selected too few genes; use `mask_var=None` to use all genes.
- Check custom `key_added=` values; PCA outputs move away from the default `.obsm["X_pca"]`/`.varm["PCs"]`/`.uns["pca"]` names.
- Use `n_comps=1` or `2` for tiny smoke fixtures.

## Scrublet optional dependency or count assumptions

Symptoms:

- `scrublet` fails when `threshold=None`.
- Doublet score columns are missing.
- Results differ unexpectedly across batches or after normalization.

Fix:

- Install `scanpy[scrublet]` or `scikit-image`, or pass an explicit `threshold`.
- Use `batch_key=` for multiple samples so each batch is processed independently.
- Start from raw unnormalized counts unless supplying `adata_sim`.
- Confirm `.obs["doublet_score"]`, `.obs["predicted_doublet"]`, and `.uns["scrublet"]` after the call.

## Batch correction errors

Symptoms:

- ComBat cannot find the batch key or reports small/empty batches.
- ComBat returns a dense matrix and memory usage rises.
- Harmony does not create `X_pca_harmony`.

Fix:

- Confirm `key` exists in `adata.obs`, has categorical-like batch labels, and every batch has enough cells.
- Include biological covariates in ComBat for unbalanced designs when appropriate.
- Run `sc.pp.pca` before `sc.pp.harmony_integrate` and verify `.obsm["X_pca"]` or the chosen `basis=` exists.
- Use `use_rep="X_pca_harmony"` in downstream neighbors, then route graph work to `graph-embedding-analysis`.

## Sampling or downsampling changes conclusions

Symptoms:

- Results are not reproducible across runs.
- Normalization totals look wrong after downsampling.
- A final analysis accidentally used a prototype subset.

Fix:

- Set `rng` or `random_state` in examples and scripts.
- Downsample counts before normalization/log transforms.
- Store sampled objects separately or use `copy=True` when retaining the original dataset.
- Clearly label sampled results and avoid hidden sampling in final pipelines.
