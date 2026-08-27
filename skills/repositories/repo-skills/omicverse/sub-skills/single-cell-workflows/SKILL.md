---
name: single-cell-workflows
description: "Single-cell biological analysis workflows for annotation,
  integration, trajectory, fate, perturbation, pseudobulk, metacells,
  metabolism, CNV, SCENIC, and lazy scRNA orchestration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Single-Cell Workflows

Use this sub-skill for biological interpretation and downstream single-cell analysis after an AnnData object has basic QC, normalization, features, embeddings, and clustering available. For package-wide routing, start at [the root skill](../../SKILL.md).

## When To Use

- Annotate clusters or cells with `ov.single.pySCSA`, `Annotation`, `AnnotationRef`, `CellVote`, `gptcelltype`, or manual marker workflows.
- Integrate batches with `ov.single.batch_correction`, including Harmony, Scanorama, CCA, scVI, scANVI, totalVI, or scPoli.
- Aggregate single cells into donor or donor-by-cell-type pseudobulk profiles with `ov.single.pseudobulk`.
- Infer trajectories, pseudotime, fate probabilities, RNA velocity, dynamic features, perturbation effects, CNV, metacells, or metabolism.
- Generate single-cell workflow reports with `ov.single.generate_scRNA_report` or use `lazy_step_*` orchestration after validating data slots.

## Route Elsewhere

- Core read/QC/preprocess/normalize/PCA/neighbors/UMAP/plotting prerequisites belong in [core analysis](../core-analysis/SKILL.md).
- Spatial-specific ligand-receptor visualization and tissue-coordinate workflows belong in [spatial integration](../spatial-integration/SKILL.md).
- CLI, MCP, registry, JARVIS, and AI-agent runtime work belongs in [agentic and MCP](../agentic-and-mcp/SKILL.md).

## Start Here

1. Confirm the AnnData slot contract with [`scripts/check_single_cell_inputs.py`](scripts/check_single_cell_inputs.py): cluster labels in `obs`, embeddings in `obsm`, and raw or scaled layers as needed.
2. Choose the closest workflow in [`references/single-cell-workflows.md`](references/single-cell-workflows.md).
3. Check concrete API names, parameters, inputs, and outputs in [`references/api-reference.md`](references/api-reference.md).
4. If imports, markers, labels, batches, or trajectory slots fail, use [`references/troubleshooting.md`](references/troubleshooting.md).

## Data Assumptions

- Most workflows consume `anndata.AnnData` with cells in rows and genes/features in columns.
- Annotation usually needs a cluster column such as `obs['leiden']` plus marker rankings in `uns['rank_genes_groups']` or computable marker genes.
- Batch integration needs `obs[batch_key]`; VAE backends normally need raw counts in `layers['counts']`.
- Trajectory/fate workflows need embeddings or neighbor graphs such as `obsm['X_pca']`, `obsm['X_umap']`, and `obsp['connectivities']`.
- Plotting-heavy outputs are produced by OmicVerse/Scanpy plotting APIs; route generic plotting details to [core analysis](../core-analysis/SKILL.md).
