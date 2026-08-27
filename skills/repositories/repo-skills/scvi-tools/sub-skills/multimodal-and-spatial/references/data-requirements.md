# Data requirements for multimodal and spatial models

Use this reference after basic `AnnData` or `MuData` setup decisions are made. Validate matrix shapes, keys, and modality overlap before calling model setup.

## Common validation checklist

- Counts: use raw nonnegative count matrices for RNA, protein, ATAC, methylated counts, coverage, and spatial counts unless a model explicitly accepts transformed values.
- Containers: use `MuData` for new multimodal workflows; reserve single `AnnData` setups for ATAC-only, legacy CITE-seq, or external models that only define `setup_anndata`.
- Batch keys: confirm `batch_key`, `panel_key`, `labels_key`, `sample_key`, and covariate keys exist in `.obs` of the correct modality or global `mdata.obs` location expected by setup.
- Layers: when passing `layer`, `rna_layer`, `protein_layer`, `atac_layer`, `mc_layer`, or `cov_layer`, confirm the layer exists and has the same shape as that modality’s `.X`.
- Features: align gene names across scRNA and spatial modalities before Stereoscope, Tangram, or GIMVI; align peak features for ATAC query/reference mapping.
- Optional dependencies: before running external models with specialized backends, test imports for packages such as `muon`, `pyro`, sequence/genomic tooling, or spatial plotting libraries as needed.

## `TOTALVI` data

Preferred setup:

```python
scvi.model.TOTALVI.setup_mudata(
    mdata,
    rna_layer="counts",
    protein_layer="counts",
    batch_key="batch",
    panel_key=None,
    modalities={"rna_layer": "rna", "protein_layer": "protein"},
)
```

Required structure:

- `mdata.mod["rna"]` contains cells by genes and raw RNA counts in `.X` or `layers[rna_layer]`.
- `mdata.mod["protein"]` contains cells by proteins and protein counts in `.X` or `layers[protein_layer]`.
- `modalities` maps setup parameter names to actual modality names.
- `panel_key` is useful when batches have different antibody panels; values should identify measured panels.
- `size_factor_key` is optional and should point to a numeric observation column if used.

Legacy single-`AnnData` setup requires `protein_expression_obsm_key` in `.obsm` and optionally `protein_names_uns_key` in `.uns`. If the `.obsm` protein matrix is a pandas `DataFrame`, column names can serve as protein names.

## `MULTIVI` data

Preferred setup:

```python
scvi.model.MULTIVI.setup_mudata(
    mdata,
    rna_layer="counts",
    atac_layer="counts",
    protein_layer=None,
    batch_key="batch",
    size_factor_key=None,
    modalities={"rna_layer": "rna", "atac_layer": "atac"},
)
```

Required structure:

- Include at least RNA or ATAC modality; include paired multiome cells when possible to learn cross-modality translation.
- RNA features are genes; ATAC features are peaks/regions; protein features are antibody tags if supplied.
- Partial modality overlap is allowed, but cell indices and modality membership must be intentional. Avoid accidental non-overlap caused by inconsistent barcodes.
- If `size_factor_key` is used, it points to `mdata.obsm`; the first column is RNA size factors and the second is ATAC size factors, with ATAC normalized between 0 and 1.
- `MULTIVI.setup_mudata` reorders modalities internally to canonical RNA, ATAC, protein order; avoid relying on pre-existing modality order for downstream assumptions.

For the hard case “RNA/protein/ATAC with partial modality overlap,” first decide whether the biological question needs protein outputs. If yes, include all three modalities in `MULTIVI`; if the key output is denoised protein with mostly paired CITE-seq data, use `TOTALVI` for RNA+protein and a separate ATAC model.

## `PEAKVI` data

Setup:

```python
scvi.model.PEAKVI.setup_anndata(
    adata,
    batch_key="batch",
    labels_key=None,
    categorical_covariate_keys=None,
    continuous_covariate_keys=None,
    layer="counts",
)
```

Required structure:

- `adata` is cells by peaks/regions.
- `.X` or `layers["counts"]` contains binary accessibility or count data.
- Peaks should be harmonized before reference/query mapping; feature order and names matter when loading query data.
- `labels_key` is optional and used for metadata-aware workflows, not required for unsupervised accessibility modeling.

## Spatial data

For Stereoscope:

- Single-cell reference: `RNAStereoscope.setup_anndata(sc_adata, labels_key="cell_type", layer="counts")` requires a categorical label column.
- Spatial target: `SpatialStereoscope.setup_anndata(st_adata, layer="counts")` requires spatial expression counts.
- Gene overlap should be checked and subset deliberately before setup.
- If reference labels are missing, do not fabricate them; ask for labels, run a separate annotation workflow, or choose a model not requiring labels.

For Tangram:

- Use `Tangram.setup_mudata(mdata, sc_layer=..., sp_layer=..., density_prior_key=..., modalities={"sc_layer": "sc", "sp_layer": "spatial", "density_prior_key": "spatial"})`.
- `density_prior_key` can be an observation key in the spatial modality or an accepted string prior such as `"rna_count_based"` or `"uniform"`.
- Confirm the single-cell and spatial modalities share the intended genes and comparable preprocessing.

## Methylation data

For `METHYLVI` and `METHYLANVI`, use methylated-count and coverage layers in one or more methylation-context modalities:

```python
scvi.external.METHYLVI.setup_mudata(
    mdata,
    mc_layer="mc",
    cov_layer="cov",
    methylation_contexts=["mCG", "mCH"],
    batch_key="batch",
    modalities={"batch_key": "mCG"},
)
```

For `METHYLANVI`, also pass `labels_key` and `unlabeled_category`. Validate that `mc_layer <= cov_layer` elementwise where coverage is nonzero, both layers are nonnegative, and both layers share identical shape and feature names in each listed methylation context.

## Velocity data

For `VELOVI`, use normalized spliced and unspliced expression layers:

```python
scvi.external.VELOVI.setup_anndata(
    adata,
    spliced_layer="spliced",
    unspliced_layer="unspliced",
)
```

Confirm both layers exist, have the same shape as `.X`, and contain nonnegative expression values from a consistent velocity preprocessing workflow. Store velocity outputs in `.layers`, `.obs`, or `.var` only after checking method return shapes.

## Contrastive and perturbation data

- `ContrastiveVI` needs target and background cell definitions; keep boolean masks or index arrays reproducible and non-overlapping.
- `MRVI` needs sample or perturbation metadata; verify repeated observations per sample/condition before training.
- `RESOLVI` is spatial/noise oriented; confirm spot-level metadata and count assumptions.
- `SysVI` needs system or batch factors that should be corrected; do not use it when the “system” column is confounded with the biology of interest.
- `DIAGVI` supports both `AnnData` and `MuData`; choose setup based on data container and verify class documentation for required diagnostic labels or modalities.

## External-model import pattern

```python
try:
    import scvi
    from scvi import external
except ImportError as error:
    raise RuntimeError("Install scvi-tools before running this workflow") from error

required = ["TOTALVI", "MULTIVI", "PEAKVI"]
missing = [name for name in required if not hasattr(scvi.model, name)]
if missing:
    raise RuntimeError(f"scvi.model is missing expected classes: {missing}")
```

For optional external models, check `hasattr(scvi.external, "ModelName")` and perform a tiny setup dry run on a copied subset before launching expensive training.
