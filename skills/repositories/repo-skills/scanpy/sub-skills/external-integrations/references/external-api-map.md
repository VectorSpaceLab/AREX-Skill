# `scanpy.external` API Map

Import external wrappers as `import scanpy.external as sce`. Most wrappers mutate `AnnData` in place by default and return `None`; wrappers with `copy=True` usually return a modified copy. Check the wrapper docstring for exact parameters before coding a final pipeline.

## Preprocessing Wrappers: `sce.pp`

| API | Purpose | Install prerequisite | Main inputs | Main output/location | Placement in workflow |
|---|---|---|---|---|---|
| `sce.pp.bbknn(adata, batch_key='batch', use_rep='X_pca', ...)` | Batch-balanced nearest-neighbor graph | `scanpy[bbknn]` | PCA or another representation in `.obsm`; batch column in `.obs` | Neighbor graph fields managed by BBKNN/Scanpy | Use instead of `sc.pp.neighbors` after PCA, before UMAP/Leiden. |
| `sce.pp.mnn_correct(*datas, var_subset=..., do_concatenate=True, ...)` | Mutual nearest-neighbor batch correction | `mnnpy` | Two or more AnnData objects or matrices with matching variables | Corrected AnnData/matrix plus MNN and angle lists | Use for expression correction; avoid differential expression on corrected matrices. |
| `sce.pp.scanorama_integrate(adata, key, basis='X_pca', adjusted_basis='X_scanorama', ...)` | Scanorama batch integration | `scanpy[scanorama]` | PCA in `.obsm[basis]`; batch key in `.obs`; cells from each batch should be grouped consistently | `.obsm[adjusted_basis]` | Run after PCA and before neighbors; use adjusted basis for neighbors. |
| `sce.pp.hashsolo(adata, cell_hashing_columns, ...)` | Cell hashing demultiplexing | Core Scanpy dependencies | Hashing barcode count columns in `.obs`; optional existing clusters | Classification/probability columns in `.obs` | Use for sample demultiplexing, not transcriptome clustering. |
| `sce.pp.magic(adata, name_list=..., solver='exact', ...)` | MAGIC imputation/denoising | `scanpy[magic]` | AnnData, preferably with `.raw`; choose targeted genes or PCA-only for memory | Depending on `name_list`: returned AnnData, `.obsm['X_magic']`, or `.X` | Use cautiously; imputation has debated biological limitations. |

## Moved Preprocessing APIs

| Prefer now | Legacy alias | Install prerequisite | Notes |
|---|---|---|---|
| `sc.pp.harmony_integrate(adata, key, basis='X_pca', adjusted_basis='X_pca_harmony', ...)` | `sce.pp.harmony_integrate` | Core Scanpy implementation | Deprecated in `scanpy.external.pp` as of the 1.13 cycle; run after PCA and before neighbors. |
| `sc.pp.scrublet(adata, batch_key=..., rng=...)` | `sce.pp.scrublet` | `scanpy[scrublet]` when threshold detection needs `scikit-image` | Predicts doublets from raw counts; can run per batch. |
| `sc.pp.scrublet_simulate_doublets(adata, rng=...)` | `sce.pp.scrublet_simulate_doublets` | `scanpy[scrublet]` for thresholding paths | Advanced path for separately simulating doublets before calling Scrublet. |

Use the current `sc.pp` APIs in new code. The `sce.pp` names are deprecated compatibility aliases.

## Tool Wrappers: `sce.tl`

| API | Purpose | Install prerequisite | Main output/location | Notes |
|---|---|---|---|---|
| `sce.tl.phate(adata, n_components=2, ...)` | PHATE trajectory embedding | `phate` | `.obsm['X_phate']` | Plot with `sce.pl.phate`. |
| `sce.tl.palantir(adata, impute_data=True, ...)` | Diffusion maps/multiscale space for Palantir workflows | `palantir` | `.obsm['X_palantir_diff_comp']`, `.obsm['X_palantir_multiscale']`, `.uns`, `.obsp`, optional `.layers['palantir_imp']` | `sce.tl.palantir_results` computes branch probabilities and pseudotime from prepared multiscale space. |
| `sce.tl.palantir_results(adata, early_cell, ms_data='X_palantir_multiscale', ...)` | Palantir pseudotime and branch probabilities | `palantir` | Palantir result fields added from upstream output | Requires multiscale representation, commonly from `sce.tl.palantir`. |
| `sce.tl.trimap(adata, n_components=2, ...)` | TriMap embedding | `trimap` | `.obsm['X_trimap']` | Wrapper raises on sparse matrices; densify or choose another embedding when data are sparse and large. |
| `sce.tl.sam(adata, projection='umap', inplace=True, ...)` | Self-Assembling Manifold analysis | `samalg`/`sc-sam` | `.uns['sam']`, SAM object, and optionally embeddings | Expects unstandardized, non-negative, preferably log-normalized data. |
| `sce.tl.phenograph(data, clustering_algo='louvain', ...)` | PhenoGraph clustering | `phenograph>=1.5.3`; Louvain/Leiden dependencies when selected | For AnnData, cluster labels in `.obs` such as `pheno_louvain` or `pheno_leiden`; can return communities/graph/modularity for array inputs | Use `clustering_algo=None` to return graph/modularity without community assignment. |
| `sce.tl.harmony_timeseries(adata, tp, ...)` | Harmony time-series augmented affinity/layout | `harmonyTS` importing as `harmony` | `.obsm['X_harmony']`, `.obsp['harmony_aff']`, `.obsp['harmony_aff_aug']`, `.uns` timepoint metadata | `adata.obs[tp]` must be categorical and ordered as discrete time points. Distinct from `sc.pp.harmony_integrate`. |
| `sce.tl.wishbone(adata, start_cell, ...)` | Bifurcating developmental trajectory | `wishbone` | `.obs['trajectory_wishbone']`, `.obs['branch_wishbone']` | Typical prerequisites include PCA, t-SNE, neighbors, and diffusion map. |
| `sce.tl.sandbag(adata, annotation=...)` | Marker-pair discovery | `pypairs>=3.2.0` | Dict of marker gene pairs | Part of pypairs wrappers. |
| `sce.tl.cyclone(adata, marker_pairs=...)` | Cell-cycle scoring from marker pairs | `pypairs>=3.2.0` | DataFrame and optional `.obs['pypairs_cc_prediction']` | Use with pypairs-compatible marker pairs. |

## Plotting Wrappers: `sce.pl`

| API | Requires prior computation | Purpose |
|---|---|---|
| `sce.pl.phate(adata, ...)` | `.obsm['X_phate']` from `sce.tl.phate` | Scatter plot in PHATE basis. |
| `sce.pl.trimap(adata, ...)` | `.obsm['X_trimap']` from `sce.tl.trimap` | Scatter plot in TriMap basis. |
| `sce.pl.sam(adata, projection='X_umap', ...)` | SAM/UMAP/t-SNE projection in `.obsm` | Scatter plot using SAM or another projection. |
| `sce.pl.harmony_timeseries(adata, ...)` | `.obsm['X_harmony']` and `.uns['harmony_timepoint_var']` from `sce.tl.harmony_timeseries` | Faceted Harmony time-series layout by time point. |
| `sce.pl.wishbone_marker_trajectory(adata, markers, ...)` | Wishbone trajectory results from `sce.tl.wishbone` | Marker trajectories over Wishbone branches. |

`sc.pl.scrublet_score_distribution` is the current plotting API for Scrublet score distributions; the old external plotting alias is deprecated.

## Exporting Wrappers: `sce.exporting`

| API | Purpose | Install prerequisite | Output |
|---|---|---|---|
| `sce.exporting.spring_project(adata, project_dir, ...)` | Export a Scanpy object to SPRING-compatible project files | Core dependencies for file writing | Project directory with graph, coordinates, matrix, color tracks, and gene/cell metadata. |
| `sce.exporting.cellbrowser(adata, ...)` | Export to UCSC Cell Browser | `cellbrowser` | Cell Browser project files. |

Treat exporting as a write-heavy operation: confirm output directory, overwrite behavior, and dataset size before running it.

## Workflow Patterns

### Batch integration before neighbors

1. Normalize/log-transform and select HVGs using core Scanpy guidance.
2. Compute PCA into `.obsm['X_pca']`.
3. Choose one integration strategy: `sc.pp.harmony_integrate`, `sce.pp.scanorama_integrate`, or `sce.pp.bbknn`.
4. For Harmony or Scanorama, run `sc.pp.neighbors(..., use_rep='X_pca_harmony' or 'X_scanorama')`.
5. For BBKNN, skip `sc.pp.neighbors` because BBKNN creates the graph.
6. Continue with UMAP, Leiden, PAGA, or plotting as appropriate.

### Imputation with dependency recovery

1. Check whether the task truly needs imputation and warn that MAGIC imputation has debated limitations.
2. Run the optional-dependency helper for `magic` or inspect `find_spec('magic')`.
3. If missing, recommend `scanpy[magic]` or `magic-impute>=2.0.4` only.
4. Prefer `name_list='pca_only'` or a targeted gene list for large sparse data to avoid replacing all of `.X` unintentionally.

### Demultiplexing with HashSolo

1. Confirm barcode count columns are present in `adata.obs` and non-negative.
2. Choose priors and optional cluster stratification.
3. Run `sce.pp.hashsolo(..., inplace=True)` to add classifications/probabilities to `.obs`.
4. Treat HashSolo outputs as sample assignment metadata, not as a replacement for doublet detection from transcriptomes.

### External plotting and exporting

1. Verify the upstream computation wrote the expected `.obsm`, `.obs`, `.uns`, `.obsp`, or `.layers` key.
2. Use the matching `sce.pl` wrapper only for PHATE, TriMap, SAM, Harmony time series, or Wishbone marker trajectories.
3. For Scrublet score distributions, use `sc.pl.scrublet_score_distribution`.
4. For exports, check path, overwrite policy, and optional `cellbrowser` availability before writing files.
