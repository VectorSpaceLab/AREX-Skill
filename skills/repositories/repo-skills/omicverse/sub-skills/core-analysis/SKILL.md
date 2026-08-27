---
name: core-analysis
description: "Core OmicVerse AnnData IO, datasets, preprocessing, plotting,
  reporting, reproducibility, and registry discovery workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Core Analysis

Use this sub-skill for OmicVerse tasks centered on an `AnnData` object: loading data, checking QC, preprocessing, dimensionality reduction, neighbor graph construction, lightweight clustering prerequisites, plotting, reports, reproducibility, and package registry discovery.

For root routing and install strategy, return to [`../../SKILL.md`](../../SKILL.md).

## When to Use

- Read or write common matrix objects with `ov.read`, `ov.io.read`, `ov.io.read_h5ad`, `ov.io.read_10x_mtx`, `ov.io.read_10x_h5`, `ov.io.read_csv`, `ov.io.save`, or `ov.io.load`.
- Load or synthesize example data with `ov.datasets.*`, especially `ov.datasets.create_mock_dataset(...)` for no-network testing.
- Run core QC and preprocessing with `ov.pp.qc_metrics`, `ov.pl.qc`, `ov.pp.qc`, `ov.pp.preprocess`, `ov.pp.scale`, `ov.pp.pca`, `ov.pp.neighbors`, `ov.pp.umap`, `ov.pp.leiden`, or `ov.pp.louvain`.
- Plot embeddings or QC distributions with `ov.pl.embedding`, `ov.pl.umap`, `ov.pl.pca`, `ov.pl.qc`, palettes, and plot style helpers.
- Create a one-file HTML pipeline report with `ov.report.from_anndata(...)` or inspect provenance with `ov.report.get_provenance(...)`.
- Discover registered OmicVerse functions through `ov.list_functions`, `ov.get_function_help`, `ov.find_function`, `ov.recommend_function`, or `ov.export_registry`.

## Route Elsewhere

- Use [`../single-cell-workflows/SKILL.md`](../single-cell-workflows/SKILL.md) for annotation, marker ranking, trajectory, pseudotime, velocity/fate, batch integration, communication, pseudobulk, and single-cell biological interpretation.
- Use [`../multiomics-statistics/SKILL.md`](../multiomics-statistics/SKILL.md) for bulk RNA-seq, enrichment/signature scoring, metabolomics, proteomics, microbiome, and table-based omics statistics.
- Use [`../spatial-integration/SKILL.md`](../spatial-integration/SKILL.md) for Visium/Xenium/Nanostring spatial workflows, histology, deconvolution, tissue zones, and spatial mapping.
- Use [`../agentic-and-mcp/SKILL.md`](../agentic-and-mcp/SKILL.md) for CLI, MCP, JARVIS, registry manifests, skill seeker, and agent runtime configuration.

## Fast Start

```python
import omicverse as ov

ov.set_seed(0)
adata = ov.io.read_10x_mtx("filtered_feature_bc_matrix", var_names="gene_symbols")
adata.var_names_make_unique()

ov.pp.qc_metrics(adata)
fig = ov.pl.qc(adata, tresh={"mito_perc": 0.2, "nUMIs": 500, "detected_genes": 250})
fig.savefig("qc.png", dpi=150, bbox_inches="tight")

adata = ov.pp.qc(
    adata,
    tresh={"mito_perc": 0.2, "nUMIs": 500, "detected_genes": 250},
    doublets=False,
)
ov.pp.preprocess(adata, mode="shiftlog|pearson", n_HVGs=2000, target_sum=1e4)
ov.pp.scale(adata)
ov.pp.pca(adata, n_pcs=50)
ov.pp.neighbors(adata, n_neighbors=15, n_pcs=50)
ov.pp.umap(adata)

ov.pl.embedding(adata, basis="X_umap", color=["nUMIs", "mito_perc"], show=False)
ov.report.from_anndata(adata, output="core_report.html", title="Core preprocessing")
adata.write_h5ad("processed.h5ad", compression="gzip")
```

Expected core slots after this workflow:

- `adata.layers['counts']`: raw counts preserved by `ov.pp.preprocess`.
- `adata.var['highly_variable']` and `adata.var['highly_variable_features']`: selected HVGs.
- `adata.layers['scaled']`: scaled expression from `ov.pp.scale`.
- `adata.obsm['X_pca']`, `adata.varm['PCs']`, `adata.uns['pca']`: PCA outputs.
- `adata.uns['neighbors']`, `adata.obsp['distances']`, `adata.obsp['connectivities']`: neighbor graph.
- `adata.obsm['X_umap']`: UMAP coordinates.
- `adata.uns['_ov_provenance']`: best-effort report provenance for tracked calls.

## References

- [`references/core-workflows.md`](references/core-workflows.md): end-to-end AnnData workflows, validation checkpoints, and plotting/reporting patterns.
- [`references/api-reference.md`](references/api-reference.md): concrete API names, signatures, slot effects, and registry helpers.
- [`references/data-formats.md`](references/data-formats.md): input formats, 10x layouts, tabular safety, AnnData slot assumptions, and output guidance.
- [`references/troubleshooting.md`](references/troubleshooting.md): lazy import failures, workflow-order errors, plotting backends, downloads, warnings, and optional dependency issues.

## Bundled Check

Run the packaged introspection script before deeper debugging:

```bash
python sub-skills/core-analysis/scripts/inspect_core.py --help
python sub-skills/core-analysis/scripts/inspect_core.py --json
python sub-skills/core-analysis/scripts/inspect_core.py --smoke-mock --mock-cells 40 --mock-genes 80
```

The script reports OmicVerse version, lazy root attributes, selected module imports, registry size, and optionally a small synthetic `AnnData` smoke. It does not require the original repository checkout and does not download data.

## Guardrails

- Preserve raw counts before filtering or normalization; keep them in `.layers['counts']` or `.raw` when possible.
- Run QC metrics before threshold plots: `ov.pl.qc` raises when standard QC metrics are missing.
- Follow the order `qc_metrics` or `qc` → `preprocess` → `scale` → `pca` → `neighbors` → `umap` → plotting/reporting.
- Treat dataset loaders as potentially networked unless the function is explicitly synthetic, such as `create_mock_dataset`.
- If a lazy import says `Failed to import omicverse.<module>`, isolate the missing optional dependency by importing that module directly and checking its traceback.
