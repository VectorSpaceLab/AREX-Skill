---
name: annotation-and-query
description: "Use for scvi-tools label transfer, query/reference mapping,
  semi-supervised annotation, doublet detection, and marker-based cell
  assignment with SCANVI, SOLO, and CellAssign."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# annotation-and-query

Use this sub-skill when the task is to annotate cells, transfer labels from a reference, map query data into a trained reference, detect doublets, or assign cell types from marker genes.

## Route here for

- Semi-supervised annotation with `scvi.model.SCANVI`, including `labels_key`, `unlabeled_category`, `SCANVI.from_scvi_model(...)`, and `model.predict(...)`.
- Query/reference workflows that start from a trained `SCVI` reference and then initialize `SCANVI` for label transfer.
- Doublet detection with `scvi.external.SOLO.from_scvi_model(...)`, `SOLO.train(...)`, and `SOLO.predict(...)`.
- Marker-based cell assignment with `scvi.external.CellAssign`, binary marker matrices, and soft assignment probabilities.
- Annotation validation, including prediction confidence, ambiguous cells, unseen labels, and marker-gene alignment checks.

## Do not route here for

- Generic `train(...)`, checkpointing, accelerators, early stopping, or dataloader tuning unless annotation-specific behavior is the core issue; route to training-and-inference coverage when available.
- General model selection among `SCVI`, `SCANVI`, `TOTALVI`, or other model families; route to core-models coverage when available.
- Spatial or multimodal specialized annotation workflows; route to multimodal-and-spatial coverage when available.

## Start points

- For SCANVI label transfer and query/reference patterns, read `references/workflows.md`.
- For exact constructors, setup methods, prediction outputs, and validation checks, read `references/api-reference.md`.
- For common label, marker, and SOLO failures, read `references/troubleshooting.md`.

## Quick decision guide

- If labels exist for some cells and one category marks unknown cells, use `SCANVI.setup_anndata(..., labels_key=..., unlabeled_category=...)` or bootstrap from a trained `SCVI` with `SCANVI.from_scvi_model(...)`.
- If a trained `SCVI` reference exists and the goal is doublet calls, use `SOLO.from_scvi_model(scvi_model, restrict_to_batch=...)` and inspect soft doublet probabilities.
- If curated marker genes define expected cell types, use `CellAssign` after subsetting `adata` to marker genes and validating that marker matrix rows exactly cover `adata.var_names`.
- Always store both hard labels and uncertainty scores in `adata.obs`; avoid trusting only the argmax label when probabilities are diffuse.
