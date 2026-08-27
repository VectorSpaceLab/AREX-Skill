---
name: multimodal-and-spatial
description: "Route scvi-tools tasks involving multimodal, ATAC, spatial,
  methylation, velocity, perturbation, contrastive, and external specialized
  model families."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# multimodal-and-spatial

Use this sub-skill when a user needs scvi-tools guidance for non-basic single-cell models beyond core RNA-only workflows: CITE-seq, RNA+protein, RNA+ATAC, ATAC-only, methylation, spatial mapping/deconvolution, velocity, perturbation/contrastive analysis, or external specialized models.

## Route by task

- RNA + protein CITE-seq: use `scvi.model.TOTALVI`; for semi-supervised labels with protein, use `scvi.external.TOTALANVI`.
- RNA + ATAC or RNA + ATAC + protein with partial modality overlap: use `scvi.model.MULTIVI` on `MuData`; for ATAC-only use `scvi.model.PEAKVI`.
- Spatial mapping or deconvolution: consider `scvi.external.Tangram`, `scvi.external.RNAStereoscope`, and `scvi.external.SpatialStereoscope`; verify reference labels before choosing Stereoscope.
- Bisulfite/methylation: use `scvi.external.METHYLVI` or `scvi.external.METHYLANVI` depending on whether labels are needed.
- Dynamics, perturbation, and contrastive designs: use `scvi.external.VELOVI`, `MRVI`, `RESOLVI`, `ContrastiveVI`, `SysVI`, `DIAGVI`, or `Decipher` only after matching their required data keys.
- Specialized external models: use `CYTOVI`, `SCAR`, `SCBASSET`, `GIMVI`, or `Tangram` when their input assumptions match; expect optional extras for some workflows.

## Use the references

- Model selection and APIs: [references/model-catalog.md](references/model-catalog.md)
- Required data keys and setup validation: [references/data-requirements.md](references/data-requirements.md)
- Failure diagnosis and recovery: [references/troubleshooting.md](references/troubleshooting.md)

## Boundaries

- For ordinary `AnnData` registration, `setup_anndata`, count layers, batches, labels, covariates, and `MuData` basics, route to the `data-setup` sub-skill first.
- For choosing among core RNA-only models such as `SCVI`, `SCANVI`, `LinearSCVI`, `AUTOZI`, or `SOLO`, route to the `core-models` sub-skill.
- Do not assume optional packages for spatial plotting, genomic sequence models, or external integrations are installed unless imports prove it.
