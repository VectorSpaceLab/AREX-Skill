# Data Formats for scvi-tools Setup

## AnnData Basics

- Use `anndata.AnnData` for single-modality RNA, ATAC, or CITE-seq data represented as one observation axis.
- `adata.X` is the default count matrix; pass `layer="counts"` when raw counts live in `adata.layers["counts"]`.
- `adata.obs` stores per-cell annotations such as `batch_key`, `labels_key`, categorical covariates, continuous covariates, and `panel_key`.
- `adata.var_names` must be stable across query/reference transfer workflows; setup records the number and names of variables in the registry.
- `adata.obsm` stores aligned per-cell matrices such as `protein_expression`, `accessibility`, spatial `coordinates`, embeddings, or size-factor matrices.
- `adata.uns` can store global metadata such as `protein_names` when protein expression is a NumPy array in `obsm` rather than a DataFrame with columns.

## Raw Count Expectations

Most scvi-tools model setup fields use `LayerField(..., is_count_data=True)`. Non-negative integer raw counts are expected in `adata.X`, selected layers, and modality layers. Normalized, log-transformed, scaled, or negative-valued matrices can trigger warnings and can make model assumptions invalid even if setup completes.

Safe preflight checks:

```python
assert adata.n_obs > 0 and adata.n_vars > 0
assert "batch" in adata.obs
assert "counts" in adata.layers or adata.X is not None
assert adata.obs_names.is_unique and adata.var_names.is_unique
```

## scvi.data Readers

- `scvi.data.read_h5ad(path)` delegates to `anndata.read_h5ad` and returns an `AnnData` object.
- `scvi.data.read_csv(path)`, `scvi.data.read_loom(path)`, and `scvi.data.read_text(path)` delegate to `anndata.io` readers.
- `scvi.data.read_10x_atac(base_path)` expects `matrix.mtx`, `peaks.bed`, and `barcodes.tsv`; it returns `AnnData(data.tocsr(), var=coords, obs=cell_annot)` with peak names formatted as `chr:start-end` and `obs["batch_id"]` parsed from barcode suffixes.
- `scvi.data.read_10x_multiome(base_path)` expects `matrix.mtx`, `features.tsv`, and `barcodes.tsv`; it returns one `AnnData` with feature metadata in `var`, including `ID`, `modality`, `chr`, `start`, and `end` when present.

The 10x ATAC/multiome readers do not split modalities into `MuData`; after `read_10x_multiome`, split features by `adata.var["modality"]` if the target model expects separate RNA and ATAC modalities.

## Synthetic Fixtures

`scvi.data.synthetic_iid(batch_size=200, n_genes=100, n_proteins=100, n_regions=100, n_batches=2, n_labels=3, dropout_ratio=0.7, sparse_format=None, generate_coordinates=False, return_mudata=False, **kwargs)` creates test-only independent synthetic data.

For `return_mudata=False`, expected fields include:

- `adata.obs["batch"]` categorical labels like `batch_0`.
- `adata.obs["labels"]` categorical labels like `label_0` when `n_labels > 0`.
- `adata.obsm["protein_expression"]` and `adata.uns["protein_names"]` when `n_proteins > 0`.
- `adata.obsm["accessibility"]` when `n_regions > 0`.
- `adata.obsm["coordinates"]` when `generate_coordinates=True`.

For `return_mudata=True`, expected modalities include `mdata.mod["rna"]`, `mdata.mod["protein_expression"]`, and `mdata.mod["accessibility"]` depending on requested feature counts.

## MuData Conventions

Use `mudata.MuData` when modalities should remain separate, especially for `TOTALVI.setup_mudata` and `MULTIVI.setup_mudata`.

- `modalities` maps setup argument roles to MuData modality names, not file names.
- `{"rna_layer": "rna", "protein_layer": "protein_expression"}` means RNA counts are in `mdata.mod["rna"]` and protein counts are in `mdata.mod["protein_expression"]`.
- Include `"batch_key": "rna"` when `batch_key` is stored in `mdata.mod["rna"].obs`; omit it only when the shared key is in `mdata.obs` and accepted by the setup method.
- `MULTIVI.setup_mudata` reorders modalities internally to canonical RNA, ATAC, protein order when those roles are present.
- `AnnDataManager` validates that `MuData` is fully paired by default; observations should align across modalities unless a model explicitly supports a different layout.
