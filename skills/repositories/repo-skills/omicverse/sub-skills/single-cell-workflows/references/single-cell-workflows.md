# Single-Cell Workflow Guide

This reference gives implementation-ready patterns for `omicverse.single` biological workflows. It assumes preprocessing, basic QC, and generic plotting are handled by the sibling [core analysis](../../core-analysis/SKILL.md) sub-skill.

## Preflight Slot Checklist

| Workflow | Required AnnData slots | Produced slots/results |
| --- | --- | --- |
| Cluster annotation | `obs[cluster_key]`; often `uns['rank_genes_groups']`; gene symbols in `var_names` | annotation tables; `obs['scsa_celltype']`, `obs['gpt_celltype']`, `obs['CellVote_celltype']`, or backend-specific prediction columns |
| Batch integration | `obs[batch_key]`; `obsm['X_pca']` or scaled matrix for embedding methods; `layers['counts']` for scVI-family methods | integrated embeddings such as `obsm['X_harmony']`, `obsm['X_scanorama']`, `obsm['X_cca']`, `obsm['X_scVI']`, `obsm['X_scANVI']`, `obsm['X_totalVI']`, or `obsm['X_scPoli']` |
| Pseudobulk | `obs[sample_col]`; optionally `obs[groups_col]`; raw counts in `layers['counts']` for count-based DE | pseudobulk AnnData with `obs['psbulk_n_cells']`, `obs['psbulk_counts']`, and `layers['psbulk_props']` |
| Monocle trajectory | count-like expression in `X`; ordering genes; learned reduction | `obs['Pseudotime']`, `obs['State']`, principal graph/reduction fields |
| TrajInfer/PseudotimeFate | `obsm[basis]`, `obsm[use_rep]`, `obs[groupby]`, neighbor graph in `obsp['connectivities']`, pseudotime column | pseudotime columns, terminal states, fate probabilities in `obsm['fate_probabilities']`, lineage entropy |
| Dynamic features | `obs[pseudotime]`; expression in `X`, `raw`, or selected layer | `DynamicFeaturesResult`; optional `uns[key_added]` trend tables |
| Velocity/fate | spliced/unspliced or velocity-ready layers, embeddings, neighbor graph | velocity layers/graphs/embeddings; CellRank estimator under `uns['velocity_cellrank']` |
| SCENIC/GRN | expression matrix, gene names compatible with ranking databases, cisTarget ranking DBs and motif table | regulons, AUCell matrices, GRN graph/tables |
| CNV | raw or near-raw expression; for inferCNV, genomic coordinates in `var` and reference labels in `obs` | CNV result object and backend-written CNV matrices/metadata |
| Metacells | low-dimensional representation such as `obsm['X_pca']`; optional count/log layers | `obs['metacell_id']`, confidence fields, metacell AnnData or backend artifacts |
| Metabolism | normalized expression for scMetabolism/scFEA or Compass output alignment | `obsm['X_metabolism']`, `uns['metabolism']`, differential metabolism table |

Run the bundled checker before choosing a workflow:

```bash
python sub-skills/single-cell-workflows/scripts/check_single_cell_inputs.py --synthetic --cluster-key leiden --embedding X_umap --embedding X_pca --layer counts
```

For a real file, pass the `.h5ad` path and requested keys:

```bash
python sub-skills/single-cell-workflows/scripts/check_single_cell_inputs.py data.h5ad --cluster-key celltype --embedding X_umap --layer counts --layer scaled
```

## Annotation Workflows

### SCSA or Marker-Based Annotation

1. Ensure clusters exist, for example `adata.obs['leiden']`.
2. Ensure `adata.uns['rank_genes_groups']` exists or allow `pySCSA.cell_anno(..., rank_rep=True)` / marker helpers to calculate rankings.
3. Run SCSA when the task asks for marker-database annotation:

```python
import omicverse as ov

scsa = ov.single.pySCSA(
    adata,
    species="Human",
    tissue="All",
    foldchange=1.5,
    pvalue=0.05,
    output="scsa_annotation.txt",
)
result = scsa.cell_anno(clustertype="leiden", cluster="all", rank_rep=False)
scsa.cell_auto_anno(adata, clustertype="leiden", key="scsa_celltype")
```

Inputs: cluster labels and marker rankings. Outputs: a SCSA result table plus `obs['scsa_celltype']` if `cell_auto_anno` is called. Use `model_path` for a local SCSA marker database; avoid assuming network access.

### Unified Annotation Manager

Use `Annotation` when the user wants one annotation interface over several backends:

```python
anno = ov.single.Annotation(adata)
result = anno.annotate(method="celltypist", cluster_key="leiden")
```

Important backends include `celltypist`, `scsa`, `gpt4celltype`, `scMulan`, `MetaTiME`, `harmony`, `scVI`, `scanorama`, and `TOSICA`. Results are backend-specific but predictions normally land in `adata.obs[f'{method}_prediction']` or backend-specific `obs`/`obsm` fields.

Use `AnnotationRef` for reference label transfer:

```python
ar = ov.single.AnnotationRef(adata_query, adata_ref, celltype_key="celltype")
ar.preprocess(mode="shiftlog|pearson", n_HVGs=3000, batch_key="integrate_batch")
# train/integrate as needed by the selected method, then:
query_labeled = ar.predict(method="harmony", n_neighbors=15)
```

Inputs: overlapping `var_names` between query and reference, reference labels in `adata_ref.obs[celltype_key]`. Prediction columns default to names such as `harmony_prediction`, `scVI_prediction`, or `scanorama_prediction`.

### CellVote and LLM-Assisted Consensus

Use `CellVote` when multiple candidate annotations need arbitration:

```python
markers = ov.single.get_celltype_marker(adata, clustertype="leiden")
cv = ov.single.CellVote(adata)
result = cv.vote(
    clusters_key="leiden",
    cluster_markers=markers,
    celltype_keys=["scsa_celltype", "celltypist_prediction"],
    species="human",
    organization="PBMC",
    result_key="CellVote_celltype",
)
```

Outputs: `obs['CellVote_celltype']`, per-cell confidence at `obs['CellVote_celltype_confidence']`, and a score table in `uns['CellVote_celltype_score_table']` when scoring succeeds. LLM-backed calls require user-provided API configuration; never embed credentials in skill files.

## Batch Integration Workflows

Call `ov.single.batch_correction(adata, batch_key=..., methods=..., n_pcs=..., **kwargs)` after the core preprocessing steps create an appropriate matrix or representation.

```python
adata = ov.single.batch_correction(adata, batch_key="batch", methods="harmony", n_pcs=50)
```

Common method choices:

- `harmony`: embedding-based integration; good default when `obsm['X_pca']` exists.
- `scanorama`: integration backend that writes an integrated embedding.
- `cca` or `seurat_cca`: pure-Python Seurat-style CCA through `pyccasc`; needs at least two batches and writes `obsm['X_cca']` plus metadata under `uns['cca']['X_cca']`.
- `scVI`: needs `scvi-tools` and count data, usually `layers['counts']`; writes `obsm['X_scVI']` and returns a model object.
- `scANVI`: needs `scvi-tools`, `labels_key`, and `unlabeled_category`; writes `obsm['X_scANVI']`.
- `totalVI`: needs `scvi-tools` and protein counts in an `obsm` key passed as `protein_expression_obsm_key`; writes `obsm['X_totalVI']`.
- `scPoli`: needs `scarches`; use `cell_type_keys` for prototype labels; writes `obsm['X_scPoli']`.

After integration, use the new `obsm` key as `use_rep` for neighbors or plotting, for example route plotting to core analysis and color by `obs[batch_key]` and biological labels.

## Pseudobulk Workflow

Use pseudobulk when a single-cell experiment has biological replicates and the downstream analysis should use sample-level profiles.

```python
pb = ov.single.pseudobulk(
    adata,
    sample_col="donor",
    groups_col="celltype",
    layer="counts",
    mode="sum",
    min_cells=10,
    min_counts=1000,
)
```

Inputs: `obs[sample_col]` and optionally `obs[groups_col]`; raw counts should be in `layers['counts']` for count-based DE. Outputs: rows are sample or sample-by-group profiles, `obs['psbulk_n_cells']`, `obs['psbulk_counts']`, and `layers['psbulk_props']`. Constant `obs` metadata within each profile is carried forward; variable metadata is dropped.

For DE after pseudobulk, convert one group to a genes-by-profiles count table and hand off to the bulk/statistics sub-skill when using bulk DE APIs.

## Trajectory, Pseudotime, and Fate

### Monocle-Style Trajectory

```python
mono = ov.single.Monocle(adata)
(
    mono.preprocess(min_expr=0.1)
        .select_ordering_genes(max_genes=1000)
        .reduce_dimension(max_components=2, reduction_method="DDRTree", method="fast")
        .order_cells(root_by_column="celltype", root_by_value="Stem")
)
```

`Monocle` writes `Pseudotime` and `State` back to the AnnData object. Use `method='exact'` in `reduce_dimension` only when R Monocle 2 parity is more important than speed.

### TrajInfer and PseudotimeFate

```python
traj = ov.single.TrajInfer(
    adata,
    basis="X_umap",
    use_rep="X_pca",
    n_comps=50,
    n_neighbors=15,
    groupby="clusters",
)
traj.set_origin_cells("Stem")
traj.set_terminal_cells(["LineageA", "LineageB"])
traj.inference(method="slingshot")

fate = ov.single.PseudotimeFate(
    adata,
    pseudotime_key="slingshot_pseudotime",
    groupby="clusters",
    n_macrostates=10,
)
result = fate.fit()
```

Inputs: embeddings and cluster labels for `TrajInfer`; `PseudotimeFate` additionally requires `obs[pseudotime_key]` and a neighbor graph at `obsp['connectivities']`. Outputs include terminal-state assignments, `obs['lineage_entropy']`, and `obsm['fate_probabilities']`.

### Dynamic Features Along Pseudotime

```python
res = ov.single.dynamic_features(
    adata,
    genes=["GATA1", "SPI1"],
    pseudotime="slingshot_pseudotime",
    groupby="celltype",
    layer="scaled",
    store_raw=True,
    raw_obs_keys=["State"],
)
```

This fits GAM trends using `pygam`. It needs enough finite pseudotime values and at least `min_cells` cells per modeled group. Store raw observations only when downstream trend plots need point overlays.

## Velocity and Fate

Use `ov.single.Velo(adata)` when a multi-step velocity workflow is needed; use wrapper functions for AnnData-first calls:

```python
ov.single.velocity(adata, backend="dynamo", basis="umap")
estimator = ov.single.cellrank_fate(adata)
states = ov.single.state_names(estimator)
```

Velocity workflows need velocity-ready layers such as spliced/unspliced or backend-specific moments. CellRank output is stored under `uns['velocity_cellrank']` for reuse.

## Perturbation and GRN Effects

```python
result = ov.single.perturb(
    adata,
    target="GATA1",
    mode="ko",
    backend="auto",
    layer="counts",
    return_delta=True,
)
summary = result.summary(top_n=20)
```

`PerturbResult` contains `adata_perturbed`, `grn`, `grn_base`, `delta_grn`, `delta_expr`, `trajectory_shift`, `delta_X`, `cell_names`, `gene_names`, `embedding`, and backend metadata. `backend='auto'` chooses CellOracle when a base GRN is provided or available in `uns['base_grn']`, otherwise scTenifoldKnk.

## SCENIC and GRN

```python
scenic = ov.single.SCENIC(
    adata,
    db_glob="resources/*rankings.feather",
    motif_path="resources/motifs.tbl",
    n_jobs=8,
    download=False,
)
scenic.cal_grn()
scenic.cal_regulons()
```

Prefer explicit local `db_glob` and `motif_path` for reproducibility. If using automatic resources, pass `species='human'`, `'mouse'`, or `'fly'` and make network/cache behavior explicit; `download=False` should raise a clear missing-resource error instead of silently fetching.

Use utility functions such as `ov.single.grn`, `build_correlation_network_umap_layout`, `add_tf_regulation`, and `plot_grn` for smaller GRN tasks.

## CNV, Metacells, Metabolism, and Milo

### CNV

```python
cnv = ov.single.CNV(adata, method="infercnv", layer="counts")
cnv.run(reference_key="celltype", reference_cat=["T cell"], platform="10x")
```

For `method='copykat'`, raw or near-raw counts are expected. For `method='infercnv'`, `adata.var` needs chromosome/start/end metadata and `platform` or explicit cutoff guidance.

### Metacells

```python
mc = ov.single.MetaCell(adata, method="kmeans", use_rep="X_pca", n_metacells=200).fit()
purity = mc.compute_purity(label_key="celltype")
```

Backends include `seacells`, `metaq`, `supercell`, `kmeans`, `random`, and `geosketch` when installed. Unified outputs include `obs['metacell_id']`, optional `obs['SEACell']`, and confidence metrics. Use `optimize_granularity` or `compare_metacell_backends` for backend selection.

### Metabolism

```python
met = ov.single.Metabolism(adata, method="scmetabolism", layer="scaled").run()
scores = met.get()
diff = ov.single.differential_metabolism(adata, groupby="celltype", group1="Tumor")
```

Outputs are `obsm['X_metabolism']` and `uns['metabolism']`. `compass` aligns precomputed Compass results back to cells; `scfea` and `scmetabolism` require their own optional dependencies.

### Milo

```python
milo = ov.single.Milo()
mdata = milo.load(adata, feature_key="rna")
milo.make_nhoods(mdata["rna"], prop=0.1)
```

Milo neighborhood analysis needs a neighbor graph in `obsp['connectivities']` or a named neighbors key.

## Lazy Pipeline and Report Orchestration

`scanpy_lazy` performs quick QC through UMAP and clustering, but it crosses into core preprocessing. Use it only when the user explicitly wants a convenience single-call scanpy-style pipeline:

```python
adata = ov.single.scanpy_lazy(adata, min_genes=200, min_cells=3, drop_doublet=True)
```

Stepwise helpers expose checkpointable stages: `lazy_step_qc`, `lazy_step_preprocess`, `lazy_step_scale`, `lazy_step_pca`, `lazy_step_cell_cycle`, `lazy_step_harmony`, `lazy_step_scvi`, `lazy_step_select_best_method`, `lazy_step_mde`, `lazy_step_clustering`, `lazy_step_final_embeddings`, and `lazy_step_by_step_guide`.

Generate a report only after analysis slots exist:

```python
report_path = ov.single.generate_scRNA_report(
    adata,
    output_path="scRNA_analysis_report.html",
    species="human",
    sample_key="batch",
    enable_analytics=False,
)
```

The report consumes the analyzed AnnData and writes an HTML file. Disable analytics unless the user explicitly wants tracking snippets.
