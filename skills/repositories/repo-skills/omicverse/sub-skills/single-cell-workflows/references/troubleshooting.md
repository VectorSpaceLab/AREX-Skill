# Single-Cell Troubleshooting

Use this guide when `omicverse.single` workflows fail because AnnData slots, labels, optional backends, or resources are missing. For core IO/QC/preprocess failures, route to [core analysis](../../core-analysis/SKILL.md).

## Fast Diagnosis Commands

Check a real `.h5ad` file:

```bash
python sub-skills/single-cell-workflows/scripts/check_single_cell_inputs.py data.h5ad --cluster-key leiden --embedding X_umap --embedding X_pca --layer counts
```

Check script installation and expected output format without a file:

```bash
python sub-skills/single-cell-workflows/scripts/check_single_cell_inputs.py --synthetic --cluster-key leiden --embedding X_umap --layer counts --layer scaled --json
```

The checker is read-only for real files. It reports missing `obs`, `obsm`, `layers`, neighbor graphs, pseudotime keys, rank-gene slots, and basic matrix sanity.

## Common Failure Modes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `KeyError: 'leiden'`, `cluster_key not in adata.obs`, or empty cluster list | Annotation workflow was started before clustering or with the wrong cluster column | Run or route to core preprocessing/clustering first; pass the actual cluster key with `clustertype`, `cluster_key`, or `clusters_key` consistently. |
| SCSA or marker annotation complains about missing `rank_genes_groups` | `scanpy.tl.rank_genes_groups` was not run, or rankings were written under another key | Compute marker rankings by cluster first, or call `pySCSA.cell_anno(..., rank_rep=True)` when appropriate. Check `adata.uns.keys()` for existing ranking keys. |
| SCSA produces `Unknown`, empty, or low-confidence labels | Marker database does not match species/tissue/gene symbols, or `model_path` is missing/wrong | Confirm `species`, `tissue`, `target`, and `Gensymbol`; pass a local marker database with `model_path`; use `norefdb=True` only with a user-defined marker DB. |
| `TypeError` or wrong argument behavior around SCSA cluster settings | Confusing SCSA `cluster` subset with AnnData cluster column | Use `clustertype='leiden'` for the AnnData column and `cluster='all'` or a cluster subset for SCSA's subset selector. |
| `CellVote` returns poor labels or raises on missing candidates | `celltype_keys` columns are absent, cluster markers are missing, or LLM credentials/provider are not configured | Build markers with `get_celltype_marker`; ensure candidate columns exist and are categorical/string; provide user-managed API key/config if an LLM provider is used. |
| `AnnotationRef` raises no shared genes | Query and reference `var_names` use different ID systems | Harmonize gene symbols/Ensembl IDs before constructing `AnnotationRef`; confirm non-empty gene intersection. |
| `AnnotationRef` warns data look log-normalized but a backend needs counts | Query or reference matrix has already been log-transformed | Recover or supply raw counts when required by the selected backend; otherwise choose an embedding-based method that accepts normalized data. |
| `ModuleNotFoundError: scvi` or scVI/scANVI/totalVI branch unavailable | `scvi-tools` is not installed in the runtime environment | Install the needed optional backend only if the user approves. Otherwise choose Harmony, Scanorama, Combat, or CCA. |
| `batch_correction(..., methods='scANVI')` raises `ValueError` mentioning `labels_key` | scANVI requires supervised labels and an unlabeled category | Add `adata.obs[labels_key]`, mark unlabeled cells with `unlabeled_category`, and pass both arguments. |
| `totalVI` raises `ValueError` mentioning `protein_expression_obsm_key` | CITE-seq protein counts are not provided | Store protein counts in `adata.obsm['protein_counts']` or the user's chosen key and pass `protein_expression_obsm_key='protein_counts'`. |
| `scPoli` import fails | `scarches` is not installed | Install `scarches` only when this backend is required, or choose another integration method. |
| CCA integration raises `requires ≥2 batches` | `obs[batch_key]` has only one category after filtering | Check filtering and batch labels; CCA needs at least two batches. Use non-integration preprocessing for one batch. |
| CCA integration raises `KeyError` around `reference` | Requested reference batch is not in `obs[batch_key]` | List `adata.obs[batch_key].unique()` and pass an existing category. |
| CCA or `seurat_cca` import fails | `pyccasc` / `cca_py` optional package is missing | Install the CCA optional dependency if approved or use Harmony/Scanorama. |
| Pseudobulk raises `KeyError` for `sample_col` or `groups_col` | Metadata column missing or misspelled | Validate `adata.obs.columns`; use biological replicate/sample IDs for `sample_col` and cell type/cluster labels for `groups_col`. |
| Pseudobulk output is invalid for DESeq2/edgeR | Aggregated normalized values instead of raw counts, or used `mode='mean'` | Use raw counts in `layers['counts']` and `mode='sum'` for count-based DE. |
| Monocle trajectory gives odd direction or root | Root state/value was not specified or incorrect | Use `order_cells(root_state=...)` or `root_by_column`/`root_by_value` based on a known early population; use `reverse=True` only when biologically justified. |
| `PseudotimeFate` raises missing pseudotime key | Trajectory backend did not write the expected `obs` column | Inspect `adata.obs.columns` and pass the actual pseudotime key, such as `slingshot_pseudotime`, `palantir_pseudotime`, or `Pseudotime`. |
| `PseudotimeFate` raises missing `connectivities` | Neighbor graph is absent | Run neighbors in core preprocessing before fate estimation; confirm `adata.obsp['connectivities']` exists. |
| `PseudotimeFate` raises NaN/inf pseudotime | Trajectory returned invalid pseudotime values or cells were not covered | Filter invalid cells or rerun trajectory with valid origin/terminal settings. |
| `dynamic_features` import fails or says `pygam` missing | GAM backend is optional | Install `pygam` if approved, or use simpler marker-over-pseudotime summaries. |
| `dynamic_features` skips groups or genes | Too few cells, missing pseudotime, zero variance, or genes absent | Lower `min_cells` carefully, pass existing genes, check `obs[pseudotime]`, and use the correct `layer`/`use_raw`. |
| `TrajInfer` symbol is unavailable | Optional `torch`/`igraph` trajectory extras are absent | Install the trajectory extras only if required, or use `Monocle` if available for the task. |
| StaVIA fails on `leidenalg`, `hnswlib`, or `pygam` | StaVIA optional dependencies are missing | Install only the missing extras when approved; otherwise choose a trajectory backend with installed dependencies. |
| SCENIC raises missing `db_glob`, `motif_path`, or species resource errors | cisTarget ranking databases/motif table were not provided or automatic resource prep is disabled/missing | Pass explicit local `db_glob` and `motif_path`, or pass `species` and make `download`/cache policy explicit. |
| SCENIC/GRN returns empty regulons or gene-name errors | Gene symbols in `adata.var_names` do not match ranking DB names | Harmonize gene symbols and species before running SCENIC; avoid Ensembl IDs unless matching resources support them. |
| CNV inferCNV raises about platform or cutoff | `method='infercnv'` needs platform-specific filtering | Pass `platform='10x'` or `platform='smartseq2'`, or an explicit cutoff when you know the correct threshold. |
| CNV inferCNV fails on chromosome metadata | `adata.var` lacks `chromosome`, `start`, `end` or equivalent bin metadata | Add genomic coordinates to `adata.var` before inferCNV; use CopyKAT only when its raw-count assumptions fit. |
| Metacell backend raises unknown method or missing backend package | Requested method is not in the backend registry or optional dependency is absent | Use an installed backend such as `kmeans`/`random` when available, or install the requested backend only after approval. |
| Metacell outputs too many/few groups | `n_metacells` default (`n_obs // 75`) is not appropriate | Set `n_metacells` explicitly or run `optimize_granularity` over a bounded grid. |
| Metabolism fails on `scmetabolism`, `compass`, or `scfea` | Backend-specific optional dependency or external output is missing | Use an installed method; for Compass, provide precomputed Compass output and align it to cells. |
| Milo `make_nhoods` raises no connectivities | Neighbor graph not present or named graph key is wrong | Run neighbors first and pass `neighbors_key` only when a named neighbors graph exists. |
| `generate_scRNA_report` lacks plots/sections | Analysis slots expected by report are missing | Complete preprocessing, embedding, clustering, and relevant single-cell analyses before report generation. |

## Optional Backend Triage

Prefer the lightest installed backend that satisfies the task:

1. Annotation: marker/manual/SCSA before LLM-backed methods when API credentials are unavailable.
2. Integration: Harmony or Scanorama before scVI-family models when GPU/deep-learning extras are unavailable.
3. Trajectory: Monocle or existing pseudotime before optional torch/igraph/StaVIA stacks.
4. GRN: smaller marker/network utilities before full SCENIC if cisTarget resources are absent.
5. Metacells: simple `kmeans`/`random` checks before heavy SEACells/MetaQ/SuperCell backends.

Known optional packages or extras that can be absent include `scvi-tools`, `scarches`, `pyccasc`/`cca_py`, `pygam`, `boltons`, `frozendict`, `torch`, `torch_geometric`, `igraph`, SCENIC resource dependencies, CellRank/scVelo/dynamo velocity stacks, CellOracle, scTenifoldKnk, CopyKAT/inferCNV backends, and metabolism backends.

## Privacy and Safety Notes

- Do not place API keys in notebooks, scripts, or skill docs; pass credentials through the user's environment or secret manager.
- Do not assume network downloads are allowed for SCSA databases, SCENIC resources, Cell Ontology files, model checkpoints, or LLM calls.
- Do not run external service or agent runtime commands from this sub-skill; route those to [agentic and MCP](../../agentic-and-mcp/SKILL.md).
- Treat original repository tests and examples as verification evidence only; runtime instructions here are self-contained and should work from an installed OmicVerse package plus user data.
