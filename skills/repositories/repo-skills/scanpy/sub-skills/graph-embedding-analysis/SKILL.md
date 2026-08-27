---
name: graph-embedding-analysis
description: "Design and debug Scanpy neighborhood graphs, embeddings,
  clustering, trajectories, marker genes, gene scoring, ingest projection, and
  graph metrics on AnnData objects."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Graph Embedding Analysis

Use this sub-skill when a Scanpy task involves graph construction, low-dimensional embeddings, graph clustering, trajectory abstraction, marker ranking, gene-set scoring, reference-to-query ingest, or graph/cluster quality metrics.

## Route by Task

- Build the graph foundation with `sc.pp.neighbors`; see `references/workflows.md#graph-foundation`.
- Embed cells with `sc.tl.umap`, `sc.tl.tsne`, `sc.tl.diffmap`, or `sc.tl.draw_graph`; see `references/workflows.md#embeddings`.
- Cluster or summarize topology with `sc.tl.leiden`, optional `sc.tl.louvain`, `sc.tl.dendrogram`, and `sc.tl.paga`; see `references/workflows.md#clustering-and-topology`.
- Infer pseudotime with `sc.tl.diffmap` plus `sc.tl.dpt`; see `references/workflows.md#trajectories`.
- Rank and filter marker genes with `sc.tl.rank_genes_groups` and `sc.tl.filter_rank_genes_groups`; see `references/workflows.md#marker-genes`.
- Score signatures with `sc.tl.score_genes` and `sc.tl.score_genes_cell_cycle`; see `references/workflows.md#gene-scoring`.
- Project query observations onto a processed reference with `sc.tl.ingest`; see `references/workflows.md#ingest`.
- Evaluate graph or clustering outputs with `scanpy.metrics`; see `references/workflows.md#metrics`.

## Boundaries

This sub-skill owns outputs in `.obs`, `.obsm`, `.obsp`, and `.uns` created by `sc.pp.neighbors`, `sc.tl.umap`, `tsne`, `diffmap`, `draw_graph`, `leiden`, `louvain`, `paga`, `dpt`, `rank_genes_groups`, `filter_rank_genes_groups`, `score_genes`, `score_genes_cell_cycle`, `ingest`, `dendrogram`, `embedding_density`, and `scanpy.metrics.morans_i`, `gearys_c`, `modularity`, and `confusion_matrix`.

Route upstream matrix preparation, QC, normalization, HVG selection, scaling, and PCA decisions to `preprocessing-qc`. Route `sc.pl.*` figure rendering and report assembly to `plotting-reporting`. Route external algorithms such as BBKNN, Scanorama, MAGIC, Scrublet, and other optional wrappers to `external-integrations`.

## Fast Patterns

```python
import scanpy as sc

sc.pp.pca(adata, n_comps=30, random_state=0)
sc.pp.neighbors(adata, n_neighbors=15, n_pcs=30, rng=0)
sc.tl.umap(adata, rng=0)
sc.tl.leiden(adata, resolution=1.0, key_added="leiden", rng=0)
sc.tl.rank_genes_groups(adata, groupby="leiden", method="wilcoxon", use_raw=False, key_added="rank_leiden")
```

```python
sc.pp.neighbors(adata, n_neighbors=20, use_rep="X_pca", metric="cosine", key_added="neighbors_cosine", rng=0)
sc.tl.umap(adata, neighbors_key="neighbors_cosine", key_added="X_umap_cosine", rng=0)
sc.metrics.morans_i(adata, obsm="X_pca", neighbors_key="neighbors_cosine")
```

## Required References

- `references/workflows.md` gives call sequences, parameter choices, graph selectors, and output slots.
- `references/troubleshooting.md` maps common exceptions, wrong-key issues, optional dependency failures, and suspicious outputs to fixes.
- `scripts/scanpy_analysis_smoke.py` is a deterministic synthetic smoke check for graph, embedding, marker, score, and metrics APIs without original repository files.

## Validation

From the root of this generated Scanpy skill, run:

```bash
python sub-skills/graph-embedding-analysis/scripts/scanpy_analysis_smoke.py
```

The script prints JSON with checks for neighbors, UMAP when available, marker ranking, gene scoring, Moran's I, Geary's C, and a confusion matrix. It intentionally avoids requiring Leiden/Louvain; optional clustering can be requested with a flag and is reported clearly if missing dependencies prevent it.
