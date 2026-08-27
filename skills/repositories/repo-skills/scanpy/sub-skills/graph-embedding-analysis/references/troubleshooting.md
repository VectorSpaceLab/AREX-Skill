# Troubleshooting Graph, Embedding, and Marker Workflows

## Neighbor Graph Selection

| Symptom | Likely cause | Fix |
|---|---|---|
| UMAP, Diffmap, PAGA, DPT, or metrics says neighbors are missing | `.uns["neighbors"]` is absent, or the graph was written under a custom key | Run `sc.pp.neighbors(adata, ...)`, or pass the exact `neighbors_key` used in `sc.pp.neighbors(key_added=...)`. |
| `KeyError` for an alternate graph | `neighbors_key` does not match a key in `.uns` | Inspect `adata.uns.keys()` and use the exact key, not the `.obsp` matrix key. |
| Results unexpectedly use the default graph | Downstream call omitted `neighbors_key` after a custom graph was created | Pass `neighbors_key="your_key"` to UMAP, Diffmap, PAGA, DPT, metrics, and supported clustering calls. |
| Direct `obsp` graph works for Leiden but not UMAP/PAGA | Only some tools support direct `obsp`; others require `.uns[neighbors_key]` metadata | Prefer `sc.pp.neighbors(key_added=...)` for reusable graphs, and use `obsp` only for APIs that document it. |

Graph storage sanity check:

```python
for key in ["neighbors", "neighbors_cosine"]:
    if key in adata.uns:
        print(key, adata.uns[key].get("connectivities_key"), adata.uns[key].get("distances_key"))
print(list(adata.obsp.keys()))
```

## Optional Leiden and Louvain Dependencies

| Symptom | Likely cause | Fix |
|---|---|---|
| Leiden import error | `igraph` and/or `leidenalg` stack is missing | Install the Leiden extra only when clustering is required, or skip Leiden in minimal smoke checks. |
| Louvain import error | Louvain optional dependency is missing | Install the Louvain extra only for legacy Louvain workflows. |
| `Cannot use igraph’s leiden ... directed` | `flavor="igraph"` does not support directed Leiden through this API | Use `directed=False`, or switch to a supported Leiden flavor when installed. |
| Different labels across runs | Seed, implementation flavor, resolution, or iteration count changed | Pass `rng=0` or `random_state=0`, and record `flavor`, `resolution`, `n_iterations`, and graph key. |
| Modularity differs from stored clustering metadata | Stored score came from a flavor-specific run or stale labels | Recompute with `sc.metrics.modularity(adata, labels="cluster_key", mode="calculate")` or `mode="update"`. |

Do not install all Scanpy extras by default. Choose the smallest optional dependency set that supports the requested graph algorithm.

## PCA, Components, and Small Data

| Symptom | Likely cause | Fix |
|---|---|---|
| Neighbor computation warns about implicit PCA | `n_pcs` was requested but `.obsm["X_pca"]`/`.uns["pca"]` is missing | Run `sc.pp.pca` explicitly before `sc.pp.neighbors`. |
| Too many PCs/components error | `n_pcs`, `n_comps`, t-SNE dimensions, or DPT `n_dcs` exceed cells/features | Reduce requested components and make tiny smoke data large enough. |
| UMAP is unstable on tiny data | Too few cells for requested `n_neighbors` or stochastic initialization | Lower `n_neighbors`, pass a seed, and assert keys/shapes rather than exact coordinates. |
| Unexpected graph density | `knn=False`, `method="gauss"`, `method="jaccard"`, or custom distances changed connectivity construction | Check `adata.uns[neighbors_key]["params"]`, `knn`, `method`, `metric`, `distances`, and `transformer`. |

## Embeddings and Trajectories

| Symptom | Likely cause | Fix |
|---|---|---|
| UMAP with alternate graph fails | `neighbors_key` was omitted or misspelled | Pass the same key used in `sc.pp.neighbors(key_added=...)`. |
| `init_pos="paga"` fails | PAGA positions were not computed before UMAP initialization | Compute PAGA and PAGA positions first, or choose `init_pos="spectral"`, `"random"`, or an array. |
| DPT complains about missing root or diffusion map | `sc.tl.diffmap` was not run or `adata.uns["iroot"]` is absent | Run `sc.tl.diffmap`, then set `adata.uns["iroot"]` to an integer cell index. |
| PAGA asks for groups or clustering | No categorical groups were provided and no suitable default cluster key exists | Run clustering or pass an existing `.obs` categorical key via `groups`. |
| PAGA group key not found | `groups` does not exist in `.obs` | Inspect `adata.obs.columns`, then use the exact key. |
| Embedding density output missing | The requested embedding basis or grouping is absent | Run the embedding first and verify the basis key in `.obsm`. |

## Marker Genes and Matrix Selection

| Symptom | Likely cause | Fix |
|---|---|---|
| Ranking fails with group/category error | `groupby` is non-categorical, has unused/empty categories, or singleton groups | Convert to `category`, remove unused categories, and ensure each group has enough cells. |
| Warning about raw count data | `rank_genes_groups` was run on counts instead of log-transformed expression | Normalize/log-transform upstream, or intentionally choose a logged layer and record it. |
| `use_raw=True` but raw is empty | `.raw` is absent | Use `use_raw=False`, create `.raw` upstream intentionally, or choose `layer`. |
| Results unexpectedly use `.raw` | `use_raw=None` defaults to `.raw` when present | Set `use_raw=False` when you intend to use `.X` or `layer`. |
| `layer` and `.raw` confusion | Ranking and filtering selected different matrices | Keep `use_raw` and `layer` explicit for both `rank_genes_groups` and `filter_rank_genes_groups`; inspect `adata.uns[key]["params"]`. |
| Filtered markers are all missing or `nan` | Fraction or fold-change filters are too strict, or `pts`/matrix choices do not support the filter | Loosen `min_in_group_fraction`, `max_out_group_fraction`, or `min_fold_change`; rerun ranking with `pts=True` when needed. |
| P-values look overconfident | Cell-level tests treat cells as independent | Document marker ranking as exploratory; route sample-level DE to pseudobulk workflows outside this sub-skill. |

## Gene Scoring

| Symptom | Likely cause | Fix |
|---|---|---|
| Score is missing, all zeros, or uninformative | Gene symbols do not match `adata.var_names`, or too few genes are present | Intersect gene lists with `adata.var_names` and report missing genes before scoring. |
| Scores change across runs | Control genes are sampled randomly | Pass `rng=0` or `random_state=0`, and record `ctrl_size`, `n_bins`, and `gene_pool`. |
| Backed object failure | Scoring is not implemented for some backed matrix types | Load into memory or score on a supported layer/representation. |
| Cell-cycle phase is unexpected | S/G2M marker lists do not match species or naming convention | Validate marker names and use `use_raw`/`layer` consistently. |

## Ingest

| Symptom | Likely cause | Fix |
|---|---|---|
| Ingest says reference needs neighbors | The reference object was not processed through `sc.pp.neighbors` | Run PCA/neighbors on the reference before ingest. |
| Query lacks mapped UMAP | Reference lacks UMAP or `embedding_method` omitted `"umap"` | Run `sc.tl.umap(adata_ref)` and request `embedding_method="umap"` or a list including it. |
| Variable mismatch error or poor mapping | Query and reference variables differ or are in different order | Reindex query as `adata_query[:, adata_ref.var_names].copy()` after checking shared genes. |
| Backed query failure | Ingest fit does not support the backed matrix type | Load query into memory before ingest. |
| Ingest interpreted as integration | Ingest is asymmetric projection, not joint batch correction | Route batch correction or external integration algorithms to `external-integrations`. |

## Metrics

| Symptom | Likely cause | Fix |
|---|---|---|
| `both use_graph and neighbors_key` error | Mutually exclusive graph selectors were provided | Use only one graph selector. |
| `KeyError` for graph in metrics | Graph key is missing from `.obsp` or `.uns` | Pass `neighbors_key` from `sc.pp.neighbors(key_added=...)`, or `use_graph` for an exact `.obsp` key. |
| Moran's I or Geary's C returns `nan` | Values are constant or have invalid variance over cells | Drop constant variables or flag them before interpreting metrics. |
| Direct graph metric shape error | Manual values are not aligned to graph observations | Prefer `AnnData` selectors; for direct graph calls, pass one value per cell or features-by-cells arrays. |
| `modularity` raises an igraph import error | `igraph` is required for modularity calculation | Install only the graph dependency needed for modularity, or skip this metric in minimal environments. |
| Confusion matrix category order surprises | Categorical and non-categorical labels are ordered differently | Convert labels to categorical with desired category order before calling `sc.metrics.confusion_matrix`. |
