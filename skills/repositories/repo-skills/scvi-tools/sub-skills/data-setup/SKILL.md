---
name: data-setup
description: "Prepare AnnData and MuData inputs, readers, fixtures,
  preprocessing, setup_anndata/setup_mudata calls, and registry validation for
  scvi-tools models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# data-setup

Use this sub-skill when the task is about getting data into scvi-tools before model construction: AnnData/MuData shape, layers, `obs`/`obsm`/`varm`/`uns` keys, `scvi.data` readers, synthetic fixtures, preprocessing, `setup_anndata`, `setup_mudata`, or `AnnDataManager` validation.

Do not use this sub-skill for model choice, architecture parameters, training loops, callbacks, inference, differential expression, or spatial interpretation. Route those to the core model, multimodal/spatial, and training/inference sub-skills.

## Fast Path

1. Load or construct an `AnnData`/`MuData` object with raw non-negative integer counts in `adata.X`, `adata.layers[layer]`, or modality-specific `.X`/layers.
2. Confirm key existence before setup: `batch_key`, `labels_key`, covariate keys, protein `obsm`/`uns` keys, MuData modality names, and requested layers.
3. Call the model class setup method exactly once for the data object and model family, then instantiate the model with that same object.
4. Inspect `model.adata_manager.registry`, `model.adata_manager.data_registry`, and `model.adata_manager.summary_stats` when troubleshooting setup failures.

## Core Setup Patterns

- `scvi.model.SCVI.setup_anndata(adata, layer=None, batch_key=None, labels_key=None, size_factor_key=None, categorical_covariate_keys=None, continuous_covariate_keys=None)` for RNA counts in `X` or a count layer.
- `scvi.model.SCANVI.setup_anndata(adata, labels_key="cell_type", unlabeled_category="Unknown", layer=None, batch_key=None, size_factor_key=None, categorical_covariate_keys=None, continuous_covariate_keys=None)` for semi-supervised labels.
- `scvi.model.TOTALVI.setup_anndata(adata, protein_expression_obsm_key="protein_expression", protein_names_uns_key="protein_names", batch_key=None, panel_key=None, layer=None, size_factor_key=None, categorical_covariate_keys=None, continuous_covariate_keys=None)` for CITE-seq-style AnnData.
- Prefer `scvi.model.TOTALVI.setup_mudata(mdata, rna_layer=None, protein_layer=None, batch_key=None, panel_key=None, modalities={"rna_layer": "rna", "protein_layer": "protein_expression", "batch_key": "rna"})` for RNA + protein MuData.
- `scvi.model.PEAKVI.setup_anndata(adata, batch_key=None, labels_key=None, categorical_covariate_keys=None, continuous_covariate_keys=None, layer=None)` for chromatin accessibility counts.
- Prefer `scvi.model.MULTIVI.setup_mudata(mdata, rna_layer=None, atac_layer=None, protein_layer=None, batch_key=None, size_factor_key=None, idx_layer=None, modalities={"rna_layer": "rna", "atac_layer": "accessibility", "protein_layer": "protein_expression", "batch_key": "rna"})` for multiome or tri-modal data.

## Internal References

- Read [data formats](references/data-formats.md) for accepted matrix locations, reader outputs, and AnnData/MuData key conventions.
- Read [API reference](references/api-reference.md) for concrete scvi-tools setup, preprocessing, synthetic fixture, and registry APIs.
- Read [troubleshooting](references/troubleshooting.md) for missing keys, non-count warnings, MuData pairing errors, protein masks, and registry validation fixes.
- Use `scripts/create_tiny_anndata.py --help` to generate small local AnnData/MuData fixtures for setup smoke tests.
