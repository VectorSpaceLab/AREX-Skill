# Graph, Embedding, and Analysis Workflows

## Graph Foundation

`sc.pp.neighbors` is the graph dependency for UMAP, Diffmap, PAGA, DPT, graph-aware clustering, and graph metrics. It computes a distance matrix and a connectivities matrix and stores metadata describing where downstream tools should read them.

| Decision | Preferred pattern | Output / note |
|---|---|---|
| Representation | Run `sc.pp.pca(adata, n_comps=...)`, then pass `n_pcs` or `use_rep="X_pca"` | Avoid implicit PCA fallback and make runs reproducible. |
| Locality | `n_neighbors=10` to `30` for typical exploratory analysis | Must be sensible for `adata.n_obs`; tiny data needs smaller values. |
| Storage | Default graph or `key_added="neighbors_name"` | Default writes `.uns["neighbors"]`, `.obsp["distances"]`, `.obsp["connectivities"]`; custom keys write `.uns[key_added]`, `.obsp[f"{key_added}_distances"]`, `.obsp[f"{key_added}_connectivities"]`. |
| Kernel | `method="umap"`, `"gauss"`, or `"jaccard"` | `method` controls connectivities; `transformer` controls kNN search backend. |
| Metric | `metric="euclidean"`, `"cosine"`, or a valid callable/backend metric | Record non-default metrics because they change all graph-dependent outputs. |
| Reproducibility | Prefer `rng=0`; legacy `random_state=0` may still work | Use the same seed for downstream stochastic tools. |

Two-graph pattern:

```python
sc.pp.pca(adata, n_comps=30, random_state=0)
sc.pp.neighbors(adata, n_neighbors=15, n_pcs=30, rng=0)
sc.pp.neighbors(
    adata,
    n_neighbors=30,
    use_rep="X_pca",
    metric="cosine",
    key_added="neighbors_cosine",
    rng=0,
)
```

Use `neighbors_key="neighbors_cosine"` whenever a downstream tool should consume the alternate graph.

## Embeddings

| Tool | Requires neighbors? | Main output | Use when |
|---|---:|---|---|
| `sc.tl.umap` | Yes | `.obsm["X_umap"]` or `.obsm[key_added]`; `.uns["umap"]` or `.uns[key_added]` | Default graph-preserving visualization. |
| `sc.tl.tsne` | No graph dependency | `.obsm["X_tsne"]` or custom key | Distance-focused visualization; set `use_rep` or `n_pcs` explicitly. |
| `sc.tl.diffmap` | Yes | `.obsm["X_diffmap"]`, `.uns["diffmap_evals"]` | Diffusion components for trajectories and pseudotime. |
| `sc.tl.draw_graph` | Yes | `.obsm["X_draw_graph_<layout>"]` | Force-directed graph layouts, optionally initialized from PAGA. |
| `sc.tl.embedding_density` | Embedding plus group/color context | `.uns[f"{basis}_density_{groupby}"]` or related density key | Quantify cell density over an existing embedding. |

UMAP reads graph metadata from `.uns[neighbors_key]` and connectivities from the key recorded there. If `key_added` is set, the embedding is stored exactly under `.obsm[key_added]`, not automatically prefixed with `X_`.

```python
sc.tl.umap(adata, min_dist=0.3, spread=1.0, neighbors_key="neighbors", rng=0)
sc.tl.umap(adata, neighbors_key="neighbors_cosine", key_added="X_umap_cosine", rng=0)
sc.tl.diffmap(adata, n_comps=15, neighbors_key="neighbors", rng=0)
```

Use plotting/reporting guidance for `sc.pl.umap`, `sc.pl.tsne`, `sc.pl.diffmap`, `sc.pl.draw_graph`, and figure styling.

## Clustering and Topology

| Task | Tool | Dependency | Output |
|---|---|---|---|
| Community detection | `sc.tl.leiden` | Neighbor graph plus optional `igraph`/`leidenalg` stack | `.obs[key_added]`, `.uns[key_added]["params"]`, `.uns[key_added]["modularity"]` when available. |
| Legacy clustering | `sc.tl.louvain` | Louvain optional dependencies | `.obs[key_added]`, `.uns[key_added]`. |
| Cluster dendrogram | `sc.tl.dendrogram` | Categorical grouping and expression/representation | `.uns[f"dendrogram_{groupby}"]` by default. |
| Partition abstraction | `sc.tl.paga` | Neighbor graph and categorical group labels | `.uns["paga"]["connectivities"]`, `.uns["paga"]["connectivities_tree"]`. |

Leiden supports `resolution`, `restrict_to`, `key_added`, `adjacency`, `neighbors_key`, `obsp`, `n_iterations`, and `flavor`. Use explicit `key_added` values when comparing resolutions or graph variants.

```python
sc.tl.leiden(adata, resolution=0.5, key_added="leiden_r05", neighbors_key="neighbors", rng=0)
sc.tl.leiden(adata, resolution=1.0, key_added="leiden_r10", neighbors_key="neighbors", rng=0)
sc.tl.paga(adata, groups="leiden_r10", neighbors_key="neighbors")
sc.tl.dendrogram(adata, groupby="leiden_r10", use_rep="X_pca")
```

For alternate graphs, pass `neighbors_key`. For functions that document direct matrix selection, such as `leiden`, `louvain`, and `draw_graph`, `obsp="custom_connectivities"` can bypass `.uns[neighbors_key]`; do not assume every graph-dependent tool supports `obsp`.

## Trajectories

DPT needs a neighbor graph, diffusion maps, and a root cell index.

```python
sc.pp.neighbors(adata, n_neighbors=15, n_pcs=30, method="gauss", rng=0)
sc.tl.diffmap(adata, n_comps=15, rng=0)
root_mask = adata.obs["cell_type"].eq("Stem")
adata.uns["iroot"] = int(root_mask.to_numpy().nonzero()[0][0])
sc.tl.dpt(adata, n_dcs=10)
```

Use `method="gauss"` in `sc.pp.neighbors` when reproducing older diffusion pseudotime behavior. Use PAGA to reason about branches before interpreting a single DPT ordering as a full lineage model.

## Marker Genes

`sc.tl.rank_genes_groups` expects log-transformed expression and a grouping column in `.obs`. It writes structured arrays under `.uns[key_added or "rank_genes_groups"]`.

| Parameter | Common values | Notes |
|---|---|---|
| `groupby` | Categorical `.obs` key | Convert to categorical, remove unused categories, and avoid singleton/empty groups. |
| `method` | `"wilcoxon"`, `"t-test"`, `"t-test_overestim_var"`, `"logreg"` | Choose explicitly for reproducibility; default can be settings-controlled. |
| `use_raw` | `True`, `False`, or `None` | `None` uses `.raw` if present. Set `False` when testing `.X` or a layer intentionally. |
| `layer` | Layer name | Use for normalized/logged matrices outside `.X`; keep `use_raw` semantics explicit. |
| `groups` / `reference` | `"all"`, selected groups, `"rest"`, or a category | If using selected groups and a category reference, ensure category names match exactly. |
| `pts` | `True` for fraction-aware results | Adds `pts` and possibly `pts_rest`, useful for filtering. |

```python
adata.obs["cluster"] = adata.obs["cluster"].astype("category").cat.remove_unused_categories()
sc.tl.rank_genes_groups(
    adata,
    groupby="cluster",
    method="wilcoxon",
    use_raw=False,
    pts=True,
    key_added="rank_cluster",
)
sc.tl.filter_rank_genes_groups(
    adata,
    key="rank_cluster",
    key_added="rank_cluster_filtered",
    min_in_group_fraction=0.25,
    max_out_group_fraction=0.5,
    min_fold_change=1.0,
)
```

Use `scanpy.get.rank_genes_groups_df(adata, group=..., key=...)` to convert structured marker results into data frames before exporting or plotting. Treat Scanpy marker ranking as exploratory cell-level ranking; for sample-level differential expression, use pseudobulk workflows outside this sub-skill.

## Gene Scoring

`sc.tl.score_genes` computes per-cell signature scores and writes `adata.obs[score_name]`. It samples matched control genes, so set a seed and record gene-pool decisions.

```python
present = [gene for gene in ["MS4A1", "CD79A", "CD79B"] if gene in adata.var_names]
missing = sorted(set(["MS4A1", "CD79A", "CD79B"]) - set(present))
if len(present) < 2:
    raise ValueError(f"Too few B-cell genes present: missing={missing}")
sc.tl.score_genes(
    adata,
    gene_list=present,
    score_name="b_cell_score",
    ctrl_size=50,
    n_bins=25,
    rng=0,
    use_raw=False,
)
```

`sc.tl.score_genes_cell_cycle` wraps the same idea for S and G2M genes and adds `S_score`, `G2M_score`, and `phase`.

```python
sc.tl.score_genes_cell_cycle(adata, s_genes=s_genes, g2m_genes=g2m_genes, use_raw=False, rng=0)
```

## Ingest

`sc.tl.ingest` maps reference labels and embeddings onto query data. The reference must already have neighbors and any requested embeddings; variables must match between reference and query.

```python
sc.pp.pca(adata_ref, n_comps=30, random_state=0)
sc.pp.neighbors(adata_ref, n_neighbors=15, n_pcs=30, rng=0)
sc.tl.umap(adata_ref, rng=0)

adata_query = adata_query[:, adata_ref.var_names].copy()
sc.tl.ingest(
    adata_query,
    adata_ref,
    obs="cell_type",
    embedding_method=["umap", "pca"],
    neighbors_key="neighbors",
    inplace=True,
)
```

Expected query outputs include mapped `.obs[obs]`, `.obsm["X_umap"]`, and `.obsm["X_pca"]` for requested methods. Ingest is projection and label transfer, not joint integration or batch correction.

## Metrics

| Function | Purpose | Graph selection |
|---|---|---|
| `sc.metrics.morans_i` | High values indicate neighboring cells have similar values | Use `neighbors_key`, `use_graph`, or pass a graph directly. |
| `sc.metrics.gearys_c` | Lower values indicate stronger local autocorrelation | Same selectors as Moran's I. |
| `sc.metrics.modularity` | Scores cluster labels against graph connectivities | With `AnnData`, pass `labels` and `neighbors_key`; with a matrix, pass label array and `is_directed`. |
| `sc.metrics.confusion_matrix` | Compares two labelings | No graph required; accepts arrays or `.obs` column names plus `data=adata.obs`. |

```python
pc_moran = sc.metrics.morans_i(adata, obsm="X_pca", neighbors_key="neighbors")
gene_geary = sc.metrics.gearys_c(adata, layer="log1p", neighbors_key="neighbors")
mod = sc.metrics.modularity(adata, labels="leiden", neighbors_key="neighbors", mode="calculate")
cm = sc.metrics.confusion_matrix("manual", "leiden", data=adata.obs, normalize=True)
```

For direct graph calls to `morans_i` or `gearys_c`, a two-dimensional values matrix should be features by cells. Passing `AnnData` with `layer`, `obsm`, `obsp`, or `use_raw` lets Scanpy handle selection and orientation.
