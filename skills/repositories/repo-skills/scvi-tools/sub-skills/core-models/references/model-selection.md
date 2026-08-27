# Core Model Selection

## Decision Matrix

| User need | Recommended class | Required data | Setup notes | Common accessors after train |
|---|---|---|---|---|
| Unsupervised scRNA-seq integration, denoising, latent space, batch correction | `scvi.model.SCVI` | RNA counts in `adata.X` or a count `layer` | Optional `batch_key`, `labels_key`, size factors, categorical/continuous covariates | `get_latent_representation`, `get_normalized_expression`, `differential_expression` |
| Semi-supervised cell annotation with labeled and unlabeled cells | `scvi.model.SCANVI` | RNA counts plus label column containing an unlabeled category | `labels_key` and `unlabeled_category` are required; can also initialize from an `SCVI` model via `from_scvi_model` | `predict`, `get_latent_representation`, `get_normalized_expression` |
| CITE-seq RNA + surface protein modeling | `scvi.model.TOTALVI` | RNA counts plus protein expression in `adata.obsm` | `protein_expression_obsm_key` is required; optional `protein_names_uns_key`, `panel_key`, `batch_key` | `get_latent_representation`, `get_normalized_expression`, `get_normalized_protein_expression`, `differential_expression` |
| scATAC-seq accessibility modeling | `scvi.model.PEAKVI` | Binary or count peak accessibility matrix | Use ATAC matrix in `adata.X` or `layer`; optional batch/label/covariate keys | `get_latent_representation`, `get_accessibility_estimates`, `differential_accessibility` |
| Joint or mosaic RNA + ATAC, optionally with protein | `scvi.model.MULTIVI` | RNA/ATAC features in a combined AnnData-like matrix; optional protein in `obsm` | Set `n_genes` and `n_regions` at construction when ambiguous; optional `protein_expression_obsm_key` | `get_latent_representation`, `get_normalized_expression`, `get_accessibility_estimates` |
| Zero-inflation diagnostics for scRNA-seq | `scvi.model.AUTOZI` | RNA counts | Similar to SCVI setup, but focused on dropout/zero-inflation probabilities | `get_alphas_betas`, `get_normalized_expression`, `get_latent_representation` |
| Interpretable linear decoder variant of SCVI | `scvi.model.LinearSCVI` | RNA counts | Similar to SCVI setup with simpler decoder assumptions | `get_loadings`, `get_latent_representation`, `get_normalized_expression` |
| Deconvolution training precursor for DestVI | `scvi.model.CondSCVI` | Single-cell RNA counts with cell-type labels | `labels_key` should name cell types; optional `fine_labels_key` and `unlabeled_category` | Used by `DestVI.from_rna_model`; also supports latent/expression methods |
| Spatial transcriptomics deconvolution from a CondSCVI reference | `scvi.model.DestVI` | Spatial RNA counts plus trained `CondSCVI` reference | Call `DestVI.setup_anndata` on spatial data, then `DestVI.from_rna_model(st_adata, sc_model, ...)` | `get_proportions`, spatial deconvolution outputs |
| Topic modeling for count matrices | `scvi.model.AmortizedLDA` | Counts matrix, usually RNA or feature counts | `setup_anndata(adata, layer=None)`; uses Pyro SVI training | `get_latent_representation`, topic/feature methods depending on version |
| Apple Silicon MLX-backed SCVI-like workflow | `scvi.model.mlxSCVI` | RNA counts; MLX optional dependency installed | Class name is lowercase prefix `mlxSCVI`; train signature differs from PyTorch SCVI | `get_latent_representation` |

## Selection Heuristics

- If the data is RNA-only and labels are not part of the task, start with `SCVI` unless interpretability (`LinearSCVI`) or zero-inflation testing (`AUTOZI`) is the main request.
- If the user says some cells are labeled and some are unlabeled, route to `SCANVI`, not plain `SCVI`; verify the `unlabeled_category` value exists in `adata.obs[labels_key]`.
- If the user mentions ADT, surface proteins, CITE-seq, or `obsm["protein_expression"]`, route to `TOTALVI` for RNA+protein.
- If the user mentions peaks, chromatin accessibility, scATAC, fragments summarized to peaks, or differential accessibility, route to `PEAKVI` for ATAC-only or `MULTIVI` for RNA+ATAC.
- If the user mentions paired and unpaired RNA/ATAC cells, mosaic multimodal integration, or RNA+ATAC+protein, route to `MULTIVI` and check whether `n_genes`, `n_regions`, and protein keys are needed.
- If the user mentions spatial deconvolution with a single-cell reference, route to `CondSCVI` first for the single-cell reference and `DestVI` for spatial spots.
- If the user specifically asks for Apple Silicon MLX acceleration, use `scvi.model.mlxSCVI`; otherwise avoid MLX assumptions because optional extras may not be installed.

## Modality Checks Before Writing Code

- RNA count models expect raw counts in `adata.X` or the named `layer`; do not feed normalized/log data unless the user explicitly prepared a count layer and chooses it.
- Protein models expect a 2D protein matrix in `adata.obsm[protein_expression_obsm_key]`; if protein names are not columns on that matrix, use `protein_names_uns_key` when available.
- ATAC models expect accessibility features in variables; `PEAKVI` is ATAC-only, while `MULTIVI` needs enough metadata or constructor arguments to distinguish genes from regions.
- Semi-supervised models require `labels_key` to exist in `adata.obs`; missing or misspelled unlabeled category causes setup or training failures.
- `DestVI` is a two-stage workflow: train/load `CondSCVI` on single-cell data first, register spatial data with `DestVI.setup_anndata`, then construct with `DestVI.from_rna_model`.

## Mixed User Description Examples

- "I have CITE-seq RNA counts and ADT proteins and want batch-corrected protein denoising" -> `TOTALVI`, not `SCVI`, because protein likelihood/background handling is part of the model.
- "I have 10x Multiome with some cells RNA-only and some ATAC-only" -> `MULTIVI`, because it supports paired/mosaic RNA+ATAC integration.
- "I have scRNA labels for some cells and want to annotate unlabeled query cells" -> `SCANVI` if the workflow is within one registered AnnData; deeper reference/query transfer belongs to annotation-and-query.
- "I have Visium spots and a labeled scRNA reference" -> `CondSCVI` + `DestVI`; do not use `TOTALVI` unless there is protein data.
