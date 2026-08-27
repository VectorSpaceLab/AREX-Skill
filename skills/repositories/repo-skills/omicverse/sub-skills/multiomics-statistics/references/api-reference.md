# API Reference

This is a compact map of public OmicVerse APIs for table-centric multiomics work. Prefer installed-package inspection for exact signatures when coding against a changed version.

## Bulk RNA-seq and Gene Sets

| API | Signature / Key Args | Input Shape | Output / Side Effects | Notes |
| --- | --- | --- | --- | --- |
| `ov.bulk.pyDEG(data)` | constructor over a pandas DataFrame | genes × samples | object with `normalize`, `drop_duplicates_index`, `deg_analysis`, `timecourse_deg` | Use `drop_duplicates_index()` before DE when gene IDs may repeat. |
| `pyDEG.deg_analysis(group1, group2, method=..., alpha=...)` | `group1`/`group2` are sample-name lists | genes × samples | DataFrame with `pvalue`, `qvalue`, `log2FC`, `sig` | Local pure-Python `edger` and `limma` paths are common; `deseq2` needs `pydeseq2`. |
| `pyDEG.timecourse_deg(time, group=None, block=None, time_basis="auto", data_type="auto")` | time Series indexed by samples | genes × samples | pyDEG-style result with temporal F-test fields | `group=None` tests temporal regulation; `group=` tests group-by-time interaction; `block=` handles repeated measures. |
| `ov.bulk.temporal_clusters(data, time, genes=None, n_clusters="auto", m="auto")` | soft clustering over temporal genes | genes × samples | cluster assignments / optional plot | Requires `pymfuzz`; needs at least 3 distinct time points. |
| `ov.bulk.geneset_enrichment(gene_list, pathways_dict, pvalue_threshold=0.05, background=None)` | gene list plus dict pathways | one list | filtered enrichment table | Offline dict path; outputs include `P-value`, `Adjusted P-value`, `Genes`, `logp`, `fraction`. |
| `ov.bulk.geneset_enrichment_GSEA(gene_rnk, pathways_dict, backend="numpy", permutation_num=1000, seed=112)` | ranked genes | DataFrame/Series | GSEA result object/table | NumPy backend is deterministic and avoids process deadlocks. |
| `omicverse.bulk._gsea_numpy.prerank(rnk, gene_sets, permutation_num=1000, min_size=15, max_size=500)` | internal but useful shape reference | ranked genes | gseapy-compatible object with `res2d`, `ranking`, `results` | Prefer public `geneset_enrichment_GSEA` unless debugging. |

## Enrichment / Signature Scoring (`ov.es`)

| API | Signature / Key Args | Input Shape | Output / Side Effects | Notes |
| --- | --- | --- | --- | --- |
| `ov.es.signatures_to_net(signatures, default_weight=1.0)` | `{name: [genes]}` or `{name: {gene: weight}}` | dict | long DataFrame `source`, `target`, `weight` | Use for explicit conversion or diagnostics. |
| `ov.es.aucell(data, signatures=None, net=None, tmin=5, engine="auto", n_up=None)` | AnnData or DataFrame | observations × genes | writes `score_aucell` to `obsm` for AnnData | Fast signature activity scoring. |
| `ov.es.ucell(data, signatures=None, max_rank=1500, missing_genes="impute", key_added="score_ucell")` | AnnData or DataFrame | observations × genes | writes `score_ucell` unless `copy=True` | Only accepts dict-style signatures, not `net`. |
| `ov.es.ora(data, signatures=None, net=None, tmin=5, engine="auto", n_bg=20000)` | AnnData or DataFrame | observations × genes | writes `score_ora` and `padj_ora` | Hypergeometric-style per-observation ORA. |
| `ov.es.gsea(data, signatures=None, net=None, tmin=5, times=1000, seed=42)` | AnnData or DataFrame | observations × genes | writes `score_gsea` | More expensive than AUCell/ORA. |
| `ov.es.decouple(data, signatures=None, net=None, methods=None, args=None, cons=True)` | multi-method wrapper | observations × genes | returns per-method dict and/or consensus | `methods=None` means decoupler defaults; `cons=False` keeps raw method outputs. |
| `ov.es.decoupler(data, signatures=None, net=None, method="aucell", engine="auto", **kwargs)` | single-method dispatcher | observations × genes | same as selected method | Valid methods: `aucell`, `gsea`, `gsva`, `ora`, `ulm`, `mlm`, `waggr`, `zscore`, `viper`, `mdt`, `udt`. |
| `ov.es.consensus(result, verbose=False)` | dict from `decouple(..., cons=False)` | score matrices | consensus score table | Use to compare multiple methods. |
| `ov.es.query_set(features, signatures=None, net=None, alternative="two-sided", n_bg=1000, tmin=5)` | feature list | one list | enrichment DataFrame | Useful for one-off feature set enrichment. |

## Metabolomics (`ov.metabol`)

| API | Signature / Key Args | Input Shape | Output / Side Effects | Notes |
| --- | --- | --- | --- | --- |
| `read_metaboanalyst(path, group_col, sample_col=None, transpose=False)` | CSV | samples × metabolites after load | AnnData with `obs['group']` | `group_col` is required and copied to `group`. |
| `read_wide(path, sep="\t", sample_col=None, group_col=None)` | CSV/TSV | samples × metabolites | AnnData | First column defaults to sample ID; group column is optional. |
| `read_lcms(path, feature_id_sep="/", label_row=None, transpose=True)` | LC-MS feature table | features-in-rows or samples-in-rows | AnnData with possible `var['m_z']`, `var['rt']` | Use for mummichog-style m/z + RT features. |
| `impute(adata, method="half_min" or "qrilc", missing_threshold=...)` | AnnData | samples × metabolites | AnnData | Drops or fills missing values depending on method. |
| `normalize(adata, method="pqn", reference="median", missing_threshold=0.5)` | AnnData | raw or positive intensities | AnnData | PQN is common before log/Pareto. |
| `transform(adata, method="log" or "pareto", pseudocount=1.0)` | AnnData | normalized matrix | AnnData | Log uses `log2(X + pseudocount)`; Pareto centers columns. |
| `cv_filter(adata, qc_mask, cv_threshold=0.30, across="qc")` | QC metadata | samples × metabolites | filtered AnnData with `var['qc_cv']` | Needs at least 3 QC samples unless `across="all"`. |
| `drift_correct(adata, injection_order, qc_mask, frac=...)` | run-order metadata | samples × metabolites | corrected AnnData | Warns when samples fall outside QC range. |
| `blank_filter(adata, blank_mask, ratio=3.0)` | blank metadata | samples × metabolites | filtered AnnData with `var['blank_ratio']` | Features absent in blanks pass. |
| `sample_qc(adata, n_components=2, alpha=0.95, layer=None)` | AnnData | samples × metabolites | DataFrame | Hotelling T² / DModX outlier diagnostics. |
| `differential(adata, group_col="group", group_a=None, group_b=None, method="welch_t", log_transformed=True)` | two groups | samples × metabolites | DataFrame with `stat`, `pvalue`, `padj`, `log2fc` | Methods: `welch_t`, `t`, `wilcoxon`, `limma`. |
| `anova(adata, group_col="group", method="welch_anova")` | 3+ groups | samples × metabolites | DataFrame | Methods include `welch_anova`, `anova`, `kruskal`. |
| `plsda(adata, group_col="group", n_components=2, scale=False)` | labeled samples | samples × metabolites | result with scores, loadings, VIP, R²/Q² | Use after PQN/log/Pareto for MetaboAnalyst-style workflow. |
| `msea_ora(hits, background, pathways=None, min_size=3, mass_db=None)` | hit/background metabolite names | lists | pathway table | Default pathway/database fetchers may require network/cache; pass local inputs to stay offline. |
| `msea_gsea(deg, stat_col="stat", pathways=None, n_perm=1000, mass_db=None)` | differential table | feature-indexed DataFrame | GSEA pathway table | `deg` should be indexed by metabolites. |
| `biomarker_panel(adata, group_col, features=10, classifier="rf", cv_outer=5, cv_inner=3)` | labeled samples | samples × metabolites | nested-CV panel result | Supports selected feature counts or explicit feature names. |
| `asca(adata, factors, include_interactions=True)` | multifactor metadata | samples × metabolites | ASCA result | Use for designed experiments. |
| `mixed_model(adata, formula, groups, term=None)` | repeated/random design | samples × metabolites | differential-like DataFrame | Needs valid formula and grouping metadata. |
| `meba(adata, group_col, time_col, subject_col)` | longitudinal design | samples × metabolites | MEBA result | Requires group, time, and subject columns. |

### Lipidomics Extensions

The `omicverse[lipidomics]` extra enables `pylipidr` and `pygoslin` routes such as `read_skyline`, `summarize_transitions`, `normalize_pqn`, `normalize_istd`, `de_lipids`, `lsea`, and `lipid_mva`. These bridge lipidr-style workflows and require lipid name parsing/annotation that plain metabolomics does not.

## Proteomics (`ov.protein`)

| API | Signature / Key Args | Input Shape | Output / Side Effects | Notes |
| --- | --- | --- | --- | --- |
| `read_maxquant(path, sample_pattern=r"LFQ intensity (.+)")` | MaxQuant `proteinGroups.txt` | proteins rows, intensity columns | AnnData samples × proteins | Converts zeros to NaN and stores peptide/gene metadata in `var`. |
| `read_diann(path, quant_col="PG.MaxLFQ", protein_col="Protein.Group")` | DIA-NN long or matrix report | mixed | AnnData | Detects long and wide formats. |
| `read_fragpipe(path, ...)` | FragPipe combined protein table | proteins × samples | AnnData | Use when FragPipe-specific metadata is present. |
| `read_olink_npx(path, ...)` | Olink long NPX table | long samples/proteins | AnnData | NPX may already be log scale; pass `log2=False` later. |
| `read_wide(path, protein_col=None, sep=None)` | generic wide table | samples × proteins | AnnData | Fallback for plain matrices. |
| `qc_filter(adata, min_peptides=2, peptides_col="peptides", min_valid=0.5, inplace=True)` | AnnData | samples × proteins | filters proteins; writes `n_valid_*` | Peptide filter is skipped if column missing. |
| `normalize(adata, method="median", log2=True, stash_raw=True)` | raw intensities | samples × proteins | mutates `X`, writes `layers['raw']` and `layers['log2']` | Methods: `median`, `equalize_medians`, `quantile`, `log2`. |
| `missing_pattern(adata)` | AnnData | samples × proteins | dict of missingness Series | Good pre-imputation diagnostic. |
| `model_selector(adata)` | normalized AnnData | samples × proteins | MCAR/MNAR mask and threshold | Requires `pyimputelcmd`. |
| `impute(adata, method="qrilc", seed=0, **kwargs)` | normalized matrix | samples × proteins | fills missing values | Optional backend coverage depends on install. |
| `de(adata, group, method="deqms", reference=None, count_var="peptides", fit_method="loess")` | grouped samples | samples × proteins | DataFrame; writes `adata.uns['protein_de']` | Methods: `deqms`, `limma`, `proda`, `wilcoxon`, `welch_t`, `olink_lmer`, `anova`, `kruskal`. |
| `enrich(...)`, `volcano(...)`, plotting helpers | result tables | DataFrame | figures/tables | Match schema before plotting. |

### Proteomics Optional Backends

Install `omicverse[protein]` when you need full proteomics parity:

- `pyimputelcmd`: imputeLCMD-style model selection and imputation.
- `pydeqms`: DEqMS moderated tests and median equalization.
- `pyproda`: proDA MNAR probabilistic differential expression.
- `pymsstats`: MSstats DDA/DIA workflows.
- `pyolinkanalyze`: Olink NPX analysis.
- `scikit-misc`, `statsmodels`: loess and model backends.

## Microbiome (`ov.micro`)

| API | Signature / Key Args | Input Shape | Output / Side Effects | Notes |
| --- | --- | --- | --- | --- |
| `rarefy(adata, depth=None, seed=0, save_original=True, copy=False)` | count AnnData | samples × taxa | rarefied AnnData; optional `layers['counts_raw']` | `depth=None` uses a common depth. |
| `collapse_taxa(adata, rank="genus")` | taxonomy in `var[rank]` | samples × ASVs/OTUs | samples × collapsed taxa | Zero-fills absent taxa when combining studies. |
| `Alpha(adata, rarefy_depth=None).run(metrics=("shannon", "observed_otus"))` | counts | samples × taxa | DataFrame; writes metrics to `obs` | `faith_pd` needs tree in `uns['tree']` and scikit-bio. |
| `Beta(adata, rarefy_depth=None).run(metric="braycurtis", rarefy=True)` | counts | samples × taxa | sample distance DataFrame; writes to `obsp[metric]` | UniFrac metrics need tree and matching taxa. |
| `Ordinate(adata, dist_key="braycurtis").pcoa(n=3)` | distance in `obsp` | samples × samples | DataFrame; writes `obsm[f'{dist_key}_pcoa']` | Also stores variance in `uns['micro']`. |
| `Ordinate(...).nmds(n=2, random_state=0)` | distance in `obsp` | samples × samples | DataFrame; writes `obsm[f'{dist_key}_nmds']` | Stores stress in `uns['micro']`. |
| `DA(adata).wilcoxon(group_key, group_a=None, group_b=None, rank=None, relative=True)` | group metadata | samples × taxa | DataFrame with `feature`, means, `p_value`, `fdr_bh`, `prevalence` | Fast no-R fallback. |
| `DA(adata).deseq2(group_key, group_a=None, group_b=None, rank=None)` | raw integer counts | samples × taxa | DESeq2-style DataFrame | Requires `pydeseq2`. |
| `DA(adata).ancombc(group_key, rank=None, pseudocount=1.0)` | compositional table | samples × taxa | ANCOM-BC DataFrame | Requires scikit-bio with supported ANCOM-BC return shape. |
| `combine_studies([adata...], study_names=None, rank="genus")` | list of studies | multiple AnnData | merged AnnData with `obs['study']` | Uses feature union and zero fill. |
| `meta_da(studies, group_key, method="wilcoxon", combine=...)` | list of studies | multiple AnnData | meta-analysis table | Reports `combined_lfc`, `combined_se`, `Q`, `I2`, `tau2`. |
| `paired_spearman(micro_adata, metabol_adata)` | aligned samples | two AnnData objects | microbe-metabolite correlation table | Requires identical `obs_names`. |
| `paired_cca(micro_adata, metabol_adata, n_components=2)` | aligned samples | two AnnData objects | CCA object/scores/loadings | Useful for table handoff, not causal inference. |
| `MMvec(...).fit(micro_adata, metabol_adata)` | aligned count/abundance tables | two AnnData objects | fitted embeddings | Requires Torch; heavier than Spearman/CCA. |

## Optional Dependency Map

| Workflow | Optional package or extra | When Needed | Fallback |
| --- | --- | --- | --- |
| Bulk DESeq2 | `pydeseq2` or broad compatible extra | `pyDEG.deg_analysis(method="deseq2")` | `method="edger"` or `"limma"` when appropriate. |
| Bulk temporal clustering | `pymfuzz` / `omicverse[timecourse]` | `ov.bulk.temporal_clusters` | Use `timecourse_deg` result without clustering. |
| Proteomics full workflow | `omicverse[protein]` | DEqMS, proDA, imputeLCMD, MSstats, OlinkAnalyze parity | `limma`, `welch_t`, `wilcoxon`, simple imputation where sufficient. |
| Lipidomics | `omicverse[lipidomics]` | Skyline/lipidr-style lipid workflows | Generic metabolomics read/normalize/differential for non-lipid tables. |
| Microbiome diversity | `scikit-bio` | Alpha/Beta, ANCOM-BC, PCoA | Basic table validation or non-phylogenetic statistics when unavailable. |
| Microbiome DESeq2 | `pydeseq2` | `DA.deseq2` | `DA.wilcoxon` or `DA.ancombc` if scikit-bio is available. |
| Microbiome paired MMvec | `torch` | `MMvec` | `paired_spearman` or `paired_cca`. |
