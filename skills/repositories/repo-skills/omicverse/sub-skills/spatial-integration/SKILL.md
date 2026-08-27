---
name: spatial-integration
description: "Use for OmicVerse spatial transcriptomics, histology-to-spatial
  prediction, deconvolution, cell mapping, tissue zones, spatial IO, and
  spatial-adjacent multimodal integration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Spatial Integration

Use this sub-skill when the user needs OmicVerse help with spatial transcriptomics data, spatial readers, histology-to-spatial routes, spatial deconvolution or mapping, spatially variable genes, tissue zones, spatial communication, bulk/single/spatial integration, or epigenomics workflows that feed spatial interpretation.

Start at the [root routing skill](../../SKILL.md) if the task may belong to another OmicVerse domain.

## Route Here

- Read or validate spatial inputs: 10x Visium/Visium HD, Xenium, NanoString/CosMx, Atera, or AnnData objects with `obsm['spatial']`.
- Build spatial neighborhoods, compute Moran/Geary statistics, select spatially variable genes, crop/rotate/map spatial images, or plot spatial coordinates/segmentations.
- Map scRNA-seq references to spatial spots or cells with `Tangram`, `Deconvolution`, `CellMap`, `CellLoc`, `Single2Spatial`, or related cell-composition helpers.
- Derive tissue zones from cell-abundance matrices, run cell-type split purification/balancing, or spatialize communication results.
- Gate optional heavy routes: `pySTAGATE`, `pySTAligner`, `pySpaceFlow`, `CAST`, `cellcharter`, `STT`, GASTON, cell2location/RCTD, and `ov.space.histo`.
- Use `ov.epi` or `ov.bulk2single` when ATAC/multiome or bulk-to-single/spatial outputs become spatial inputs.

## Route Elsewhere

- Generic AnnData reading, QC, normalization, PCA, neighbors, UMAP, or plotting basics: [core analysis](../core-analysis/SKILL.md).
- Single-cell annotation, marker ranking, batch integration, trajectory, or communication before spatial projection: [single-cell workflows](../single-cell-workflows/SKILL.md).
- Bulk RNA-seq, enrichment, metabolomics, proteomics, or microbiome table statistics that do not become spatial maps: [multiomics statistics](../multiomics-statistics/SKILL.md).
- FASTQ alignment, Space Ranger execution, external binary pipelines, GWAS, AIRR, or molecular/docking work: [specialist domains](../specialist-domains/SKILL.md).

## Safe First Step

Before running heavy spatial models, validate the file layout or AnnData slots:

```bash
python sub-skills/spatial-integration/scripts/check_spatial_inputs.py --kind auto --path PATH_TO_INPUT
python sub-skills/spatial-integration/scripts/check_spatial_inputs.py --kind h5ad --path spatial.h5ad
python sub-skills/spatial-integration/scripts/check_spatial_inputs.py --kind nanostring --path SAMPLE_DIR --counts-file exprMat.csv --meta-file metadata.csv
```

Expected success signal: `ERRORS: 0`. Warnings are common for optional images, boundaries, or caches and should be reviewed before plotting or segmentation.

## Reference Map

- Use [spatial workflows](references/spatial-workflows.md) for end-to-end recipes and model gating.
- Use [API reference](references/api-reference.md) for concrete OmicVerse functions, signatures, inputs, and outputs.
- Use [data formats](references/data-formats.md) for Visium HD, Xenium, NanoString, and AnnData slot contracts.
- Use [troubleshooting](references/troubleshooting.md) for missing images, coordinate mismatch, optional dependency, GPU/backend, and deconvolution reference errors.

## Operating Rules

- Never run histology prediction, cell2location, RCTD, Tangram training, `CAST`, or torch-geometric methods as a default smoke check; validate inputs first and ask for explicit runtime/backend choices.
- Prefer `load_image=False` or bounded `image_max_dim` for Xenium morphology and WSI-scale data until the user confirms memory budget.
- Confirm gene intersection between reference and spatial data before training mapping/deconvolution models; report the number of shared genes and dropped features.
- Keep `obsm['spatial']`, `uns['spatial']`, `obs['geometry']`, `layers['counts']`, and method-specific `obsm` outputs explicit in handoffs.
- Treat optional downloads, model weights, Hugging Face access, GPU use, and large tile caches as opt-in operations.
