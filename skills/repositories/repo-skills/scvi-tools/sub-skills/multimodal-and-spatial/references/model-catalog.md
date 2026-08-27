# Multimodal and spatial model catalog

This reference maps specialized scvi-tools questions to concrete model classes, setup calls, training outputs, and validation checks. Import core multimodal classes from `scvi.model`; import specialized families from `scvi.external`.

## Anchor models

### `scvi.model.TOTALVI`

Use for paired RNA + protein CITE-seq and protein-aware batch integration.

```python
import scvi
scvi.model.TOTALVI.setup_mudata(
    mdata,
    rna_layer=None,
    protein_layer=None,
    batch_key="batch",
    panel_key=None,
    modalities={"rna_layer": "rna", "protein_layer": "protein"},
)
model = scvi.model.TOTALVI(mdata, n_latent=20)
model.train()
latent = model.get_latent_representation()
rna, protein = model.get_normalized_expression(n_samples=10)
```

Use `setup_anndata(adata, protein_expression_obsm_key=..., protein_names_uns_key=..., batch_key=..., panel_key=...)` only for legacy single-`AnnData` CITE-seq. Prefer `setup_mudata` for new work. Use `panel_key` when antibody panels differ by batch; initialize with `override_missing_proteins=True` only when missing protein panels are expected and deliberate.

Common outputs: `get_latent_representation()`, `get_normalized_expression()`, `differential_expression()`, `posterior_predictive_sample()`. Protein denoising options include `include_protein_background` and `sampling_protein_mixing` in normalized expression calls.

### `scvi.model.MULTIVI`

Use for multiome integration, missing-modality imputation, RNA + ATAC, or RNA + ATAC + protein with partially overlapping observations. `MULTIVI.setup_anndata` is deprecated in scvi-tools 1.4; use `MuData`.

```python
import scvi
scvi.model.MULTIVI.setup_mudata(
    mdata,
    rna_layer=None,
    atac_layer=None,
    protein_layer=None,
    batch_key="batch",
    size_factor_key=None,
    modalities={"rna_layer": "rna", "atac_layer": "atac", "protein_layer": "protein"},
)
model = scvi.model.MULTIVI(mdata, n_latent=20, gene_likelihood="zinb")
model.train()
mdata.obsm["X_multivi"] = model.get_latent_representation()
rna = model.get_normalized_expression()
atac = model.get_normalized_accessibility(n_samples_overall=10)
```

`modalities` maps setup argument names to `mdata.mod` keys. For RNA + ATAC only, omit `protein_layer`. For RNA + protein without ATAC, prefer `TOTALVI` unless the task specifically needs MultiVI-style missing modality handling.

Common outputs: latent representation, `get_normalized_expression()`, `get_normalized_accessibility()`, `differential_expression()`, and `differential_accessibility()`. Use `transform_batch` for counterfactual batch decoding when supported by the output method.

### `scvi.model.PEAKVI`

Use for ATAC-only accessibility modeling, latent embedding, transfer learning, and differential accessibility.

```python
import scvi
scvi.model.PEAKVI.setup_anndata(
    adata,
    batch_key="batch",
    labels_key=None,
    layer="counts",
)
model = scvi.model.PEAKVI(adata, n_latent=10, encode_covariates=False)
model.train()
adata.obsm["X_peakvi"] = model.get_latent_representation()
access = model.get_normalized_accessibility(use_z_mean=True)
da = model.differential_accessibility(groupby="cell_type")
```

Input can be binary or count accessibility. Ensure features are genomic regions/peaks, not genes. Use `PEAKVI.load_query_data(query_adata, reference_dir)` for scArches-style query mapping after a reference model is saved.

## Spatial models

### `scvi.external.RNAStereoscope` and `SpatialStereoscope`

Use for spatial deconvolution when a labeled single-cell RNA reference is available and the spatial data has overlapping genes.

```python
import scvi
scvi.external.RNAStereoscope.setup_anndata(sc_adata, labels_key="cell_type", layer="counts")
rna_model = scvi.external.RNAStereoscope(sc_adata)
rna_model.train()

scvi.external.SpatialStereoscope.setup_anndata(st_adata, layer="counts")
spatial_model = scvi.external.SpatialStereoscope.from_rna_model(st_adata, rna_model)
spatial_model.train()
st_adata.obsm["stereoscope_proportions"] = spatial_model.get_proportions()
```

Do not use Stereoscope if reference labels are missing or unreliable. First create or validate a `labels_key` in the single-cell reference; otherwise choose label-free mapping such as `Tangram` or ask for a labeled reference.

### `scvi.external.Tangram`

Use for mapping single-cell profiles to spatial locations with scRNA and spatial modalities in `MuData`.

```python
import scvi
scvi.external.Tangram.setup_mudata(
    mdata,
    density_prior_key="rna_count_based",
    sc_layer="counts",
    sp_layer="counts",
    modalities={"sc_layer": "sc", "sp_layer": "spatial", "density_prior_key": "spatial"},
)
model = scvi.external.Tangram(mdata)
model.train()
```

`density_prior_key` may be an observation column in the spatial modality or one of `"rna_count_based"` or `"uniform"`. Check that genes are aligned before setup.

## Methylation models

### `scvi.external.METHYLVI` and `METHYLANVI`

Use for single-cell bisulfite sequencing. `METHYLVI` is unsupervised; `METHYLANVI` is semi-supervised.

```python
import scvi
scvi.external.METHYLVI.setup_mudata(
    mdata,
    mc_layer="mc",
    cov_layer="cov",
    methylation_contexts=["mCG", "mCH"],
    batch_key="batch",
    modalities={"batch_key": "mCG"},
)
model = scvi.external.METHYLVI(mdata)
model.train()
```

For `METHYLANVI`, call `setup_mudata(..., labels_key="cell_type", unlabeled_category="Unknown", methylation_contexts=[...])`. Validate that methylated counts and coverage are nonnegative integer matrices of the same shape for every methylation context.

## Perturbation, contrastive, and representation models

- `scvi.external.MRVI`: use for multi-sample or perturbation response modeling. Setup with `MRVI.setup_anndata(adata, sample_key=..., batch_key=..., labels_key=...)`; require a meaningful sample or perturbation key.
- `scvi.external.RESOLVI`: use for spatial transcriptomics noise/bias modeling. Setup with `RESOLVI.setup_anndata(adata, layer=..., batch_key=...)`; verify spatial assay assumptions and count data.
- `scvi.external.ContrastiveVI`: use for target-versus-background latent factor analysis. Setup with `ContrastiveVI.setup_anndata(adata, layer=..., batch_key=...)`; initialize with `ContrastiveVI(adata)` and pass target/background indices through its training/data-splitting API.
- `scvi.external.SysVI`: use for system-factor correction in expression data. Setup with `SysVI.setup_anndata(adata, batch_key=..., layer=...)`; inspect latent results for biology-versus-system separation.
- `scvi.external.DIAGVI`: use for diagnostic or modality-aware tasks that support both `setup_anndata` and `setup_mudata`; pick the setup method matching the container type.
- `scvi.external.Decipher`: use for derailed-state or trajectory-oriented representation workflows. It is Pyro-backed; confirm `pyro` imports before recommending execution.

## Other specialized external models

- `scvi.external.CYTOVI`: cytometry-oriented VAE family; setup with `CYTOVI.setup_anndata(adata, layer=..., batch_key=...)` and validate marker panels.
- `scvi.external.GIMVI`: integrates spatial and scRNA expression with paired gene sets; use when a GIMVI-specific workflow is requested rather than general spatial deconvolution.
- `scvi.external.SCAR`: ambient RNA removal; requires an `ambient_profile` at model initialization, so do not suggest it without an ambient profile or a preprocessing path to estimate one.
- `scvi.external.SCBASSET`: sequence-based scATAC model; verify DNA sequence/peak representation requirements and optional dependencies before use.
- `scvi.external.TOTALANVI`: semi-supervised extension of `TOTALVI`; choose for CITE-seq with labels and unlabeled cells.

## Selection heuristics

- If all cells have RNA and protein, choose `TOTALVI`; if proteins are missing by panel, still choose `TOTALVI` with `panel_key` or missing-protein handling.
- If cells include RNA-only, ATAC-only, and paired multiome observations, choose `MULTIVI` and preserve modality-specific `MuData` keys.
- If the request says “spatial deconvolution” and has reference cell types, choose Stereoscope; if labels are missing, stop and request labels or choose Tangram-style mapping.
- If the request says “ATAC differential accessibility” without RNA, choose `PEAKVI`; if it includes RNA+ATAC, choose `MULTIVI` and use its `differential_accessibility()`.
- If the model is in `scvi.external`, warn that API stability and optional dependencies may be narrower than core `scvi.model` classes.
